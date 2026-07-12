#!/usr/bin/env python3
"""Generate lightweight website derivatives from canonical article covers."""

import io
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
ARTICLE_IMAGES_DIR = ROOT / "assets" / "images" / "articles"
OUTPUT_DIR = ROOT / "assets" / "images" / "_generated"
CATALOG_DIR = OUTPUT_DIR / "catalog-covers"
HERO_SOURCE = ARTICLE_IMAGES_DIR / "合集-05-我在康杰念高中（怀昔）" / "cover.png"


def write_if_changed(path: Path, content: bytes) -> bool:
    if path.is_file() and path.read_bytes() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return True


def render_webp(source: Path, size: tuple[int, int], quality: int) -> bytes:
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="WEBP", quality=quality, method=6)
        return output.getvalue()


def render_favicon(source: Path) -> bytes:
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image = ImageOps.fit(image, (64, 64), method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()


def main() -> None:
    covers = sorted(ARTICLE_IMAGES_DIR.glob("*/cover.png"), key=lambda path: path.parent.name)
    if not covers:
        raise SystemExit(f"No article covers found under {ARTICLE_IMAGES_DIR}")

    changed = 0
    for cover in covers:
        target = CATALOG_DIR / f"{cover.parent.name}.webp"
        changed += write_if_changed(target, render_webp(cover, (480, 320), 74))

    changed += write_if_changed(
        OUTPUT_DIR / "home-hero.webp",
        render_webp(HERO_SOURCE, (1200, 800), 80),
    )
    changed += write_if_changed(OUTPUT_DIR / "favicon.png", render_favicon(HERO_SOURCE))

    generated = list(OUTPUT_DIR.rglob("*.webp")) + list(OUTPUT_DIR.rglob("*.png"))
    total_bytes = sum(path.stat().st_size for path in generated)
    print(
        f"generated {len(covers)} catalog covers and 2 site assets; "
        f"updated {changed}; total {total_bytes / 1024 / 1024:.2f} MB"
    )


if __name__ == "__main__":
    main()