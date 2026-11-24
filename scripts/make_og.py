"""Paylaşım (Open Graph) görselini üretir: og.jpg, 1200x630.

Sol tarafta başlık, sağ tarafta ana sayfadaki ağ animasyonunun durağan hâli
(js/logo-points.js noktaları, aynı palet). Yazı tipi: Poppins ExtraBold TTF
(--font ile verilir; varsayılan: scripts/fonts/Poppins-ExtraBold.ttf, depoda yok,
github.com/google/fonts deposundaki ofl/poppins klasöründen indirilir).

Kullanım: python3 scripts/make_og.py [--font /yol/Poppins-ExtraBold.ttf]
"""
import argparse
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POINTS_JS = os.path.join(ROOT, "js", "logo-points.js")
OUT = os.path.join(ROOT, "og.jpg")

WIDTH, HEIGHT = 1200, 630
SCALE = 2                                  # kenar yumuşatma için 2 kat çiz, küçült
BG = (26, 21, 20)
INK = (254, 252, 250)
MUTED = (185, 169, 165)
PALETTE = [(239, 90, 67), (194, 64, 47), (243, 233, 228), (255, 154, 92)]
LOGO_SIZE = 500
LOGO_CENTER = (900, 315)
LINK_DIST = 0.026                          # ana sayfadaki bağlantı mesafesiyle aynı (logo boyuna oranı)
LINK_ALPHA = 0.5
DOT_RADIUS = 2.1
TITLE = ["MESEM çocuk", "işçiliğidir."]
TITLE_SIZE = 78
SUBTITLE = "MESEM'li Gençler"
TAGLINE = "Haberleşme ve dayanışma ağı"
FOOTER = "mesemligencler.com"
DEFAULT_FONT = os.path.join(ROOT, "scripts", "fonts", "Poppins-ExtraBold.ttf")  # depoda yok; --font ile ver


def load_points():
    text = open(POINTS_JS, encoding="utf-8").read()
    return json.loads(text[text.index("=") + 1:].strip().rstrip(";"))["points"]


def draw_network(img, points):
    s = SCALE
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = LOGO_CENTER
    pts = [((cx + (x - 0.5) * LOGO_SIZE) * s, (cy + (y - 0.5) * LOGO_SIZE) * s, c) for x, y, c in points]
    max_d = LINK_DIST * LOGO_SIZE * s
    for i, (x1, y1, c1) in enumerate(pts):
        for x2, y2, c2 in pts[i + 1:]:
            if abs(x1 - x2) > max_d or abs(y1 - y2) > max_d:
                continue
            if math.hypot(x1 - x2, y1 - y2) <= max_d:
                color = PALETTE[c1 if c1 != 2 else c2]
                d.line([(x1, y1), (x2, y2)], fill=color + (int(255 * LINK_ALPHA),), width=s)
    r = DOT_RADIUS * s
    for x, y, c in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=PALETTE[c] + (255,))
    img.alpha_composite(layer)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default=DEFAULT_FONT)
    args = parser.parse_args()

    s = SCALE
    img = Image.new("RGBA", (WIDTH * s, HEIGHT * s), BG + (255,))
    draw_network(img, load_points())
    d = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(args.font, TITLE_SIZE * s)
    small_font = ImageFont.truetype(args.font, 30 * s)
    foot_font = ImageFont.truetype(args.font, 22 * s)
    x = 70 * s
    y = 150 * s
    for line in TITLE:
        d.text((x, y), line, font=title_font, fill=INK)
        y += int(TITLE_SIZE * 1.18) * s
    d.text((x, y + 22 * s), SUBTITLE, font=small_font, fill=PALETTE[0])
    d.text((x, y + 70 * s), TAGLINE, font=small_font, fill=MUTED)
    d.text((x, (HEIGHT - 60) * s), FOOTER, font=foot_font, fill=MUTED)

    final = img.convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    final.save(OUT, "JPEG", quality=90, optimize=True)
    print(f"{OUT} yazıldı, {os.path.getsize(OUT) // 1024} KB")


if __name__ == "__main__":
    main()
