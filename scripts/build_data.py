"""data/*.json dosyalarını tek bir tarayıcı betiğine (js/data.js) derler.

Neden: site sunucusuz da (dosyayı çift tıklayarak) açılabilsin; fetch()
file:// altında çalışmaz. Eksik dosya boş veriyle geçilir ve uyarı basılır.

Çıktı: window.MG_DATA = {kayiplar, onergeler, haberler, instagram}
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "js", "data.js")

SOURCES = {
    "kayiplar": ("kayiplar.json", {"kaynakNotu": "", "yillar": []}),
    "onergeler": ("onergeler.json", []),
    "haberler": ("haberler.json", []),
    "instagram": ("instagram.json", {"gonderiler": []}),
    "logolar": ("logolar.json", {}),
    "mektuplar": ("mektuplar.json", []),
}


def load(name, fallback):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        print(f"uyarı: {name} yok, boş veri kullanıldı", file=sys.stderr)
        return fallback
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as err:
            sys.exit(f"hata: {name} geçerli JSON değil: {err}")


def with_cover(letters, news):
    """Her mektuba, kaynak yazısının haber kaydındaki kapak görselini ekler (asıl sitedeki görsel)."""
    covers = {n["url"]: n.get("gorsel") for n in news if n.get("url")}
    out = []
    for letter in letters:
        cover = next((covers[k["url"]] for k in letter.get("kaynakca", []) if covers.get(k.get("url"))), None) or letter.get("gorsel")
        # Haber listesinde kapağı olmayan mektup (ör. Genç Hayat senkronu) kendi görselini taşıyabilir.
        if not cover:
            print(f"uyarı: {letter.get('id')} için kaynak görseli bulunamadı (haber listesinde yok)", file=sys.stderr)
        out.append({**letter, "gorsel": cover})
    return out


def main():
    bundle = {key: load(name, fb) for key, (name, fb) in SOURCES.items()}
    bundle["mektuplar"] = with_cover(bundle["mektuplar"], bundle["haberler"])
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* scripts/build_data.py tarafından üretildi; data/*.json dosyalarını düzenleyin. */\n")
        f.write("window.MG_DATA = ")
        json.dump(bundle, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    kisi = sum(len(y["kisiler"]) for y in bundle["kayiplar"]["yillar"])
    print(f"js/data.js yazıldı: {kisi} kişi, {len(bundle['onergeler'])} önerge, "
          f"{len(bundle['haberler'])} haber, {len(bundle['instagram']['gonderiler'])} gönderi, "
          f"{len(bundle['logolar'])} logo, {len(bundle['mektuplar'])} mektup")


if __name__ == "__main__":
    main()
