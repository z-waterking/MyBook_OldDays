#!/usr/bin/env python3
"""Validate the generated and hand-maintained parts of the Docsify site."""

from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageChops, ImageOps, ImageStat, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
FOOTPRINT_KINDS = {"life", "study", "work", "choice", "travel", "transit"}
ILLUSTRATION_SIZE = (1536, 1024)
ILLUSTRATION_WEB_SIZE = (960, 640)
ILLUSTRATION_RMS_LIMIT = 8.0

MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)"
)
HTML_LINK_RE = re.compile(r"(?:href|src)\s*=\s*['\"](?P<target>[^'\"]+)['\"]", re.IGNORECASE)
ILLUSTRATION_ID_RE = re.compile(r'data-illustration=["\']([^"\']+)["\']')
CATALOG_ARTICLE_RE = re.compile(r'class="article-cover-title"\s+href="#/(?P<target>[^"]+)"')

errors: list[str] = []


def report_error(message: str) -> None:
    errors.append(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        report_error(message)


def repository_target(raw_target: str, source: Path) -> Path | None:
    target = html.unescape(raw_target.strip().strip("<>"))
    if not target or target.startswith(("http://", "https://", "//", "mailto:", "tel:", "data:")):
        return None
    if target.startswith("#/"):
        target = target[2:]
    elif target.startswith("#"):
        return None
    elif target == "/":
        return None

    target = unquote(target).split("?", 1)[0].split("#", 1)[0]
    if not target:
        return None
    if target.startswith("/"):
        target = target.lstrip("/")

    if target.startswith(("./", "../")):
        return (source.parent / target).resolve()
    return (ROOT / target).resolve()


def check_site_links() -> int:
    checked: set[tuple[Path, str]] = set()
    link_count = 0
    for source in sorted(WEBSITE.glob("*.md")):
        content = source.read_text(encoding="utf-8")
        for pattern in (MARKDOWN_LINK_RE, HTML_LINK_RE):
            for match in pattern.finditer(content):
                raw_target = match.group("target")
                key = (source, raw_target)
                if key in checked:
                    continue
                checked.add(key)
                target = repository_target(raw_target, source)
                if target is None:
                    continue
                link_count += 1
                if not target.exists():
                    line = content.count("\n", 0, match.start()) + 1
                    try:
                        display_target = target.relative_to(ROOT).as_posix()
                    except ValueError:
                        display_target = str(target)
                    report_error(f"{source.relative_to(ROOT).as_posix()}:{line} 目标不存在: {display_target}")
    return link_count


def check_articles_and_catalog() -> tuple[int, int]:
    article_directories = sorted(path for path in (ROOT / "articles").iterdir() if path.is_dir())
    articles = [path for path in article_directories if (path / "index.md").is_file()]
    directories_without_articles = [path.name for path in article_directories if not (path / "index.md").is_file()]
    require(not directories_without_articles, f"文章目录缺少 index.md: {', '.join(directories_without_articles)}")

    missing_reviews = [path.name for path in articles if not (path / "review.md").is_file()]
    require(not missing_reviews, f"文章缺少 review.md: {', '.join(missing_reviews)}")

    catalog = (WEBSITE / "catalog.md").read_text(encoding="utf-8")
    catalog_rows = catalog.count('class="article-cover-row"')
    require(catalog_rows == len(articles), f"目录条目为 {catalog_rows}，文章实际为 {len(articles)}")

    expected_targets = {f"articles/{article.name}/index.md" for article in articles}
    catalog_targets = [unquote(html.unescape(match.group("target"))) for match in CATALOG_ARTICLE_RE.finditer(catalog)]
    target_counts = Counter(catalog_targets)
    duplicate_targets = sorted(target for target, count in target_counts.items() if count > 1)
    missing_targets = sorted(expected_targets - set(catalog_targets))
    extra_targets = sorted(set(catalog_targets) - expected_targets)
    require(len(catalog_targets) == catalog_rows, "目录中每个条目必须恰有一个文章标题链接")
    require(not duplicate_targets, f"目录存在重复文章: {', '.join(duplicate_targets)}")
    require(not missing_targets, f"目录缺少文章: {', '.join(missing_targets)}")
    require(not extra_targets, f"目录存在未知文章: {', '.join(extra_targets)}")

    catalog_total = re.search(r"> 共 (\d+) 篇文章", catalog)
    require(catalog_total is not None, "website/catalog.md 缺少文章总数")
    if catalog_total:
        require(int(catalog_total.group(1)) == len(articles), "website/catalog.md 标注的文章总数不正确")

    return len(articles), catalog_rows


def check_footprints() -> tuple[int, int]:
    data_path = WEBSITE / "footprints-data.json"
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        report_error(f"无法读取足迹数据: {error}")
        return 0, 0

    for scope in ("china", "world"):
        require(isinstance(data.get(scope), list), f"足迹数据缺少 {scope} 数组")
    if not isinstance(data.get("china"), list) or not isinstance(data.get("world"), list):
        return 0, 0

    names: set[str] = set()
    for scope in ("china", "world"):
        for index, item in enumerate(data[scope], start=1):
            label = f"{scope}[{index}]"
            if not isinstance(item, dict):
                report_error(f"{label} 必须是对象")
                continue
            for field in ("name", "lat", "lng", "kind", "status", "period", "article", "story"):
                require(field in item and item[field] != "", f"{label} 缺少字段 {field}")
            for field in ("name", "kind", "status", "period", "article", "story"):
                require(isinstance(item.get(field), str), f"{label}.{field} 必须是字符串")
            name = item.get("name") if isinstance(item.get("name"), str) else ""
            require(name not in names, f"足迹名称重复: {name}")
            names.add(name)
            latitude = item.get("lat")
            longitude = item.get("lng")
            require(isinstance(latitude, (int, float)) and not isinstance(latitude, bool) and -90 <= latitude <= 90, f"{label} 纬度无效")
            require(isinstance(longitude, (int, float)) and not isinstance(longitude, bool) and -180 <= longitude <= 180, f"{label} 经度无效")
            require(item.get("kind") in FOOTPRINT_KINDS, f"{label}.kind 无效: {item.get('kind')}")
            article = item.get("article")
            if isinstance(article, str) and article:
                require((ROOT / article).is_file(), f"{label} 来源文章不存在: {article}")

    routes = data.get("routes")
    require(isinstance(routes, dict), "足迹数据缺少 routes")
    if isinstance(routes, dict):
        for route_name in ("china", "spain"):
            route = routes.get(route_name)
            require(isinstance(route, list) and len(route) >= 2, f"足迹路线 {route_name} 至少需要两个坐标")
            if not isinstance(route, list):
                continue
            for index, point in enumerate(route, start=1):
                label = f"routes.{route_name}[{index}]"
                valid_shape = isinstance(point, list) and len(point) == 2
                require(valid_shape, f"{label} 必须是 [纬度, 经度]")
                if not valid_shape:
                    continue
                latitude, longitude = point
                valid_latitude = isinstance(latitude, (int, float)) and not isinstance(latitude, bool) and -90 <= latitude <= 90
                valid_longitude = isinstance(longitude, (int, float)) and not isinstance(longitude, bool) and -180 <= longitude <= 180
                require(valid_latitude, f"{label} 纬度无效")
                require(valid_longitude, f"{label} 经度无效")

    return len(data["china"]), len(data["world"])


def check_illustrations() -> int:
    manifest_path = ROOT / "scripts" / "illustration_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        report_error(f"无法读取插画清单: {error}")
        return 0

    items = manifest.get("items")
    require(isinstance(items, list), "插画清单缺少 items 数组")
    if not isinstance(items, list):
        return 0

    ids: set[str] = set()
    expected_page_ids: dict[Path, set[str]] = {}
    for index, item in enumerate(items, start=1):
        illustration_id = item.get("id")
        group = item.get("group")
        page_value = item.get("page")
        filename = item.get("filename")
        label = f"插画清单第 {index} 项"
        require(all(isinstance(value, str) and value for value in (illustration_id, group, page_value, filename)), f"{label} 字段不完整")
        if not all(isinstance(value, str) and value for value in (illustration_id, group, page_value, filename)):
            continue
        require(illustration_id not in ids, f"插画 ID 重复: {illustration_id}")
        ids.add(illustration_id)

        page = ROOT / page_value
        source = ROOT / "assets" / "images" / "illustrations" / group / filename
        derivative = ROOT / "assets" / "images" / "_generated" / "illustrations" / group / f"{Path(filename).stem}.webp"
        require(page.is_file(), f"插画页面不存在: {page_value}")
        require(source.is_file(), f"插画原图不存在: {source.relative_to(ROOT).as_posix()}")
        require(derivative.is_file(), f"插画派生图不存在: {derivative.relative_to(ROOT).as_posix()}")
        if source.is_file() and derivative.is_file():
            try:
                with Image.open(source) as source_image:
                    require(source_image.format == "JPEG", f"插画原图不是 JPEG: {source.relative_to(ROOT).as_posix()}")
                    require(source_image.size == ILLUSTRATION_SIZE, f"插画原图尺寸不是 1536x1024: {source.relative_to(ROOT).as_posix()}")
                    expected = ImageOps.fit(
                        ImageOps.exif_transpose(source_image).convert("RGB"),
                        ILLUSTRATION_WEB_SIZE,
                        method=Image.Resampling.LANCZOS,
                    )
                with Image.open(derivative) as derivative_image:
                    require(derivative_image.format == "WEBP", f"插画派生图不是 WebP: {derivative.relative_to(ROOT).as_posix()}")
                    require(derivative_image.size == ILLUSTRATION_WEB_SIZE, f"插画派生图尺寸不是 960x640: {derivative.relative_to(ROOT).as_posix()}")
                    actual = derivative_image.convert("RGB")
                if actual.size == expected.size:
                    channel_rms = ImageStat.Stat(ImageChops.difference(expected, actual)).rms
                    average_rms = sum(channel_rms) / len(channel_rms)
                    require(
                        average_rms <= ILLUSTRATION_RMS_LIMIT,
                        f"插画派生图可能未同步（RMS {average_rms:.2f}）: {derivative.relative_to(ROOT).as_posix()}",
                    )
            except (OSError, UnidentifiedImageError) as error:
                report_error(f"无法读取插画 {illustration_id}: {error}")
        expected_page_ids.setdefault(page, set()).add(illustration_id)

    for page, expected_ids in expected_page_ids.items():
        if not page.is_file():
            continue
        actual_ids = set(ILLUSTRATION_ID_RE.findall(page.read_text(encoding="utf-8")))
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        require(not missing, f"{page.relative_to(ROOT).as_posix()} 缺少插画块: {', '.join(missing)}")
        require(not extra, f"{page.relative_to(ROOT).as_posix()} 存在清单外插画块: {', '.join(extra)}")

    return len(items)


def check_required_files() -> None:
    required = [
        "index.html",
        "website/home.md",
        "website/_sidebar.md",
        "website/catalog.md",
        "website/ranking.md",
        "website/literary-gems.md",
        "website/fun-rankings.md",
        "website/footprints.md",
        "website/footprints-data.json",
    ]
    for relative_path in required:
        require((ROOT / relative_path).is_file(), f"缺少网站关键文件: {relative_path}")


def main() -> int:
    check_required_files()
    article_count, catalog_count = check_articles_and_catalog()
    link_count = check_site_links()
    china_count, world_count = check_footprints()
    illustration_count = check_illustrations()

    if errors:
        print(f"网站巡检失败，共 {len(errors)} 个问题：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("网站巡检通过")
    print(f"- 文章 / 目录：{article_count} / {catalog_count}")
    print(f"- 已检查本地链接与图片：{link_count}")
    print(f"- 足迹：中国 {china_count}，世界视图 {world_count}")
    print(f"- 插画原图与派生图：{illustration_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())