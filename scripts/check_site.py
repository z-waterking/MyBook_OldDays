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
BOOK = ROOT / "book"
AI_EDITED = ROOT / "ai-edited-articles"
ARTICLE_IMAGES = ROOT / "assets" / "images" / "articles"
GENERATED_IMAGES = ROOT / "assets" / "images" / "_generated"
FOOTPRINT_KINDS = {"life", "study", "work", "choice", "travel", "transit"}
ARTICLE_COVER_SIZE = (1536, 1024)
CATALOG_COVER_SIZE = (480, 320)
ARTICLE_WEB_COVER_SIZE = (1200, 800)
HOME_HERO_SIZE = (1200, 800)
FAVICON_SIZE = (64, 64)
CATALOG_COVER_RMS_LIMIT = 9.0
ARTICLE_WEB_COVER_RMS_LIMIT = 8.0
HOME_HERO_SOURCE = "合集-05-我在康杰念高中（怀昔）"
ILLUSTRATION_SIZE = (1536, 1024)
ILLUSTRATION_WEB_SIZE = (960, 640)
ILLUSTRATION_RMS_LIMIT = 8.0
REVIEW_SECTIONS = ("总体印象", "亮点分析", "写作建议", "金句摘录", "综合评分", "综合评价")
CATALOG_FOOTER = "<!-- 此文件由 scripts/save_article.py 自动生成，请勿手工编辑。 -->"

MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)"
)
HTML_LINK_RE = re.compile(r"(?:href|src)\s*=\s*['\"](?P<target>[^'\"]+)['\"]", re.IGNORECASE)
ILLUSTRATION_ID_RE = re.compile(r'data-illustration=["\']([^"\']+)["\']')
CATALOG_ARTICLE_RE = re.compile(r'class="article-cover-title"\s+href="#/(?P<target>[^"]+)"')
REVIEW_SCORE_RE = re.compile(r"\*\*(?P<score>\d+(?:\.\d+)?)\s*/\s*10\*\*")
RANKING_ROW_RE = re.compile(
    r"^\|\s*(?P<rank>\d+)\s*\|\s*\*\*(?P<score>\d+(?:\.\d+)?)\*\*\s*\|\s*"
    r"(?P<category>合集|散篇)\s*\|\s*\[(?P<title>[^\]]+)\]\((?P<target>articles/[^)\n]+/review\.md)\)\s*\|",
    re.MULTILINE,
)
MAPPING_ROW_RE = re.compile(
    r"^\|\s*\[(?P<label>[^\]]+)\]\(\.\./articles/(?P<source>[^/]+)/index\.md\)\s*\|\s*"
    r"(?P<target>ai-edited-articles/(?P<category>合集|散篇)/(?P<edited>[^/]+)/index\.md)\s*\|\s*"
    r"(?P<status>[^|]+?)\s*\|$",
    re.MULTILINE,
)

errors: list[str] = []


def report_error(message: str) -> None:
    errors.append(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        report_error(message)


def image_rms(expected: Image.Image, actual: Image.Image) -> float:
    channel_rms = ImageStat.Stat(ImageChops.difference(expected, actual)).rms
    return sum(channel_rms) / len(channel_rms)


def parse_front_matter(content: str) -> dict[str, str]:
    match = re.match(r"^---\r?\n(?P<body>[\s\S]*?)\r?\n---", content.lstrip("\ufeff"))
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def article_sort_key(name: str) -> tuple[int, int, str]:
    category_order = 0 if name.startswith("合集-") else 1 if name.startswith("散篇-") else 2
    match = re.match(r"^(?:合集|散篇)-(\d{2})-", name)
    return category_order, int(match.group(1)) if match else 999, name


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
    ai_pages = [
        path
        for category in ("合集", "散篇")
        for path in (AI_EDITED / category).glob("*/*.md")
    ]
    sources = sorted([*WEBSITE.glob("*.md"), *BOOK.glob("*.md"), *ai_pages])
    for source in sources:
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


def markdown_article_targets(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [
        unquote(html.unescape(match.group("target").strip().strip("<>")))
        for match in MARKDOWN_LINK_RE.finditer(content)
        if match.group("target").strip().strip("<>").startswith("articles/")
    ]


def check_book_reading_order(article_count: int) -> tuple[int, int]:
    manifest_path = BOOK / "reading-order.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        report_error(f"无法读取成书阅读顺序: {error}")
        return 0, 0

    parts = manifest.get("parts")
    require(isinstance(parts, list), "成书阅读顺序缺少 parts 数组")
    if not isinstance(parts, list):
        return 0, 0

    require(len(parts) == 8, f"成书阅读顺序应为七部加附录，当前为 {len(parts)} 个部分")
    part_ids: list[str] = []
    part_pages: list[str] = []
    selected_targets: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            report_error("成书阅读顺序包含非对象部分")
            continue
        part_id = str(part.get("id", ""))
        page = unquote(str(part.get("page", "")))
        chapters = part.get("chapters")
        part_ids.append(part_id)
        part_pages.append(page)
        require(bool(part_id), "成书阅读部分缺少 id")
        require(bool(part.get("number")), f"成书阅读部分缺少 number: {part_id or '未知'}")
        require(bool(part.get("title")), f"成书阅读部分缺少 title: {part_id or '未知'}")
        require(isinstance(chapters, list) and bool(chapters), f"成书阅读部分没有章节: {part_id or '未知'}")
        page_path = ROOT / page
        require(page_path.is_file(), f"成书阅读部分页面不存在: {page}")
        if not isinstance(chapters, list):
            continue

        part_targets: list[str] = []
        for chapter in chapters:
            if not isinstance(chapter, dict):
                report_error(f"成书阅读部分包含非对象章节: {part_id}")
                continue
            target = unquote(str(chapter.get("path", "")))
            require(bool(chapter.get("title")), f"成书阅读章节缺少标题: {target or part_id}")
            require(target.startswith("articles/") and target.endswith("/index.md"), f"成书阅读章节路径格式错误: {target}")
            require((ROOT / target).is_file(), f"成书阅读章节不存在: {target}")
            part_targets.append(target)
            selected_targets.append(target)

        if page_path.is_file():
            require(
                markdown_article_targets(page_path) == part_targets,
                f"成书分部页面与阅读顺序不一致: {page}",
            )

    require(len(part_ids) == len(set(part_ids)), "成书阅读部分 id 重复")
    require(len(part_pages) == len(set(part_pages)), "成书阅读部分页面重复")
    require(part_ids == [f"part-{number}" for number in range(1, 8)] + ["appendix"], "成书阅读部分顺序错误")
    require(len(selected_targets) == 33, f"成书阅读版应选 33 篇，当前为 {len(selected_targets)} 篇")
    require(len(selected_targets) == len(set(selected_targets)), "成书阅读版存在重复文章")
    require(len(selected_targets) <= article_count, "成书阅读版篇数超过文章档案总数")

    contents_path = BOOK / "01-成书目录.md"
    require(contents_path.is_file(), "缺少公开成书阅读目录")
    if contents_path.is_file():
        require(
            markdown_article_targets(contents_path) == selected_targets,
            "公开成书目录与 reading-order.json 顺序不一致",
        )

    legacy_volumes = sorted(path.name for path in BOOK.glob("卷*.md"))
    require(not legacy_volumes, f"成书区仍有旧卷文件: {', '.join(legacy_volumes)}")
    legacy_links = [
        path.name
        for path in BOOK.glob("*.md")
        if "../articles/" in path.read_text(encoding="utf-8")
    ]
    require(not legacy_links, f"成书区仍使用旧相对文章链接: {', '.join(legacy_links)}")
    return len(parts), len(selected_targets)


def check_articles_and_catalog() -> tuple[list[Path], int, dict[str, float]]:
    article_directories = sorted(path for path in (ROOT / "articles").iterdir() if path.is_dir())
    articles = [path for path in article_directories if (path / "index.md").is_file()]
    directories_without_articles = [path.name for path in article_directories if not (path / "index.md").is_file()]
    require(not directories_without_articles, f"文章目录缺少 index.md: {', '.join(directories_without_articles)}")

    review_scores: dict[str, float] = {}
    for article in articles:
        review_files = sorted(path.name for path in article.glob("review*.md"))
        require(review_files == ["review.md"], f"{article.name} 的评价文件必须且只能是 review.md，当前为: {', '.join(review_files) or '无'}")
        review_path = article / "review.md"
        if not review_path.is_file():
            continue
        content = review_path.read_text(encoding="utf-8")
        missing_sections = [section for section in REVIEW_SECTIONS if f"## {section}" not in content]
        require(not missing_sections, f"{article.name}/review.md 缺少章节: {', '.join(missing_sections)}")
        score_matches = REVIEW_SCORE_RE.findall(content)
        require(len(score_matches) == 1, f"{article.name}/review.md 必须恰有一个加粗的 X/10 综合评分")
        if len(score_matches) == 1:
            score = float(score_matches[0])
            require(0 <= score <= 10, f"{article.name}/review.md 评分超出 0-10: {score}")
            review_scores[f"articles/{article.name}/review.md"] = score

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
    require(CATALOG_FOOTER in catalog, "website/catalog.md 缺少规范的自动生成声明")

    return articles, catalog_rows, review_scores


def check_ranking(review_scores: dict[str, float]) -> int:
    ranking_path = WEBSITE / "ranking.md"
    content = ranking_path.read_text(encoding="utf-8")
    rows = [
        {
            "rank": int(match.group("rank")),
            "score": float(match.group("score")),
            "category": match.group("category"),
            "title": match.group("title"),
            "target": unquote(match.group("target")),
        }
        for match in RANKING_ROW_RE.finditer(content)
    ]
    targets = [row["target"] for row in rows]
    require(len(rows) == len(review_scores), f"评分榜有 {len(rows)} 行，规范评价有 {len(review_scores)} 个")
    require(len(set(targets)) == len(targets), "评分榜存在重复文章")
    require(set(targets) == set(review_scores), "评分榜文章集合与规范评价不一致")
    require([row["rank"] for row in rows] == list(range(1, len(rows) + 1)), "评分榜排名必须从 1 连续递增")

    for row in rows:
        expected_score = review_scores.get(row["target"])
        if expected_score is not None:
            require(abs(row["score"] - expected_score) < 1e-9, f"评分榜与评价分数不一致: {row['target']}")
        article_name = Path(row["target"]).parent.name
        expected_category = "合集" if article_name.startswith("合集-") else "散篇"
        require(row["category"] == expected_category, f"评分榜分类错误: {row['target']}")

    expected_order = [
        target
        for target, _ in sorted(
            review_scores.items(),
            key=lambda item: (-item[1], *article_sort_key(Path(item[0]).parent.name)),
        )
    ]
    require(targets == expected_order, "评分榜顺序与分数及同分排序规则不一致")

    groups = {
        "总体": list(review_scores.values()),
        "合集": [score for target, score in review_scores.items() if Path(target).parent.name.startswith("合集-")],
        "散篇": [score for target, score in review_scores.items() if Path(target).parent.name.startswith("散篇-")],
    }
    for label, scores in groups.items():
        pattern = re.compile(
            rf"- \*\*{label}：\*\* (?P<count>\d+) 篇，总分 (?P<total>\d+(?:\.\d+)?)，平均分 \*\*(?P<average>\d+(?:\.\d+)?)/10\*\*"
        )
        match = pattern.search(content)
        require(match is not None, f"评分榜缺少{label}统计")
        if not match:
            continue
        total = sum(scores)
        require(int(match.group("count")) == len(scores), f"评分榜{label}篇数错误")
        require(abs(float(match.group("total")) - total) < 1e-9, f"评分榜{label}总分错误")
        require(abs(float(match.group("average")) - total / len(scores)) < 0.00005, f"评分榜{label}平均分错误")

    expected_distribution = {
        "9.0 - 10.0": sum(score >= 9.0 for score in review_scores.values()),
        "8.5 - 8.9": sum(8.5 <= score < 9.0 for score in review_scores.values()),
        "8.0 - 8.4": sum(8.0 <= score < 8.5 for score in review_scores.values()),
        "7.5 - 7.9": sum(7.5 <= score < 8.0 for score in review_scores.values()),
        "7.0 - 7.4": sum(7.0 <= score < 7.5 for score in review_scores.values()),
        "6.0 - 6.9": sum(6.0 <= score < 7.0 for score in review_scores.values()),
        "低于 6.0": sum(score < 6.0 for score in review_scores.values()),
    }
    for label, expected_count in expected_distribution.items():
        match = re.search(rf"^\|\s*{re.escape(label)}\s*\|\s*(?P<count>\d+)\s*\|$", content, re.MULTILINE)
        require(match is not None, f"评分榜缺少分布区间: {label}")
        if match:
            require(int(match.group("count")) == expected_count, f"评分榜分布数量错误: {label}")

    if rows:
        for label, row in (("最高分", rows[0]), ("最低分", rows[-1])):
            match = re.search(
                rf"^- \*\*{label}：\*\* \*\*(?P<score>\d+(?:\.\d+)?)/10\*\*（(?P<title>.+)）$",
                content,
                re.MULTILINE,
            )
            require(match is not None, f"评分榜缺少{label}摘要")
            if match:
                require(abs(float(match.group("score")) - row["score"]) < 1e-9, f"评分榜{label}摘要分数错误")
                require(match.group("title") == row["title"], f"评分榜{label}摘要标题错误")

    return len(rows)


def check_ai_edits(articles: list[Path]) -> int:
    expected: dict[tuple[str, str], Path] = {}
    for article in articles:
        category = "合集" if article.name.startswith("合集-") else "散篇"
        expected[(category, article.name)] = AI_EDITED / category / article.name

    actual = {
        (category, path.name): path
        for category in ("合集", "散篇")
        for path in (AI_EDITED / category).iterdir()
        if path.is_dir()
    }
    require(set(actual) == set(expected), "AI 改稿目录与原文目录不是一一对应")

    for (category, name), expected_dir in expected.items():
        edit_dir = actual.get((category, name), expected_dir)
        index_path = edit_dir / "index.md"
        notes_path = edit_dir / "notes.md"
        require(index_path.is_file(), f"AI 改稿缺少 index.md: {name}")
        require(notes_path.is_file(), f"AI 改稿缺少 notes.md: {name}")
        version_files = sorted(path.name for path in edit_dir.glob("index_v*.md"))
        require(not version_files, f"AI 改稿不得使用平行版本文件 {name}: {', '.join(version_files)}")

        if index_path.is_file():
            index_content = index_path.read_text(encoding="utf-8")
            metadata = parse_front_matter(index_content)
            source_value = metadata.get("source_article")
            require(bool(source_value), f"AI 改稿缺少 source_article: {name}")
            if source_value:
                source_path = (index_path.parent / source_value).resolve()
                require(source_path == (ROOT / "articles" / name / "index.md").resolve(), f"AI 改稿 source_article 错误: {name}")
            require(metadata.get("status") == "AI 修改稿", f"AI 改稿 status 错误: {name}")
            decoded_content = unquote(index_content)
            source_route = f'href="#/articles/{name}/index.md"'
            notes_route = f'href="#/ai-edited-articles/{category}/{name}/notes.md"'
            require("](#/" not in index_content, f"AI 改稿包含会被 Docsify 误解析的 Markdown hash 路由: {name}")
            require(source_route in decoded_content, f"AI 改稿缺少正确的返回原文路由: {name}")
            require(notes_route in decoded_content, f"AI 改稿缺少正确的改稿说明路由: {name}")
        if notes_path.is_file():
            notes = notes_path.read_text(encoding="utf-8")
            require("## 本版实际改动" in notes, f"AI 改稿说明缺少“本版实际改动”: {name}")

    mapping_content = (AI_EDITED / "mapping.md").read_text(encoding="utf-8")
    mapping_rows = list(MAPPING_ROW_RE.finditer(mapping_content))
    mapped_sources = [match.group("source") for match in mapping_rows]
    expected_names = {name for _, name in expected}
    require(len(mapping_rows) == len(expected), f"AI 映射表有 {len(mapping_rows)} 行，预期 {len(expected)} 行")
    require(len(set(mapped_sources)) == len(mapped_sources), "AI 映射表存在重复原文")
    for match in mapping_rows:
        source = match.group("source")
        category = "合集" if source.startswith("合集-") else "散篇"
        expected_target = f"ai-edited-articles/{category}/{source}/index.md"
        require(match.group("label") == source, f"AI 映射标题与原文目录不一致: {source}")
        require(match.group("edited") == source, f"AI 映射目录名不一致: {source}")
        require(match.group("category") == category, f"AI 映射分类错误: {source}")
        require(match.group("target") == expected_target, f"AI 映射目标错误: {source}")
        require(match.group("status").strip() == "已改稿", f"AI 映射状态错误: {source}")
    require(set(mapped_sources) == expected_names, "AI 映射表与原文目录集合不一致")
    return len(actual)


def check_footprints() -> tuple[int, int, int]:
    data_path = WEBSITE / "footprints-data.json"
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        report_error(f"无法读取足迹数据: {error}")
        return 0, 0, 0

    for scope in ("china", "world"):
        require(isinstance(data.get(scope), list), f"足迹数据缺少 {scope} 数组")
    if not isinstance(data.get("china"), list) or not isinstance(data.get("world"), list):
        return 0, 0, 0

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

    spanish_count = sum(item.get("country") == "西班牙" for item in data["world"] if isinstance(item, dict))
    return len(data["china"]), len(data["world"]), spanish_count


def check_cover_derivatives(articles: list[Path]) -> int:
    catalog_dir = GENERATED_IMAGES / "catalog-covers"
    article_web_dir = GENERATED_IMAGES / "article-covers"
    expected_names = {article.name for article in articles}
    derivative_sets = (
        ("目录封面", catalog_dir),
        ("正文封面", article_web_dir),
    )
    for label, directory in derivative_sets:
        actual_names = {path.stem for path in directory.glob("*.webp")} if directory.is_dir() else set()
        missing = sorted(expected_names - actual_names)
        extra = sorted(actual_names - expected_names)
        require(not missing, f"{label}派生图缺失: {', '.join(missing)}")
        require(not extra, f"{label}派生图没有对应文章: {', '.join(extra)}")

    hero_original: Image.Image | None = None
    for article in articles:
        source = ARTICLE_IMAGES / article.name / "cover.png"
        catalog_derivative = catalog_dir / f"{article.name}.webp"
        article_derivative = article_web_dir / f"{article.name}.webp"
        article_content = (article / "index.md").read_text(encoding="utf-8")
        cover_tag_match = re.search(r'<img class="article-cover"(?:\s|>)[^>]*>', article_content)
        require(cover_tag_match is not None, f"文章缺少正文封面块: {article.name}")
        if cover_tag_match is not None:
            cover_tag = cover_tag_match.group(0)
            expected_src = f'assets/images/_generated/article-covers/{article.name}.webp'
            require(f'src="{expected_src}"' in cover_tag, f"文章未引用轻量正文封面: {article.name}")
            require('width="1200"' in cover_tag and 'height="800"' in cover_tag, f"文章正文封面缺少尺寸声明: {article.name}")
        require(source.is_file(), f"文章封面原图不存在: {source.relative_to(ROOT).as_posix()}")
        if not source.is_file():
            continue
        try:
            with Image.open(source) as source_image:
                require(source_image.format == "PNG", f"文章封面原图不是 PNG: {source.relative_to(ROOT).as_posix()}")
                require(source_image.size == ARTICLE_COVER_SIZE, f"文章封面原图尺寸不是 1536x1024: {source.relative_to(ROOT).as_posix()}")
                original = ImageOps.exif_transpose(source_image).convert("RGB")
                if article.name == HOME_HERO_SOURCE:
                    hero_original = original.copy()
            derivative_specs = (
                ("目录封面", catalog_derivative, CATALOG_COVER_SIZE, CATALOG_COVER_RMS_LIMIT),
                ("正文封面", article_derivative, ARTICLE_WEB_COVER_SIZE, ARTICLE_WEB_COVER_RMS_LIMIT),
            )
            for label, derivative, expected_size, rms_limit in derivative_specs:
                if not derivative.is_file():
                    continue
                expected = ImageOps.fit(original, expected_size, method=Image.Resampling.LANCZOS)
                with Image.open(derivative) as derivative_image:
                    require(derivative_image.format == "WEBP", f"{label}派生图不是 WebP: {derivative.relative_to(ROOT).as_posix()}")
                    require(derivative_image.size == expected_size, f"{label}派生图尺寸不是 {expected_size[0]}x{expected_size[1]}: {derivative.relative_to(ROOT).as_posix()}")
                    actual = derivative_image.convert("RGB")
                if actual.size == expected.size:
                    difference = image_rms(expected, actual)
                    require(
                        difference <= rms_limit,
                        f"{label}派生图可能未同步（RMS {difference:.2f}）: {derivative.relative_to(ROOT).as_posix()}",
                    )
        except (OSError, UnidentifiedImageError) as error:
            report_error(f"无法读取文章封面 {article.name}: {error}")

    hero_path = GENERATED_IMAGES / "home-hero.webp"
    favicon_path = GENERATED_IMAGES / "favicon.png"
    require(hero_original is not None, f"首页主视觉来源文章不存在: {HOME_HERO_SOURCE}")
    require(hero_path.is_file(), f"首页主视觉派生图不存在: {hero_path.relative_to(ROOT).as_posix()}")
    require(favicon_path.is_file(), f"站点图标不存在: {favicon_path.relative_to(ROOT).as_posix()}")
    if hero_original is not None and hero_path.is_file():
        try:
            expected = ImageOps.fit(hero_original, HOME_HERO_SIZE, method=Image.Resampling.LANCZOS)
            with Image.open(hero_path) as hero_image:
                require(hero_image.format == "WEBP", "首页主视觉派生图不是 WebP")
                require(hero_image.size == HOME_HERO_SIZE, "首页主视觉派生图尺寸不是 1200x800")
                actual = hero_image.convert("RGB")
            if actual.size == expected.size:
                difference = image_rms(expected, actual)
                require(difference <= ARTICLE_WEB_COVER_RMS_LIMIT, f"首页主视觉派生图可能未同步（RMS {difference:.2f}）")
        except (OSError, UnidentifiedImageError) as error:
            report_error(f"无法读取首页主视觉派生图: {error}")
    if hero_original is not None and favicon_path.is_file():
        try:
            expected = ImageOps.fit(hero_original, FAVICON_SIZE, method=Image.Resampling.LANCZOS)
            with Image.open(favicon_path) as favicon_image:
                require(favicon_image.format == "PNG", "站点图标不是 PNG")
                require(favicon_image.size == FAVICON_SIZE, "站点图标尺寸不是 64x64")
                actual = favicon_image.convert("RGB")
            if actual.size == expected.size:
                require(image_rms(expected, actual) == 0, "站点图标与首页主视觉来源未同步")
        except (OSError, UnidentifiedImageError) as error:
            report_error(f"无法读取站点图标: {error}")

    return len(expected_names)


def check_docsify_asset_resolver() -> None:
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    require(
        'function resolveRootAssetPaths(hook)' in index_html
        and 'hook.afterEach(function (html)' in index_html
        and '/src=\"[^\"]*?assets\\/images\\//g' in index_html,
        "Docsify 缺少仓库根图片路径修正，深层文章路由会导致正文图片 404",
    )


def check_illustrations() -> tuple[int, Counter[str]]:
    manifest_path = ROOT / "scripts" / "illustration_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        report_error(f"无法读取插画清单: {error}")
        return 0, Counter()

    items = manifest.get("items")
    require(isinstance(items, list), "插画清单缺少 items 数组")
    if not isinstance(items, list):
        return 0, Counter()

    ids: set[str] = set()
    group_counts: Counter[str] = Counter()
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
        group_counts[group] += 1

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
                    average_rms = image_rms(expected, actual)
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

    return len(items), group_counts


def check_documented_counts(
    article_count: int,
    ai_edit_count: int,
    china_count: int,
    spanish_count: int,
    illustration_counts: Counter[str],
) -> None:
    book_readme = (ROOT / "book" / "README.md").read_text(encoding="utf-8")
    require(f"已归档正文：{article_count} 篇" in book_readme, "book/README.md 的正文规模快照已过期")
    require(f"规范评价：{article_count} 篇" in book_readme, "book/README.md 的评价规模快照已过期")
    require(f"AI 修改稿：{ai_edit_count} 篇" in book_readme, "book/README.md 的 AI 改稿规模快照已过期")

    home = (WEBSITE / "home.md").read_text(encoding="utf-8")
    require(f"<strong>{china_count}</strong> 中国地点" in home, "首页中国地点统计已过期")
    require(f"<strong>{spanish_count}</strong> 西班牙地点" in home, "首页西班牙地点统计已过期")

    footprints = (WEBSITE / "footprints.md").read_text(encoding="utf-8")
    require(f"<strong>{china_count}</strong> 个中国地点" in footprints, "足迹页中国地点统计已过期")
    require(f"<strong>{spanish_count}</strong> 个西班牙地点" in footprints, "足迹页西班牙地点统计已过期")

    literary_count = illustration_counts.get("literary-gems", 0)
    literary = (WEBSITE / "literary-gems.md").read_text(encoding="utf-8")
    require(f"共 {literary_count} 句" in literary, "佳句榜底部总数与插画清单不一致")

    fun_count = illustration_counts.get("fun-rankings", 0)
    fun_rankings = (WEBSITE / "fun-rankings.md").read_text(encoding="utf-8")
    fun_sections = len(re.findall(r"^## ", fun_rankings, re.MULTILINE))
    require(fun_sections == fun_count, f"趣味榜有 {fun_sections} 个章节，插画清单有 {fun_count} 项")


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
        "website/MAINTENANCE.md",
        "book/README.md",
        "book/01-成书目录.md",
        "book/02-时间线.md",
        "book/03-写作规划.md",
        "book/04-候选题目库.md",
        "book/reading-order.json",
        "ai-edited-articles/AI_EDITING_GUIDE.md",
        "ai-edited-articles/mapping.md",
    ]
    for relative_path in required:
        require((ROOT / relative_path).is_file(), f"缺少网站关键文件: {relative_path}")
    for legacy_name in ("catalog.md", "ranking.md", "literary-gems.md", "fun-rankings.md", "_sidebar.md"):
        require(not (ROOT / legacy_name).exists(), f"网站页面不应留在根目录: {legacy_name}")


def main() -> int:
    check_required_files()
    articles, catalog_count, review_scores = check_articles_and_catalog()
    book_part_count, book_chapter_count = check_book_reading_order(len(articles))
    ranking_count = check_ranking(review_scores)
    ai_edit_count = check_ai_edits(articles)
    link_count = check_site_links()
    china_count, world_count, spanish_count = check_footprints()
    check_docsify_asset_resolver()
    cover_count = check_cover_derivatives(articles)
    illustration_count, illustration_counts = check_illustrations()
    check_documented_counts(len(articles), ai_edit_count, china_count, spanish_count, illustration_counts)

    if errors:
        print(f"网站巡检失败，共 {len(errors)} 个问题：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("网站巡检通过")
    print(f"- 文章 / 目录 / 排名 / AI 改稿：{len(articles)} / {catalog_count} / {ranking_count} / {ai_edit_count}")
    print(f"- 已检查本地链接与图片：{link_count}")
    print(f"- 成书阅读：{book_part_count} 个部分，{book_chapter_count} 篇入选文章")
    print(f"- 足迹：中国 {china_count}，世界视图 {world_count}")
    print(f"- 文章封面派生图：{cover_count} × 2，站点资产：2")
    print(f"- 插画原图与派生图：{illustration_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
