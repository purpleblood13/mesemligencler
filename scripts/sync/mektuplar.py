"""Mektuplarımız: Genç Hayat'ın MESEM dosyasına (genchayat.net/dosyalar/mesem) eklenen yeni yazıları ekler.

Neden: mektuplar elle seçilip build_letters.py ile üretiliyordu. Dosya sayfası, Genç Hayat'ın
"MESEM" etiketli yazılarıdır ve API'den okunabilir (/api/articles?label=MESEM).

Yalnızca SINCE tarihinden (dosyanın otomatik izlenmeye başladığı gün) sonra eklenen ve listede
olmayan yazılar alınır; mevcut kayıtlara dokunulmaz. build_letters.py'nin main()'i çağrılmaz:
data/mektuplar.json elle düzenlenmiş kayıtlar içerir ve onu baştan yazar.

Kullanım:
    python scripts/sync/mektuplar.py [--dry-run] [--since 2026-11-27]
"""
import argparse
import hashlib
import io
import json
import sys
from datetime import date, datetime
from pathlib import Path

import common as c

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_letters as bl  # noqa: E402  (body, issue_dates: Genç Hayat biçimini çözen mevcut kod)

SINCE = date(2026, 11, 27)
API = "https://genchayat.net/api"
SITE = "https://genchayat.net/articles"
DATA_FILE = "mektuplar.json"
NEWS_DIR = c.ROOT / "assets" / "news"
IMG_MAX, IMG_Q = 800, 80


def get_json(url):
    return json.loads(c.fetch(url, headers={"Accept": "application/json"}))


def save_image(url, key):
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(c.fetch(url))).convert("RGB")
        img.thumbnail((IMG_MAX, IMG_MAX))
        rel = f"assets/news/{key}.webp"
        NEWS_DIR.mkdir(parents=True, exist_ok=True)
        img.save(c.ROOT / rel, "WEBP", quality=IMG_Q, method=6)
        return rel
    except Exception as e:  # görselsiz de eklenir
        print(f"    ! görsel alınamadı: {e}", flush=True)
        return None


def letter(article_id, dates):
    a = get_json(f"{API}/articles/{article_id}")
    number = int(a["issueNumber"])
    day = dates.get(number) or datetime.fromtimestamp(int(a["createdAt"]) / 1000).strftime("%Y-%m-%d")
    title = a["title"].strip()
    where = ", ".join(x for x in [a.get("school"), a.get("place")] if x)
    who = f"{a.get('author') or 'Genç Hayat'}" + (f" ({where})" if where else "")
    # Sayfa her paragrafı düz metin olarak basar; ara başlıklar da paragraf olur.
    text = [p["ara"] if isinstance(p, dict) else p for p in bl.body(a)]
    return {
        "id": a["slug"],
        "baslik": title,
        "tarih": day,
        "kaynakAdi": f"Genç Hayat, Sayı {number}",
        "metin": text,
        "kaynakca": [{"metin": f'Genç Hayat, Sayı {number}, "{title}", {who}.', "url": f"{SITE}/{a['slug']}"}],
        "_gorselUrl": a.get("imageUrl"),
    }


def run(since, dry_run):
    data = c.load_json(DATA_FILE)
    known_ids = {m["id"] for m in data}
    known_urls = {c.norm_url(k.get("url")) for m in data for k in m.get("kaynakca", [])}
    articles = get_json(f"{API}/articles?label=MESEM")
    known_titles = {c.tr_lower(m["baslik"]).strip() for m in data}
    fresh = []
    for a in articles:
        title = c.tr_lower(a.get("title") or "").strip()
        # Genç Hayat aynı yazıyı bazen iki kimlikle yayımlıyor; başlık da anahtar.
        if (datetime.fromtimestamp(int(a["createdAt"]) / 1000).date() >= since and title not in known_titles
                and a.get("slug") not in known_ids and c.norm_url(f"{SITE}/{a.get('slug')}") not in known_urls):
            fresh.append(a)
            known_titles.add(title)
    print(f"Genç Hayat MESEM dosyası: {len(articles)} yazı, {since} sonrası yeni: {len(fresh)}", flush=True)
    if not fresh:
        print("değişiklik yok.", flush=True)
        return
    dates = {int(i["number"]): i["date"] for i in get_json(f"{API}/issues") if i.get("date")}
    added = []
    for a in fresh:
        rec = letter(a["id"], dates)
        words = sum(len(p.split()) for p in rec["metin"])
        print(f"  + {rec['tarih']} {rec['baslik'][:80]} ({words} kelime)", flush=True)
        added.append(rec)
    if dry_run:
        print("--dry-run: hiçbir şey yazılmadı.", flush=True)
        return
    for rec in added:
        img = rec.pop("_gorselUrl")
        if img:
            rec["gorsel"] = save_image(img, hashlib.sha1(rec["id"].encode()).hexdigest()[:12])
    data.extend(added)
    data.sort(key=lambda m: m.get("tarih") or "", reverse=True)
    c.write_json(DATA_FILE, data)
    c.rebuild()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", type=date.fromisoformat, default=SINCE)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        run(args.since, args.dry_run)
    except (c.SyncError, KeyError, ValueError) as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
