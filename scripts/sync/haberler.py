"""Haberler: Evrensel, BirGün, Bianet, T24 ve Cumhuriyet'teki yeni MESEM haberlerini data/haberler.json'a ekler.

Neden: haberler elle derleniyordu. Her sitenin kendi arama sayfası ya da RSS'i MESEM haberlerini
listeler; habere ait başlık, kısa açıklama, görsel ve tarih makalenin kendi paylaşım etiketlerinden
(og:title, og:description, og:image, article:published_time) okunur. Haber metni kopyalanmaz.

Kaynak başına bulma yolu:
    Evrensel, Cumhuriyet: arama sayfası (son haberler, günlerce geriye gider)
    Bianet: RSS (yaklaşık bir aylık)
    BirGün, T24: RSS (yalnızca son ~1 gün; 3 günde bir çalışınca arada kalan haberler kaçabilir)

Yalnızca başlığında ya da açıklamasında "MESEM" geçen ve son WINDOW_DAYS gün içinde yayımlanan
haberler eklenir. Görsel 800 px WebP olarak assets/news/'e indirilir.

Kullanım:
    python scripts/sync/haberler.py [--dry-run] [--days 10]
"""
import argparse
import hashlib
import io
import re
import sys
from datetime import date, datetime, timedelta

import common as c

WINDOW_DAYS = 10  # 3 günde bir çalışır; kaçan bir çalıştırmayı da kapsasın
DATA_FILE = "haberler.json"
NEWS_DIR = c.ROOT / "assets" / "news"
IMG_MAX, IMG_Q = 800, 80
SUMMARY_MAX = 400
SOURCES = {
    "Evrensel": {"search": "https://www.evrensel.net/arama?q=mesem", "pattern": r"https://www\.evrensel\.net/haber/\d+/[^\"'#?]+"},
    "Cumhuriyet": {"search": "https://www.cumhuriyet.com.tr/arama/mesem",
                   "pattern": r"https://www\.cumhuriyet\.com\.tr/[a-z-]+/[^\"'#?]+-\d{5,}"},
    "Bianet": {"rss": "https://bianet.org/rss/biamag"},
    "BirGün": {"rss": "https://www.birgun.net/rss/home"},
    "T24": {"rss": "https://t24.com.tr/rss"},
}
TITLE_SUFFIX = re.compile(r"\s*[-|–]\s*(Evrensel|Cumhuriyet|BirGün|Birgün|bianet|Bianet|T24)\s*$", re.I)


def has_mesem(text):
    return "mesem" in c.tr_lower(text or "")


def candidates(name, cfg):
    """(url, rss_başlığı) listesi; RSS'te başlıkta MESEM yoksa sayfaya hiç gidilmez."""
    if "search" in cfg:
        page = c.fetch_text(cfg["search"])
        return [(u, None) for u in dict.fromkeys(re.findall(cfg["pattern"], page)) if "mesem" in u.lower()]
    feed = c.fetch_text(cfg["rss"])
    out = []
    for item in re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", feed, re.S):
        link = re.search(r"<link>\s*(?:<!\[CDATA\[)?\s*(\S+?)\s*(?:\]\]>)?\s*</link>|<link[^>]+href=\"([^\"]+)\"", item)
        title = re.search(r"<title>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</title>", item, re.S)
        desc = re.search(r"<(?:description|summary)>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</(?:description|summary)>", item, re.S)
        text = f"{title.group(1) if title else ''} {c.strip_tags(desc.group(1)) if desc else ''}"
        if link and has_mesem(text):
            out.append((link.group(1) or link.group(2), title.group(1).strip() if title else None))
    return out


def meta(page, *names):
    for n in names:
        m = (re.search(rf'<meta[^>]+(?:property|name|itemprop)="{n}"[^>]*content="([^"]*)"', page)
             or re.search(rf'<meta[^>]+content="([^"]*)"[^>]*(?:property|name|itemprop)="{n}"', page))
        if m and m.group(1).strip():
            return c.strip_tags(m.group(1))
    return None


def published(page):
    raw = meta(page, "article:published_time", "datePublished", "pubdate", "date")
    if not raw:
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', page)
        raw = m.group(1) if m else None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date() if raw else None
    except ValueError:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
        return date.fromisoformat(m.group(1)) if m else None


def save_image(url, key):
    """Görseli 800 px WebP olarak kaydeder; olmazsa None (haber görselsiz eklenir)."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(c.fetch(url))).convert("RGB")
        img.thumbnail((IMG_MAX, IMG_MAX))
        rel = f"assets/news/{key}.webp"
        NEWS_DIR.mkdir(parents=True, exist_ok=True)
        img.save(c.ROOT / rel, "WEBP", quality=IMG_Q, method=6)
        return rel
    except Exception as e:  # görsel yoksa haber yine eklenir
        print(f"    ! görsel alınamadı: {e}", flush=True)
        return None


def article(url, source, since, rss_title):
    page = c.fetch_text(url)
    title = TITLE_SUFFIX.sub("", meta(page, "og:title", "twitter:title") or rss_title or "").strip()
    summary = meta(page, "og:description", "description", "twitter:description") or ""
    if not title or not (has_mesem(title) or has_mesem(summary)):
        return None, "başlıkta ya da açıklamada MESEM yok"
    day = published(page)
    if day is None:
        return None, "yayın tarihi okunamadı"
    if day < since:
        return None, f"eski ({day})"
    if len(summary) > SUMMARY_MAX:
        summary = summary[:SUMMARY_MAX].rsplit(" ", 1)[0] + "…"
    image = meta(page, "og:image", "twitter:image")
    return {
        "baslik": title,
        "kaynak": source,
        "tarih": day.isoformat(),
        "url": url,
        "ozet": summary or None,
        "etiket": "diğer",
        "gorsel": None,
        "_gorselUrl": image,
    }, None


def run(days, dry_run):
    data = c.load_json(DATA_FILE)
    known = {c.norm_url(h.get("url")) for h in data}
    since = date.today() - timedelta(days=days)
    added = []
    for name, cfg in SOURCES.items():
        try:
            found = candidates(name, cfg)
        except c.SyncError as e:
            print(f"  ! {name}: liste okunamadı: {e}", flush=True)
            continue
        new = [(u, t) for u, t in found if c.norm_url(u) not in known]
        print(f"{name}: {len(found)} aday, {len(new)} yeni", flush=True)
        for url, rss_title in new:
            try:
                rec, why = article(url, name, since, rss_title)
            except c.SyncError as e:
                print(f"  ! {url}: {e}", flush=True)
                continue
            known.add(c.norm_url(url))
            if rec is None:
                print(f"  - {url} atlandı: {why}", flush=True)
                continue
            added.append(rec)
            print(f"  + {rec['tarih']} {name}: {rec['baslik'][:90]}", flush=True)
    if not added:
        print("değişiklik yok.", flush=True)
        return
    if dry_run:
        print("--dry-run: hiçbir şey yazılmadı.", flush=True)
        return
    for rec in added:
        img = rec.pop("_gorselUrl")
        if img:
            rec["gorsel"] = save_image(img, hashlib.sha1(rec["url"].encode()).hexdigest()[:12])
    data.extend(added)
    data.sort(key=lambda h: h.get("tarih") or "", reverse=True)
    c.write_json(DATA_FILE, data)
    c.rebuild()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=WINDOW_DAYS)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        run(args.days, args.dry_run)
    except c.SyncError as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
