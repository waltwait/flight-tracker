#!/usr/bin/env python3
"""Generate PWA icons for flight-tracker (journal stamp style)."""
from PIL import Image, ImageDraw, ImageFont
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, "icons")
os.makedirs(ICONS, exist_ok=True)

RED = (179, 48, 31, 255)      # --red stamp
CREAM = (243, 236, 220, 255)  # --bg paper
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def rounded_bg(size, radius_ratio=0.22):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * radius_ratio), fill=RED)
    return img, d


def draw_icon(size, padding_ratio):
    """padding_ratio: fraction of size kept as safe padding (for maskable)."""
    img, d = rounded_bg(size)
    pad = int(size * padding_ratio)
    # stamp double border
    d.rounded_rectangle([pad, pad, size - 1 - pad, size - 1 - pad],
                        radius=int(size * 0.12), outline=CREAM, width=max(2, size // 128))
    pad2 = pad + max(4, size // 64)
    d.rounded_rectangle([pad2, pad2, size - 1 - pad2, size - 1 - pad2],
                        radius=int(size * 0.10), outline=CREAM, width=max(1, size // 256))
    # plane glyph
    fs = int(size * (0.42 if padding_ratio < 0.1 else 0.34))
    font = ImageFont.truetype(FONT, fs)
    glyph = "✈"
    bbox = d.textbbox((0, 0), glyph, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1] - size * 0.02),
           glyph, font=font, fill=CREAM)
    return img


# standard icons (full bleed)
draw_icon(512, 0.06).save(os.path.join(ICONS, "icon-512.png"))
draw_icon(192, 0.06).save(os.path.join(ICONS, "icon-192.png"))
# maskable: keep content inside central safe zone
draw_icon(512, 0.16).save(os.path.join(ICONS, "icon-512-maskable.png"))
# apple touch icon (180, no transparency issues)
apple = draw_icon(180, 0.06).convert("RGB")
apple.save(os.path.join(ICONS, "apple-touch-icon.png"))

for f in sorted(os.listdir(ICONS)):
    p = os.path.join(ICONS, f)
    im = Image.open(p)
    print(f, im.size, os.path.getsize(p), "bytes")
