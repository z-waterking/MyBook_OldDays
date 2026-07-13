#!/usr/bin/env python3
"""Generate the full-site search index used by the Docsify front end."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "website" / "search-index.json"
FRONT_MATTER_RE = re.compile(r"^---\r?\n[\s\S]*?\r?\n---\r?\n+")


def markdown_title(content: str, fallback: str) -> str:
    front_matter = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
    if front_matter:
        title = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', front_matter.group(1), re.MULTILINE)
        if title:
            return title.group(1).strip().strip("\"'")
    heading = re.search(r"(?m)^#\s+(.+?)\s*$", content)
    return heading.group(1).strip() if heading else fallback


def plain_text(content: str) -> str:
    content = FRONT_MATTER_RE.sub("", content, count=1)
    content = re.sub(r"<[^>]+>", " ", content)
    content = re.sub(r"!\[([^]]*)\]\([^)]*\)", r" \1 ", content)
    content = re.sub(r"\[([^]]+)\]\([^)]*\)", r" \1 ", content)
    content = re.sub(r"[`#>*_|~=-]+", " ", content)
    return re.sub(r"\s+", " ", html.unescape(content)).strip()


def page_type(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if relative.startswith("articles/") and path.name == "review.md":
        return "文章评价"
    if relative.startswith("articles/"):
        return "原文档案"
    if relative.startswith("ai-edited-articles/") and path.name == "notes.md":
        return "改稿说明"
    if relative.startswith("ai-edited-articles/"):
        return "AI 改稿"
    if relative.startswith("book/"):
        return "成书阅读"
    return "网站栏目"


def source_pages() -> list[Path]:
    pages = [*ROOT.glob("articles/*/index.md"), *ROOT.glob("articles/*/review.md")]
    pages.extend(ROOT.glob("ai-edited-articles/*/*/index.md"))
    pages.extend(ROOT.glob("ai-edited-articles/*/*/notes.md"))
    pages.extend(path for path in (ROOT / "website").glob("*.md") if not path.name.startswith("_"))
    pages.extend(
        path
        for path in (ROOT / "book").glob("*.md")
        if path.name not in {"manuscript.md"}
    )
    return sorted(set(pages), key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> None:
    entries = []
    for path in source_pages():
        content = path.read_text(encoding="utf-8").lstrip("\ufeff")
        relative = path.relative_to(ROOT).as_posix()
        fallback = path.parent.name if path.name in {"index.md", "review.md", "notes.md"} else path.stem
        entries.append(
            {
                "path": relative,
                "title": markdown_title(content, fallback),
                "type": page_type(path),
                "text": plain_text(content),
            }
        )
    OUTPUT.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(f"generated {len(entries)} searchable pages: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
