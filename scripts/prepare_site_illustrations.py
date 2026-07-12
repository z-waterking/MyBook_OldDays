#!/usr/bin/env python3
"""Create web derivatives and inject illustration blocks into curated pages."""

import json
import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "illustration_manifest.json"
SOURCE_ROOT = ROOT / "assets" / "images" / "illustrations"
WEB_ROOT = ROOT / "assets" / "images" / "_generated" / "illustrations"
BLOCK_RE = re.compile(
    r"\n?<figure class=\"section-illustration\" data-illustration=\"[^\"]+\">[\s\S]*?</figure>\n?"
)


def encode_webp(source: Path) -> bytes:
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image = ImageOps.fit(image, (960, 640), method=Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="WEBP", quality=78, method=6)
        return output.getvalue()


def write_if_changed(path: Path, content: bytes) -> bool:
    if path.is_file() and path.read_bytes() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return True


def illustration_block(item: dict) -> str:
    filename = Path(item["filename"]).with_suffix(".webp").name
    src = f"assets/images/_generated/illustrations/{item['group']}/{filename}"
    return (
        f'<figure class="section-illustration" data-illustration="{item["id"]}">\n'
        f'  <img src="{src}" alt="{item["alt"]}" loading="lazy" decoding="async" '
        'width="960" height="640">\n'
        '</figure>'
    )


def inject_page(path: Path, items: list[dict]) -> bool:
    original = path.read_text(encoding="utf-8")
    text = BLOCK_RE.sub("\n", original)
    for item in items:
        heading = item["heading"]
        if heading not in text:
            raise ValueError(f"Heading not found in {path}: {heading}")
        text = text.replace(heading, f"{heading}\n\n{illustration_block(item)}", 1)
    text = re.sub(r"\n{4,}", "\n\n\n", text).rstrip() + "\n"
    if text == original:
        return False
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = []
    updated_derivatives = 0
    for item in manifest["items"]:
        source = SOURCE_ROOT / item["group"] / item["filename"]
        if not source.is_file():
            missing.append(item["id"])
            continue
        target = WEB_ROOT / item["group"] / Path(item["filename"]).with_suffix(".webp")
        updated_derivatives += write_if_changed(target, encode_webp(source))

    if missing:
        raise SystemExit(
            f"Missing {len(missing)} source illustration(s): {', '.join(missing[:8])}"
            + ("..." if len(missing) > 8 else "")
        )

    changed_pages = 0
    by_page: dict[str, list[dict]] = {}
    for item in manifest["items"]:
        by_page.setdefault(item["page"], []).append(item)
    for relative_path, items in by_page.items():
        changed_pages += inject_page(ROOT / relative_path, items)

    web_files = list(WEB_ROOT.rglob("*.webp"))
    total_bytes = sum(path.stat().st_size for path in web_files)
    print(
        f"prepared {len(web_files)} web illustrations; updated {updated_derivatives}; "
        f"changed pages {changed_pages}; total {total_bytes / 1024 / 1024:.2f} MB"
    )


if __name__ == "__main__":
    main()
