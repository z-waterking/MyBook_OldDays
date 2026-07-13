#!/usr/bin/env python3
"""Synchronize public book-page links with reading-order.json readingPath values."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote, unquote


ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
MANIFEST = BOOK / "reading-order.json"


def path_variants(value: str) -> set[str]:
    decoded = unquote(value)
    return {value, decoded, quote(decoded, safe="/()（）·_-—")}


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    replacements: dict[str, str] = {}
    pages = {BOOK / "01-成书目录.md"}
    for part in manifest["parts"]:
        pages.add(ROOT / unquote(part["page"]))
        for chapter in part["chapters"]:
            archive_path = chapter["archivePath"]
            reading_path = chapter["readingPath"]
            for variant in path_variants(archive_path):
                replacements[variant] = reading_path

    changed = 0
    for page in sorted(pages):
        content = page.read_text(encoding="utf-8")
        updated = content
        for source, target in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            updated = updated.replace(f"]({source})", f"]({target})")
        if updated != content:
            page.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1
    print(f"synchronized {changed} book reading pages")


if __name__ == "__main__":
    main()
