#!/usr/bin/env python3
"""
Generate optimized thumbnails and display versions for art portfolio images.

Usage (run from project root):
    pip install Pillow
    python generate_thumbnails.py

Output folders:
    images/portofolio/thumbs/   — 600px max, ~30-80 KB  (used in gallery grid)
    images/portofolio/display/  — 1500px max, ~200-400 KB (used in popup lightbox)
"""

import re
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not found. Run:  pip install Pillow")
    raise SystemExit(1)

SOURCE_DIR = Path("images/portofolio")
THUMB_DIR  = SOURCE_DIR / "thumbs"
DISPLAY_DIR = SOURCE_DIR / "display"

THUMB_MAX    = 600    # px
DISPLAY_MAX  = 1500   # px
THUMB_QUALITY   = 80
DISPLAY_QUALITY = 85


def normalize_name(filename: str) -> str:
    """Lowercase, spaces → underscores, .jpeg → .jpg, strip specials."""
    stem = Path(filename).stem.strip()
    ext  = Path(filename).suffix.lower()
    stem = re.sub(r"\s+", "_", stem).lower()
    stem = re.sub(r"[^a-z0-9_\-]", "", stem)
    if ext == ".jpeg":
        ext = ".jpg"
    return stem + ext


def resize(img: Image.Image, max_px: int) -> Image.Image:
    w, h = img.size
    if w <= max_px and h <= max_px:
        return img.copy()
    ratio = min(max_px / w, max_px / h)
    return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)


def to_rgb(img: Image.Image) -> Image.Image:
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        return bg
    if img.mode not in ("RGB", "L"):
        return img.convert("RGB")
    return img


def process():
    THUMB_DIR.mkdir(exist_ok=True)
    DISPLAY_DIR.mkdir(exist_ok=True)

    supported = {".jpg", ".jpeg", ".png", ".gif"}
    results = []

    for src in sorted(SOURCE_DIR.iterdir()):
        if src.is_dir() or src.suffix.lower() not in supported:
            continue

        norm    = normalize_name(src.name)
        is_gif  = src.suffix.lower() == ".gif"

        print(f"\n{src.name!r:40s} -> {norm!r}")

        if is_gif:
            # Display: keep the animated GIF as-is
            disp_path = DISPLAY_DIR / norm
            if not disp_path.exists():
                shutil.copy2(src, disp_path)
                print(f"  display : copied original GIF")
            else:
                print(f"  display : already exists, skipped")

            # Thumb: first frame as JPEG
            thumb_name = norm[:-4] + ".jpg"
            thumb_path = THUMB_DIR / thumb_name
            if not thumb_path.exists():
                with Image.open(src) as img:
                    img.seek(0)
                    frame = resize(img.convert("RGB"), THUMB_MAX)
                    frame.save(thumb_path, "JPEG", quality=THUMB_QUALITY)
                print(f"  thumb   : {thumb_path.name}")
            else:
                print(f"  thumb   : already exists, skipped")

            results.append((src.name, thumb_name, norm))
            continue

        # Regular image
        thumb_path = THUMB_DIR  / norm
        disp_path  = DISPLAY_DIR / norm

        with Image.open(src) as img:
            img = to_rgb(img)

            if not thumb_path.exists():
                t = resize(img, THUMB_MAX)
                t.save(thumb_path, "JPEG", quality=THUMB_QUALITY, optimize=True)
                print(f"  thumb   : {t.size[0]}×{t.size[1]} px")
            else:
                print(f"  thumb   : already exists, skipped")

            if not disp_path.exists():
                d = resize(img, DISPLAY_MAX)
                d.save(disp_path, "JPEG", quality=DISPLAY_QUALITY, optimize=True)
                print(f"  display : {d.size[0]}×{d.size[1]} px")
            else:
                print(f"  display : already exists, skipped")

        results.append((src.name, norm, norm))

    print("\n\n" + "-" * 100)
    print(f"{'Original':<38} {'Thumb':<35} Display")
    print("-" * 100)
    for orig, thumb, disp in results:
        print(f"  {orig:<36} {thumb:<35} {disp}")
    print(f"\nDone! {len(results)} images processed.")
    print(f"  Thumbs  -> {THUMB_DIR}")
    print(f"  Display -> {DISPLAY_DIR}")


if __name__ == "__main__":
    process()
