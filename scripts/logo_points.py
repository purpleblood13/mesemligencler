"""Logodan ağ animasyonu için nokta bulutu üretir.

Girdi:  assets/logo/profile.jpg (Instagram profil fotoğrafı, 150x150)
Çıktı:  js/logo-points.js  ->  window.MG_LOGO = {size, points: [[x, y, renkIndeksi], ...]}

Logo koyu zemine ters çevrilerek okunur: kırmızı pikseller kırmızı tonlarına,
koyu (siyah) çizgiler kâğıt beyazına eşlenir, beyaz zemin atlanır.
Koordinatlar 0..1 aralığına normalize edilir.
"""
import json
import math
import os
import random

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "logo", "profile.jpg")
OUT = os.path.join(ROOT, "js", "logo-points.js")

GRID_STEP = 2          # piksel aralığı (150px logoda ~2 = yoğun)
MAX_POINTS = 2400      # canvas performansı için üst sınır
JITTER = 0.3           # ızgara görüntüsünü kırmak için piksel cinsinden sarsma
RING_KEEP = 0.93       # dış kenar halkasındaki gürültüyü atmak için yarıçap oranı
INNER_DISC = 0.69      # resimli iç diskin yarıçap oranı; dışı yazılı beyaz halka

# Renk indeksleri network.js içindeki PALETTE dizisiyle eşleşir
RED, RED_DARK, CREAM, EMBER = 0, 1, 2, 3


def is_red(r, g, b):
    return r > 120 and r > g * 1.6 and r > b * 1.6


def classify_ring(r, g, b):
    """Halka: beyaz zemin üstünde siyah yazı -> yazı açık nokta, zemin boş."""
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return CREAM if lum < 110 else None


def classify_disc(r, g, b):
    """İç disk: kırmızı figürler (el sıkışma, fabrika) kırmızı; beyaz parlamalar
    açık nokta; koyu çizgiler ve gri gökyüzü zemin olarak boş kalır."""
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if is_red(r, g, b):
        if r > 215 and g > 85:
            return EMBER
        return RED if r > 175 else RED_DARK
    if lum > 215:
        return CREAM
    return None


def main():
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    cx, cy, radius = w / 2, h / 2, min(w, h) / 2
    px = img.load()
    rng = random.Random(7)
    points = []
    for y in range(0, h, GRID_STEP):
        for x in range(0, w, GRID_STEP):
            dist = math.hypot(x - cx, y - cy)
            if dist > radius * RING_KEEP:
                continue
            classify = classify_disc if dist < radius * INNER_DISC else classify_ring
            idx = classify(*px[x, y])
            if idx is None:
                continue
            jx = x + rng.uniform(-JITTER, JITTER)
            jy = y + rng.uniform(-JITTER, JITTER)
            points.append([round(jx / w, 4), round(jy / h, 4), idx])
    rng.shuffle(points)
    points = points[:MAX_POINTS]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* scripts/logo_points.py tarafından üretildi; elle düzenlemeyin. */\n")
        f.write("window.MG_LOGO = ")
        json.dump({"size": [w, h], "points": points}, f, separators=(",", ":"))
        f.write(";\n")
    counts = {i: sum(1 for p in points if p[2] == i) for i in range(4)}
    print(f"{len(points)} nokta yazıldı -> {OUT}  renk dağılımı: {counts}")


if __name__ == "__main__":
    main()
