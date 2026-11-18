"""Google Fonts yazı tiplerini siteye gömer (tek seferlik).

Neden: voltran.space kök dizinindeki güvenlik kuralı (CSP) yalnızca aynı kökenden
font yüklemeye izin veriyor; fonts.googleapis.com engelleniyor.

Üretir: assets/fonts/*.woff2 ve css/fonts.css (yalnızca latin ve latin-ext: Türkçe için yeterli).
Yazı tipleri SIL Open Font License altında, gömülerek dağıtılabilir.
"""
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
CSS_OUT = os.path.join(ROOT, "css", "fonts.css")
CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Bricolage+Grotesque:opsz,wght@12..96,500..800"
    "&family=Instrument+Sans:wght@400..700"
    "&family=Poppins:wght@500;600;700;800&display=swap"
)
# woff2 sürümünü almak için modern bir tarayıcı başlığı gerekir
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
KEEP_SUBSETS = {"latin", "latin-ext"}
TIMEOUT_SEC = 30

BLOCK = re.compile(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", re.S)


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    os.makedirs(FONT_DIR, exist_ok=True)
    css = fetch(CSS_URL)
    out = ["/* scripts/fetch_fonts.py tarafından üretildi; elle düzenlemeyin. */"]
    count = 0
    for subset, block in BLOCK.findall(css):
        if subset not in KEEP_SUBSETS:
            continue
        family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        weight = re.search(r"font-weight:\s*([^;]+);", block).group(1).strip().replace(" ", "-")
        src = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not src:
            sys.exit(f"hata: {family} {subset} için woff2 adresi yok")
        name = f"{slug(family)}-{weight}-{subset}.woff2"
        with open(os.path.join(FONT_DIR, name), "wb") as f:
            f.write(fetch(src.group(1), binary=True))
        out.append(block.replace(src.group(1), f"../assets/fonts/{name}"))
        count += 1
    with open(CSS_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    size = sum(os.path.getsize(os.path.join(FONT_DIR, n)) for n in os.listdir(FONT_DIR))
    print(f"{count} yazı tipi dosyası indirildi, toplam {size // 1024} KB -> {CSS_OUT}")


if __name__ == "__main__":
    main()
