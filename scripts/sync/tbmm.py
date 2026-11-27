"""Meclis Önergeleri: TBMM'deki MESEM'le ilgili yazılı soru önergelerini data/onergeler.json'a ekler.

Neden: önergeler elle, haberlerden derleniyordu. TBMM'nin yazılı soru önergesi araması
(https://www.tbmm.gov.tr/denetim/yazili-soru-onergeleri) "MESEM" kelimesiyle herkese açık sorgulanabiliyor.

Akış: arama sayfası (CSRF) → sonuç tablosu (DataTables POST) → her yeni önergenin detay sayfası
(muhatap, metin PDF'i) → PDF'teki numaralı sorular. Önerge tablosunda parti boş geldiği için parti,
TBMM'nin milletvekili listesinden (/milletvekili/AllList) vekil kimliğiyle okunur.

Haberden girilmiş, esas numarası olmayan bir kayıt aynı vekilin ±10 gün içindeki önergesiyse yeni kayıt
açılmaz, o kayda yalnızca esas numarası eklenir.

Kullanım:
    python scripts/sync/tbmm.py              # son 21 günü tara, yenileri ekle
    python scripts/sync/tbmm.py --days 90    # daha geriye bak
    python scripts/sync/tbmm.py --dry-run
"""
import argparse
import html
import http.cookiejar
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

import common as c

BASE = "https://www.tbmm.gov.tr"
SEARCH_PAGE = f"{BASE}/denetim/yazili-soru-onergeleri"
RESULT_PAGE = f"{BASE}/Denetim/Yazili-Soru-Onergeleri-Sonuc"
TABLE_URL = f"{BASE}/Denetim/YaziliSoruOnergesiTable"
DETAIL_URL = f"{BASE}/Denetim/Yazili-Soru-Onergesi-Detay/{{id}}"
TOKEN_NAME = "X-CSRF-TOKEN-TBMM-WEB-Mvc-Prod"
KEYWORD = "MESEM"
DEFAULT_DAYS = 21  # haftalık çalışır; bir iki çalıştırma kaçsa da yakalasın
MP_LIST_URL = f"{BASE}/milletvekili/AllList"
# TBMM listesindeki yazım → sitede kullanılan ad (onergeler.js'deki PARTY anahtarları).
PARTY_NAMES = {
    "dem parti̇": "DEM Parti", "dem parti": "DEM Parti", "saadet partisi": "Saadet Partisi",
    "yeni yol": "Yeni Yol", "bağımsız": "Bağımsız", "yeniden refah": "Yeniden Refah", "hüda par": "HÜDA PAR",
}
DATA_FILE = "onergeler.json"
MAX_QUESTIONS = 12


# ---------- TBMM ----------

def session():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def search(op, since, until):
    page = c.fetch_text(SEARCH_PAGE, opener=op)
    tok = re.search(rf'name="{TOKEN_NAME}"[^>]*value="([^"]+)"', page)
    if not tok:
        raise c.SyncError("arama sayfasında CSRF anahtarı yok")
    form = {TOKEN_NAME: tok.group(1), "AranacakKelime": KEYWORD,
            "BaslangicTarihi": since.strftime("%d.%m.%Y"), "BitisTarihi": until.strftime("%d.%m.%Y")}
    result = c.fetch_text(RESULT_PAGE, data=urllib.parse.urlencode(form).encode(), opener=op)
    script = next((s for s in re.findall(r"<script[^>]*>(.*?)</script>", result, re.S) if "mecTable" in s), None)
    if not script:
        raise c.SyncError("sonuç sayfasında tablo betiği yok")
    table_tok = re.search(rf'"{TOKEN_NAME}":\s*"([^"]+)"', script).group(1)
    payload = json.loads(re.search(r'data:\s*(\{"AranacakKelime"[^\n]*\})\s*,\s*\n', script).group(1))
    columns = re.findall(r'"data":\s*"([^"]+)"', script)
    # Sunucu DataTables'ın tüm parametrelerini bekliyor; eksik olursa "null" döner.
    fields = [(k, "" if v is None else (str(v).lower() if isinstance(v, bool) else str(v)))
              for k, v in payload.items() if not isinstance(v, list)]
    fields += [("draw", "1"), ("start", "0"), ("length", "500"), ("search[value]", ""), ("search[regex]", "false"),
               ("order[0][column]", "0"), ("order[0][dir]", "asc")]
    for i, col in enumerate(columns):
        fields += [(f"columns[{i}][data]", col), (f"columns[{i}][name]", ""), (f"columns[{i}][searchable]", "true"),
                   (f"columns[{i}][orderable]", "false"), (f"columns[{i}][search][value]", ""),
                   (f"columns[{i}][search][regex]", "false")]
    raw = c.fetch(TABLE_URL, data=urllib.parse.urlencode(fields).encode(), opener=op,
                  headers={TOKEN_NAME: table_tok, "X-Requested-With": "XMLHttpRequest", "Referer": RESULT_PAGE})
    table = json.loads(raw or b"null")
    if not isinstance(table, dict) or "data" not in table:
        raise c.SyncError("sonuç tablosu boş döndü (parametreler değişmiş olabilir)")
    return table["data"]


def detail(op, kanun_id):
    """(muhatap, PDF adresi, sayfa adresi)."""
    url = DETAIL_URL.format(id=kanun_id)
    page = c.fetch_text(url, opener=op)
    text = c.strip_tags(page)
    m = re.search(r"Önergenin Muhatabı\s+(.*?)\s+Önergeyi Cevaplayan", text)
    muhatap = None
    if m:
        # "Çalışma Ve Sosyal Güvenlik Bakanı Vedat IŞIKHAN" → "Çalışma ve Sosyal Güvenlik Bakanı"
        role = re.match(r"(.*?(?:Bakanı|Cumhurbaşkanı Yardımcısı|Cumhurbaşkanı))(?:\s|$)", m.group(1))
        muhatap = re.sub(r"\bVe\b", "ve", role.group(1)) if role else None
    pdf = re.search(r'href="(https://cdn\.tbmm\.gov\.tr/[^"]+\.pdf)"', page)
    return muhatap, pdf.group(1) if pdf else None, url


def questions(pdf_url):
    """PDF'teki numaralı sorular; metin katmanı yoksa ya da numara yoksa boş liste."""
    try:
        from pypdf import PdfReader
        text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(c.fetch(pdf_url))).pages)
    except Exception as e:  # PDF okunamazsa önerge yine eklenir, sorular boş kalır
        print(f"    ! PDF okunamadı: {e}", flush=True)
        return []
    found = re.findall(r"(?ms)^\s*(\d{1,2})\s*[-.)]\s+(.+?)(?=^\s*\d{1,2}\s*[-.)]\s+|\Z)", text)
    out = []
    for _, q in found:
        q = re.sub(r"\s+", " ", q).strip()
        q = q.replace("MEŞEM", "MESEM")  # PDF metni OCR'lı; en sık hata
        # Sayfa alt bilgisi (adres, telefon) bir sonraki numaraya kadar karışabiliyor; soru son "?"ta biter.
        if "?" not in q:
            continue
        q = q[: q.rfind("?") + 1]
        if 10 <= len(q) <= 600:
            out.append(q)
    return out[:MAX_QUESTIONS]


# ---------- Parti ----------

def party_map(op):
    """TBMM'nin tam listesinden {vekil kimliği: parti}; önergedeki onergeSahibiId ile aynı kimlik."""
    try:
        page = c.fetch_text(MP_LIST_URL, opener=op)
    except c.SyncError as e:
        print(f"  ! milletvekili listesi okunamadı, parti boş kalacak: {e}", flush=True)
        return {}
    rows = re.findall(r'milletvekilidetay\?DonemId=[^&"]+&(?:amp;)?Id=([0-9a-f-]+)"[^>]*>[^<]+</a>\s*</div>\s*'
                      r'<div class="col-md-4 text-right">\s*([^<]*?)\s*</div>', page, re.I)
    return {mp_id: PARTY_NAMES.get(c.tr_lower(html.unescape(p)), html.unescape(p)) for mp_id, p in rows if p}


# ---------- Veri ----------

def find_news_record(data, vekil, day):
    """Haberden girilmiş, esas numarası olmayan aynı vekilin yakın tarihli kaydı."""
    # Haber kaydı "İskender Bayhan, Sevda Karaca" gibi birden çok vekili ya da soyadın bir kısmını
    # ("Sevda Karaca" / TBMM'de "Sevda Karaca Demir") içerebilir: ad ve soyadlardan biri geçiyorsa aynı kişi.
    first, *rest = c.tr_lower(vekil).split()
    best = None
    for rec in data:
        if rec.get("esasNo") or not rec.get("tarih"):
            continue
        words = set(re.findall(r"\w+", c.tr_lower(rec.get("vekil") or "")))
        if first not in words or not words & set(rest):
            continue
        gap = abs((date.fromisoformat(rec["tarih"]) - day).days)
        if gap <= 10 and (best is None or gap < best[0]):
            best = (gap, rec)
    return best[1] if best else None


def run(days, dry_run):
    data = c.load_json(DATA_FILE)
    known = {r.get("esasNo") for r in data if r.get("esasNo")}
    until = date.today()
    op = session()
    rows = search(op, until - timedelta(days=days), until)
    print(f"TBMM: son {days} günde '{KEYWORD}' geçen {len(rows)} yazılı soru", flush=True)
    parties = None
    changed = False
    # Eskiden yeniye: haber kaydı önce kendi tarihine en yakın önergeyle eşleşsin.
    for row in sorted(rows, key=lambda r: r["baskanligaGelisTarihiDt"]):
        esas = f"{row['taksimNo']}/{row['esasNo']}"
        if esas in known:
            continue
        vekil = c.tr_title(f"{row['onergeSahibiAdi']} {row['onergeSahibiSoyadi']}")
        day = datetime.fromisoformat(row["baskanligaGelisTarihiDt"]).date()
        match = find_news_record(data, vekil, day)
        if match is not None:
            print(f"  = {esas} {vekil}: haberden girilmiş kayıt vardı, esas no eklendi", flush=True)
            match["esasNo"] = esas
            known.add(esas)
            changed = True
            continue
        if parties is None:
            parties = party_map(op)
        muhatap, pdf, url = detail(op, row["yasamaKanunId"])
        ozet = (row.get("onergeOzeti") or "").strip()
        record = {
            "vekil": vekil,
            "parti": parties.get(row.get("onergeSahibiId")),
            "il": c.tr_title(row.get("ilAdi") or "") or None,
            "tur": "Yazılı soru",
            "esasNo": esas,
            "tarih": day.isoformat(),
            "muhatap": muhatap,
            "konu": c.tr_capitalize(ozet) + ("" if ozet.endswith(".") else ".") if ozet else None,
            "sorular": questions(pdf) if pdf else [],
            "url": url,
            "kaynakTuru": "TBMM",
        }
        data.append(record)
        known.add(esas)
        changed = True
        print(f"  + {esas} {vekil} ({record['parti'] or 'parti ?'}), {record['tarih']}, {muhatap}, "
              f"{len(record['sorular'])} soru", flush=True)
    if not changed:
        print("değişiklik yok.", flush=True)
        return
    data.sort(key=lambda r: r.get("tarih") or "", reverse=True)
    if dry_run:
        print("--dry-run: hiçbir şey yazılmadı.", flush=True)
        return
    c.write_json(DATA_FILE, data)
    c.rebuild()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        run(args.days, args.dry_run)
    except (c.SyncError, KeyError, ValueError) as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
