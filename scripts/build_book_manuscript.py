#!/usr/bin/env python3
"""Build the current continuous book manuscript from the reading manifest."""

from __future__ import annotations

import argparse
from datetime import date
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
MANIFEST = BOOK / "reading-order.json"
DEFAULT_OUTPUT = BOOK / "manuscript.md"
BOOK_README = BOOK / "README.md"

FRONT_MATTER_RE = re.compile(r"^---\r?\n[\s\S]*?\r?\n---\r?\n+", re.MULTILINE)
FIRST_HEADING_RE = re.compile(r"^#\s+[^\r\n]+\r?\n+", re.MULTILINE)
BYLINE_RE = re.compile(r"^>\s*作者:.*\r?\n+", re.MULTILINE)
ARTICLE_COVER_RE = re.compile(
    r'<p>\s*<img\s+[^>]*class=["\']article-cover["\'][^>]*>\s*</p>\s*',
    re.IGNORECASE,
)
SOURCE_FOOTER_RE = re.compile(
    r"\r?\n---\r?\n+(?:\*原文(?:链接)?:[\s\S]*?\*|<nav class=[\"']ai-edit-links[\"'][\s\S]*?</nav>)\s*$",
    re.MULTILINE,
)


def read_manifest() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def article_source_path(article_path: str, source: str) -> Path:
    original = ROOT / unquote(article_path)
    if source == "original":
        return original
    article_name = original.parent.name
    category = "合集" if article_name.startswith("合集-") else "散篇"
    return ROOT / "ai-edited-articles" / category / article_name / "index.md"


def chapter_source_path(chapter: dict[str, object], source: str) -> Path:
    """Resolve a chapter without conflating its archive and public reading paths."""
    archive_path = str(chapter.get("archivePath") or chapter.get("path") or "")
    reading_path = str(chapter.get("readingPath") or "")
    if source == "edited" and reading_path:
        return ROOT / unquote(reading_path)
    return article_source_path(archive_path, source)


def clean_article(content: str) -> str:
    content = content.lstrip("\ufeff")
    content = FRONT_MATTER_RE.sub("", content, count=1)
    content = FIRST_HEADING_RE.sub("", content, count=1)
    content = BYLINE_RE.sub("", content, count=1)
    content = ARTICLE_COVER_RE.sub("", content, count=1)
    content = SOURCE_FOOTER_RE.sub("", content, count=1)
    return content.strip()


def demote_article_headings(content: str) -> str:
    """Keep chapter H2 headings distinct from headings inside an article."""
    return re.sub(
        r"(?m)^(#{2,6})(?=\s)",
        lambda match: "#" * min(len(match.group(1)) + 1, 6),
        content,
    )


def part_heading_and_intro(page: Path) -> tuple[str, str]:
    content = FRONT_MATTER_RE.sub("", page.read_text(encoding="utf-8").lstrip("\ufeff"), count=1)
    lines = content.splitlines()
    heading = next((line[2:].strip() for line in lines if line.startswith("# ")), page.stem)
    heading_index = next((index for index, line in enumerate(lines) if line.startswith("# ")), -1)
    intro_lines: list[str] = []
    for line in lines[heading_index + 1 :]:
        if line.startswith("## "):
            break
        intro_lines.append(line)
    return heading, "\n".join(intro_lines).strip()


def build_manuscript(source: str) -> str:
    manifest = read_manifest()
    output: list[str] = [
        "<!-- 此文件由 scripts/build_book_manuscript.py 自动生成，请勿手工编辑。 -->",
        "",
        "# 旧日之书",
        "",
        "> 当前工作书稿。章节顺序来自 `book/reading-order.json`，正文使用"
        + (" AI 修改稿。" if source == "edited" else " 原始归档稿。"),
        "",
        "## 总序：为什么要写旧日",
        "",
        clean_article((BOOK / "00-总序草案.md").read_text(encoding="utf-8")),
    ]

    parts = manifest.get("parts")
    if not isinstance(parts, list):
        raise ValueError("reading-order.json 缺少 parts 数组")

    for part in parts:
        if not isinstance(part, dict):
            raise ValueError("reading-order.json 包含非对象部分")
        page = ROOT / unquote(str(part["page"]))
        heading, intro = part_heading_and_intro(page)
        output.extend(["", "---", "", f"# {heading}", ""])
        if intro:
            output.extend([intro, ""])

        chapters = part.get("chapters")
        if not isinstance(chapters, list):
            raise ValueError(f"{part.get('id', '未知部分')} 缺少 chapters 数组")
        for chapter in chapters:
            if not isinstance(chapter, dict):
                raise ValueError("reading-order.json 包含非对象章节")
            title = str(chapter["title"])
            source_path = chapter_source_path(chapter, source)
            if not source_path.is_file():
                raise FileNotFoundError(f"章节源文件不存在: {source_path}")
            body = demote_article_headings(clean_article(source_path.read_text(encoding="utf-8")))
            output.extend([f"## {title}", "", body, ""])

    manuscript = "\n".join(output).strip() + "\n"
    expected_chapters = sum(
        len(part.get("chapters", [])) for part in parts if isinstance(part, dict)
    )
    expected_titles = [
        str(chapter["title"])
        for part in parts
        if isinstance(part, dict)
        for chapter in part.get("chapters", [])
        if isinstance(chapter, dict)
    ]
    actual_chapters = sum(
        len(re.findall(rf"(?m)^## {re.escape(title)}$", manuscript))
        for title in expected_titles
    )
    if actual_chapters != expected_chapters:
        raise ValueError(f"书稿章节数量错误: 预期 {expected_chapters}，实际 {actual_chapters}")
    archive_metadata = re.search(
        r"(?m)^(?:source_article|target_score|edit_round|edited|archived):\s*",
        manuscript,
    )
    if archive_metadata or "class=\"article-cover\"" in manuscript:
        raise ValueError("书稿仍包含文章归档元数据或封面块")
    if re.search(r"(?m)^\*原文(?:链接)?:", manuscript):
        raise ValueError("书稿仍包含文章原文链接")
    return manuscript


def write_text_lf(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def manuscript_stats_line(manuscript: str) -> str:
    character_count = len(manuscript)
    return f"- 当前连续书稿：{character_count:,} 字符（约 {character_count / 10000:.1f} 万）"


def sync_readme_stats(manuscript: str, *, check: bool) -> bool:
    content = BOOK_README.read_text(encoding="utf-8")
    expected_line = manuscript_stats_line(manuscript)
    current_match = re.search(r"(?m)^- 当前连续书稿：.*$", content)
    if current_match and current_match.group(0) == expected_line:
        return True
    if check:
        return False
    if not current_match:
        raise ValueError("book/README.md 缺少当前连续书稿统计行")
    updated = content[: current_match.start()] + expected_line + content[current_match.end() :]
    updated = re.sub(
        r"(?m)^> 规模快照更新于 \d{4}-\d{2}-\d{2}",
        f"> 规模快照更新于 {date.today().isoformat()}",
        updated,
        count=1,
    )
    write_text_lf(BOOK_README, updated)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=("edited", "original"),
        default="edited",
        help="正文来源，默认使用当前 AI 修改稿",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="输出 Markdown 路径",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="只检查现有输出是否可由当前源文件重复生成",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    manuscript = build_manuscript(args.source)
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != manuscript:
            print(f"成书稿需要重建: {output.relative_to(ROOT)}", file=sys.stderr)
            return 1
        if not sync_readme_stats(manuscript, check=True):
            print("book/README.md 的连续书稿统计需要重建", file=sys.stderr)
            return 1
        print(f"成书稿可重复生成: {output.relative_to(ROOT)}")
        return 0

    write_text_lf(output, manuscript)
    sync_readme_stats(manuscript, check=False)
    print(f"已生成成书稿: {output.relative_to(ROOT)}")
    print(f"- 来源: {'AI 修改稿' if args.source == 'edited' else '原始归档稿'}")
    print(f"- 字符数: {len(manuscript)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
