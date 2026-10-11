"""Generate the PWA icons, the favicon and the placeholder avatar with a green leaf.

Run with the project venv: `~/.venv/bin/python scripts/gen_icons.py`.
"""

from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public")
OUT_DIR = os.path.join(PUBLIC_DIR, "icons")
LEAF = (34, 197, 94)
LEAF_DARK = (21, 128, 61)
SUPERSAMPLE = 1024
BACKGROUND = (11, 18, 32)
PANEL = (27, 39, 64)


def _half_width(t: float, scale: float) -> float:
    return scale * 0.58 * math.sin(math.pi * t) ** 0.9 * (1 - 0.25 * t)


def _leaf_outline(n: int, scale: float, cx: float, cy: float) -> list[tuple[float, float]]:
    right = [(cx + _half_width(i / n, scale), cy - scale + 2 * scale * i / n) for i in range(n + 1)]
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    return right + left


def _leaf() -> Image.Image:
    size = SUPERSAMPLE
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy, scale = size / 2, size * 0.46, size * 0.42
    draw.polygon(_leaf_outline(200, scale, cx, cy), fill=LEAF + (255,))
    rib = size * 0.028
    draw.line([(cx, cy - scale * 0.82), (cx, cy + scale * 1.18)], fill=LEAF_DARK + (255,), width=round(rib))
    for t in (0.28, 0.44, 0.6, 0.76):
        y0 = cy - scale + 2 * scale * t
        reach = _half_width(t - 0.12, scale) * 0.6
        for side in (1, -1):
            draw.line(
                [(cx, y0), (cx + side * reach, y0 - scale * 0.24)],
                fill=LEAF_DARK + (255,),
                width=round(rib * 0.6),
            )
    layer = layer.rotate(-35, resample=Image.BICUBIC, center=(cx, size / 2))
    return _square(layer)


def _square(img: Image.Image) -> Image.Image:
    img = img.crop(img.getbbox())
    side = max(img.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return square


def _compose(size: int, emoji_ratio: float, background: tuple[int, int, int]) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), background + (255,))
    emoji_size = round(size * emoji_ratio)
    emoji = _leaf().resize((emoji_size, emoji_size), Image.LANCZOS)
    offset = (size - emoji_size) // 2
    canvas.alpha_composite(emoji, (offset, offset))
    return canvas.convert("RGB")


def generate(size: int, filename: str, emoji_ratio: float) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    _compose(size, emoji_ratio, BACKGROUND).save(os.path.join(OUT_DIR, filename))


def generate_favicon(size: int = 64) -> None:
    _leaf().resize((size, size), Image.LANCZOS).save(os.path.join(PUBLIC_DIR, "favicon.png"))


def generate_avatar_placeholder(size: int = 240) -> None:
    img_dir = os.path.join(PUBLIC_DIR, "img")
    os.makedirs(img_dir, exist_ok=True)
    _compose(size, 0.5, PANEL).save(os.path.join(img_dir, "perfil.webp"), quality=90)


def main() -> None:
    generate(192, "icon-192.png", emoji_ratio=0.72)
    generate(512, "icon-512.png", emoji_ratio=0.72)
    # Maskable icons can be cropped to a circle of 80% of the size.
    generate(512, "maskable-512.png", emoji_ratio=0.52)
    generate_favicon()
    generate_avatar_placeholder()
    print(f"Icons written to {os.path.normpath(PUBLIC_DIR)}")


if __name__ == "__main__":
    main()
