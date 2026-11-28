"""Kayıplarımız: İSİG Meclisi'nin Instagram paylaşımlarından çocuk işçi ölümlerini ekler ve doğrular.

Neden: kayıplar listesi elle (bircocukeksik.org'dan) derleniyordu ve aylarca geride kalıyordu.
İSİG her çocuk işçi ölümünü aynı kalıpla paylaşır:
    "Bu yıl tespit edebildiğimiz 81. çocuk işçi ölümü.. Ad Soyad.. 16 yaşında.. ... İl İlçe'de ... hayatını kaybetti.."
Bu betik o kalıbı okur. Kalıba tam uymayan paylaşım eklenmez, yalnızca loglanır (yanlış bilgi
yayınlamaktansa eksik bırakmak). Giriş, şifre, çerez kullanılmaz; yalnızca public embed sayfaları okunur.

Komutlar:
    python scripts/kayiplar/isig_sync.py discover          # son paylaşımlardaki yeni çocuk ölümlerini ekle
    python scripts/kayiplar/isig_sync.py verify            # İSİG kodu olan kayıtları yeniden oku, değişeni güncelle
    python scripts/kayiplar/isig_sync.py codes KOD1 KOD2   # verilen gönderileri işle (geçmişe dönük tamamlama)
    python scripts/kayiplar/isig_sync.py gaps              # İSİG sıra numaralarında eksik olanları yaz
Seçenekler: --dry-run (hiçbir şey yazma), --push (uzak main'e eşitle, commit et ve gönder; Actions dışında çalıştırılırsa).

Nerede çalışır: GitHub Actions (.github/workflows/kayiplar.yml). discover saat başı (profil embed'i
son ~6 paylaşımı gösterir, İSİG günde ~8 paylaşım yapar), verify her sabah 09:00'da (İstanbul).

Kayıt alanları (data/kayiplar.json): ad, yas, il, tarih, isKolu, olay, mesem, kaynakUrl, not,
ve "isig": {no, kod, ad, yas, il, olay, mesem}. "isig", İSİG'in en son okunan halidir; bir alan
İSİG'de değişince (yaş düzeltmesi, MESEM bilgisi, ölüm nedeni) kayıttaki karşılığı da güncellenir.
Elle düzeltilmiş alanlar, İSİG o alanı değiştirmedikçe korunur.

Çıkış kodu 0 = başarılı, 1 = hata.
"""
import argparse
import difflib
import html
import json
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "kayiplar.json"
BUILD_DATA = ROOT / "scripts" / "build_data.py"
COMMIT_PATHS = ["data/kayiplar.json", "js/data.js"]
# İşlenmiş (çocuk ölümü olmayan) kodlar, aynı makinede yeniden indirilmesin. Depoya girmez.
SEEN_FILE = ROOT / ".isig_seen.json"
SEEN_MAX = 500

USERNAME = "isigmeclisi"
PROFILE_EMBED_URL = f"https://www.instagram.com/{USERNAME}/embed/"
POST_EMBED_URL = "https://www.instagram.com/p/{code}/embed/captioned/"
POST_URL = "https://www.instagram.com/p/{code}/"
HTTP_TIMEOUT = 60
REQUEST_DELAY_SEC = 1.5
CHILD_AGE_LIMIT = 18
ISTANBUL = timezone(timedelta(hours=3))
BOT_NAME = "mesemli-sync"
BOT_EMAIL = "mesemli-sync@users.noreply.github.com"

# Instagram embed'i tarayıcıdan gelmeyen isteğe giriş duvarı gösterir; başlık seti tarayıcınınki gibi olmalı.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Referer": "https://www.google.com/",
}

# Medya id'sinin üst bitleri ms cinsinden zaman damgasıdır (Instagram'ın id şeması).
ID_EPOCH_MS = 1314220021721
ID_TIMESTAMP_SHIFT = 23

CONTEXT_KEY = '"contextJSON":"'
COUNTER_RE = re.compile(r"(\d{1,3})\s*\.\s*çocuk\s+işçi\s+ölümü", re.I)
AGE_RE = re.compile(r"(?<![\d-])(\d{1,2})\s*yaş(?:ında|larında)", re.I)
AGE_RANGE_RE = re.compile(r"\d{1,2}\s*[-–]\s*\d{1,2}\s*yaş", re.I)
DEATH_RE = re.compile(r"hayatını\s+kaybetti|yaşamını\s+yitirdi|can\s+verdi|öldü|cansız\s+bedeni\s+bulundu", re.I)
# Ölüm tarihi paylaşımdan farklıysa İSİG sona "/ 24 Ekim" yazar.
DEATH_DATE_RE = re.compile(r"/\s*(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\b")
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
MESEM_RE = re.compile(r"\bMESEM\b|mesleki\s+eğitim\s+merkez", re.I)
LOCATIVE_RE = re.compile(r"^(?:\S+\s+){0,5}?\S+['’]n?(?:de|da|te|ta)\s+", re.I)
TIME_RE = re.compile(r"^\d{1,2}[.:]\d{2}\s+sularında\s+", re.I)
NAME_WORD_RE = re.compile(r"^[A-ZÇĞİÖŞÜÂÎÛ][a-zçğıöşüâîû]+$")

PROVINCES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", "Antalya", "Ardahan",
    "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu",
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne",
    "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay",
    "Iğdır", "Isparta", "İstanbul", "İzmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu",
    "Kayseri", "Kilis", "Kırıkkale", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya",
    "Manisa", "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya",
    "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli",
    "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak",
]
PROVINCE_ALIASES = {"Afyon": "Afyonkarahisar", "Maraş": "Kahramanmaraş", "Urfa": "Şanlıurfa", "Antep": "Gaziantep"}
WATCHED_FIELDS = ("ad", "yas", "il", "olay", "mesem")


class SyncError(RuntimeError):
    """Senkron akışında kurtarılamayan hata."""


class PostGone(SyncError):
    """Gönderi silinmiş ya da gizlenmiş."""


# ---------- Instagram ----------

def http_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise PostGone(url) from e
        raise SyncError(f"{url}: HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise SyncError(f"{url}: {e}") from e


def embed_context(page):
    """Embed HTML'ine gömülü JSON (kaçışlı string içinde string); kodlar düz HTML'de görünmez."""
    start = page.find(CONTEXT_KEY)
    if start < 0:
        return {}
    start += len(CONTEXT_KEY)
    i = start
    while i < len(page) and page[i] != '"':
        i += 2 if page[i] == "\\" else 1
    try:
        return json.loads(json.loads('"' + page[start:i] + '"'))
    except ValueError:
        return {}


def recent_codes():
    """Profil embed'indeki son ~6 paylaşımın kodları (yeniden eskiye).

    İSİG günde ~8 paylaşım yapar; bu yüzden bulma adımı saatte bir çalışır, 6'lık pencere yeter.
    """
    grid = (embed_context(http_get(PROFILE_EMBED_URL)).get("context") or {}).get("graphql_media") or []
    codes = list(dict.fromkeys(c for item in grid if (c := (item.get("shortcode_media") or {}).get("shortcode"))))
    if not codes:
        raise SyncError("son paylaşımlar okunamadı (giriş duvarı ya da şema değişikliği).")
    return codes


def fetch_post(code):
    """(açıklama metni, paylaşım günü YYYY-AA-GG) döner."""
    page = http_get(POST_EMBED_URL.format(code=code))
    m = re.search(r'class="Caption"(.*?)</div>', page, re.S)
    if not m:
        raise PostGone(f"{code}: açıklama yok (silinmiş ya da gizli olabilir)")
    text = html.unescape(re.sub(r"<br\s*/?>", " ", m.group(1)))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"View all( \d+)? comments?", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(rf"^>?\s*{USERNAME}\s*", "", text)
    media = re.search(r'data-media-id="(\d+)"', page)
    day = None
    if media:
        ms = (int(media.group(1)) >> ID_TIMESTAMP_SHIFT) + ID_EPOCH_MS
        day = datetime.fromtimestamp(ms / 1000, ISTANBUL).strftime("%Y-%m-%d")
    return text, day


# ---------- Ayrıştırma ----------

def find_province(text):
    best = None
    for name in PROVINCES + list(PROVINCE_ALIASES):
        m = re.search(rf"(?<![\wçğıöşü]){re.escape(name)}(?![a-zçğıöşü])", text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), PROVINCE_ALIASES.get(name, name))
    return best[1] if best else None


def clean_event(segment):
    """'Şanlıurfa Karaköprü'de 16.00 sularında çalıştığı inşaattan...' → 'Çalıştığı inşaattan...'."""
    event = segment.strip(" .")
    stripped = LOCATIVE_RE.sub("", event, count=1)
    if stripped != event and find_province(event[: len(event) - len(stripped)]):
        event = stripped
    event = TIME_RE.sub("", event)
    return tr_capitalize(event)


def tr_capitalize(text):
    """str.upper() "i"yi "I" yapar; Türkçede "İ" olmalı."""
    first = {"i": "İ", "ı": "I"}.get(text[:1], text[:1].upper())
    return first + text[1:]


def event_text(segments):
    """Olaydan ölüme kadar olan bölümler: 'yaralandı.. hastanede hayatını kaybetti' ikisi birden kalır."""
    death = next((i for i, s in enumerate(segments) if DEATH_RE.search(s)), None)
    if death is None:
        return None
    start = next((i for i, s in enumerate(segments[: death + 1]) if find_province(s)), death)
    return ". ".join(clean_event(s) for s in segments[start: death + 1])


def death_day(caption):
    """'/ 24 Ekim' → (gün, ay); yoksa None. Yıl, paylaşım tarihine göre add_or_link'te belirlenir."""
    m = DEATH_DATE_RE.search(caption)
    return (int(m.group(1)), MONTHS.index(m.group(2)) + 1) if m else None


def resolve_day(parsed, post_day):
    """Ölüm günü verilmişse onu, yoksa paylaşım gününü döndürür (YYYY-AA-GG)."""
    if not post_day or not parsed.get("olumGunu"):
        return post_day
    d, m = parsed["olumGunu"]
    year = int(post_day[:4]) - (1 if m > int(post_day[5:7]) else 0)
    try:
        return datetime(year, m, d).strftime("%Y-%m-%d")
    except ValueError:
        return post_day


def parse(caption):
    """Kalıba tam uyan bir çocuk işçi ölümü paylaşımıysa alan sözlüğü, değilse (None, neden) döner."""
    # İSİG çoğu çocuk ölümünü "Bu yıl tespit edebildiğimiz 81. çocuk işçi ölümü.." diye açar, ama
    # bazılarını her işçi ölümü gibi "Ad.. 17 yaşında.." diye paylaşır; sayaç varsa okunur, şart değil.
    counter = COUNTER_RE.search(caption)
    if not DEATH_RE.search(caption):
        return None, "ölüm ifadesi yok"

    after = caption[counter.end():] if counter else caption
    segments = [s.strip(" ,") for s in re.split(r"\.{2,}|…", after) if s.strip(" ,")]
    if len(segments) < 2:
        return None, "sayaçtan sonra isim ve yaş yok"
    # "Halil (İbrahim) Yağız" gibi parantezli ikinci adlar adın parçasıdır.
    name = re.sub(r"\s+", " ", re.sub(r"[()]", "", segments[0])).strip()
    words = name.split()
    if not (2 <= len(words) <= 5 and all(NAME_WORD_RE.match(w) for w in words)):
        return None, f"isim kalıba uymuyor: {segments[0]!r}"
    # Yaş, isimden hemen sonraki bölümden okunur; metnin devamında başka çocukların yaşları geçebilir.
    age_seg = segments[1]
    if AGE_RANGE_RE.search(age_seg):
        return None, "yaş aralık olarak verilmiş"
    ages = {int(a) for a in AGE_RE.findall(age_seg)}
    if len(ages) != 1:
        return None, f"isimden sonra tek bir yaş yok ({age_seg[:40]!r})"
    age = ages.pop()
    if age >= CHILD_AGE_LIMIT:
        return None, f"yaş {age}"

    return {
        "no": int(counter.group(1)) if counter else None,
        "olumGunu": death_day(caption),
        "ad": name,
        "yas": age,
        "il": find_province(after),
        "olay": event_text(segments[2:]),
        "mesem": bool(MESEM_RE.search(caption)),
    }, None


# ---------- Veri ----------

NAME_SIMILARITY = 0.9  # "kadir sevlilgen" ~ "kadir sevilgen" 0.97; farklı soyadlar 0.8'in altında


def norm_name(name):
    folded = (name or "").replace("İ", "i").replace("I", "ı").lower()
    folded = unicodedata.normalize("NFKD", folded.replace("ı", "i"))
    return re.sub(r"[^a-z ]", "", "".join(c for c in folded if not unicodedata.combining(c))).strip()


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def write(data):
    """Atomik yazım: yarıda kesilirse bozuk JSON kalmaz."""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=DATA.parent, suffix=".json", delete=False) as tmp:
        # Dosyanın mevcut biçimi (indent=1, sonda satır sonu yok) korunur; fark yalnızca değişen kayıt olsun.
        tmp.write(json.dumps(data, ensure_ascii=False, indent=1))
    Path(tmp.name).replace(DATA)
    subprocess.run([sys.executable, str(BUILD_DATA)], check=True, capture_output=True)


def all_records(data):
    for year in data["yillar"]:
        for rec in year["kisiler"]:
            yield year, rec


def sort_year(year):
    """Kayıplar dosyasının sırası: önce MESEM'liler, sonra diğerleri, her grupta yeniden eskiye."""
    year["kisiler"].sort(key=lambda k: (not k.get("mesem"), [-ord(c) for c in (k.get("tarih") or "")]))


def find_existing(data, parsed, code, day):
    """Aynı gönderi ya da aynı yıl içinde aynı isim (±60 gün) zaten listede mi?"""
    key = norm_name(parsed["ad"])
    year_no = int(day[:4]) if day else None
    for year, rec in all_records(data):
        isig = rec.get("isig") or {}
        if isig.get("kod") == code:
            return rec
        # İSİG aynı çocuğu düzeltilmiş metinle yeniden paylaşabiliyor; yıl içindeki sıra numarası aynı kişidir.
        if year_no and parsed["no"] is not None and year["yil"] == year_no and isig.get("no") == parsed["no"]:
            return rec
    for _, rec in all_records(data):
        if not rec.get("tarih") or not day:
            continue
        gap = abs((datetime.fromisoformat(rec["tarih"]) - datetime.fromisoformat(day)).days)
        if gap > 60:
            continue
        other = norm_name(rec.get("ad"))
        if other == key:
            return rec
        # Haberle İSİG arasında harf hatası olabiliyor ("Sevlilgen" / "Sevilgen"): yaşı tutan, adı çok
        # benzeyen kayıt da aynı kişidir.
        if (rec.get("yas") == parsed.get("yas") and parsed.get("yas") is not None
                and difflib.SequenceMatcher(None, other, key).ratio() >= NAME_SIMILARITY):
            return rec
    return None


def snapshot(parsed, code):
    return {"no": parsed["no"], "kod": code, **{f: parsed[f] for f in WATCHED_FIELDS}}


def add_or_link(data, code, parsed, day, log):
    """Yeni kaydı ekler; aynı kişi zaten varsa yalnızca İSİG bağlantısını iliştirir (elle girilmiş alanlara dokunmaz)."""
    day = resolve_day(parsed, day)
    existing = find_existing(data, parsed, code, day)
    if existing is not None:
        if (existing.get("isig") or {}).get("kod") == code:
            return False
        existing["isig"] = snapshot(parsed, code)
        log(f"  = {code} #{parsed['no'] or '-'} {parsed['ad']}: listede vardı, İSİG kaydı bağlandı")
        return True
    if not day:
        log(f"  ! {code} #{parsed['no']}: paylaşım tarihi okunamadı, eklenmedi")
        return False
    record = {
        "ad": parsed["ad"],
        "yas": parsed["yas"],
        "il": parsed["il"],
        "tarih": day,
        "isKolu": None,
        "olay": parsed["olay"],
        "mesem": parsed["mesem"],
        "kaynakUrl": POST_URL.format(code=code),
        "not": "İSİG Meclisi paylaşımından otomatik eklendi" + ("." if parsed.get("olumGunu") else "; tarih paylaşım günüdür."),
        "isig": snapshot(parsed, code),
    }
    year_no = int(day[:4])
    year = next((y for y in data["yillar"] if y["yil"] == year_no), None)
    if year is None:
        year = {"yil": year_no, "kisiler": []}
        data["yillar"].append(year)
        data["yillar"].sort(key=lambda y: -y["yil"])
    year["kisiler"].append(record)
    sort_year(year)
    log(f"  + {code} #{parsed['no'] or '-'} {parsed['ad']}, {parsed['yas']}, {parsed['il']}, {day}"
        f"{', MESEM' if parsed['mesem'] else ''}")
    return True


def process_codes(data, codes, seen, log):
    """Kodları sırayla işler; değişiklik olduysa True döner."""
    changed = False
    for i, code in enumerate(codes):
        if i:
            time.sleep(REQUEST_DELAY_SEC)
        try:
            caption, day = fetch_post(code)
        except SyncError as e:
            log(f"  ! {code}: {e}")
            continue
        parsed, reason = parse(caption)
        if parsed is None:
            if COUNTER_RE.search(caption) or any(int(a) < CHILD_AGE_LIMIT for a in AGE_RE.findall(caption)):
                # Çocuk ölümü sayacı var ama kalıp tutmadı: elle bakılmalı, sessizce geçilmez.
                log(f"  ? {code}: çocuk işçi paylaşımı ama eklenmedi ({reason}): {caption[:140]}")
            else:
                seen.add(code)
            continue
        changed |= add_or_link(data, code, parsed, day, log)
        seen.add(code)
    return changed


def verify(data, log):
    """İSİG kodu olan her kaydı yeniden okur; İSİG'de değişen alanları kayda yansıtır. Hiçbir kaydı silmez."""
    changed = False
    targets = [(y, r) for y, r in all_records(data) if (r.get("isig") or {}).get("kod")]
    log(f"doğrulanacak: {len(targets)} kayıt")
    for i, (year, rec) in enumerate(targets):
        if i:
            time.sleep(REQUEST_DELAY_SEC)
        old = rec["isig"]
        code = old["kod"]
        try:
            caption, _ = fetch_post(code)
        except PostGone as e:
            log(f"  ! {rec['ad']} ({code}): gönderiye ulaşılamadı, kayıt olduğu gibi bırakıldı: {e}")
            continue
        except SyncError as e:
            log(f"  ! {rec['ad']} ({code}): {e}")
            continue
        parsed, reason = parse(caption)
        if parsed is None:
            log(f"  ? {rec['ad']} ({code}): paylaşım artık kalıba uymuyor ({reason}); kayıt değiştirilmedi")
            continue
        diffs = [f for f in WATCHED_FIELDS if parsed[f] != old.get(f)]
        if parsed["no"] != old.get("no"):
            diffs.append("no")
        if not diffs:
            continue
        for f in diffs:
            if f in WATCHED_FIELDS and parsed[f] is not None:
                rec[f] = parsed[f]
        rec["isig"] = snapshot(parsed, code)
        sort_year(year)
        log(f"  ~ {rec['ad']} ({code}): " + ", ".join(f"{f}: {old.get(f)!r} → {parsed[f]!r}" for f in diffs))
        changed = True
    return changed


def gaps(data, year_no):
    """İSİG sıra numarası bilinen kayıtlar arasında atlanan numaralar."""
    nums = sorted({(r.get("isig") or {}).get("no") for y, r in all_records(data)
                   if y["yil"] == year_no and (r.get("isig") or {}).get("no")})
    if not nums:
        return []
    return [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)]


# ---------- git ----------

def git(*args, check=True):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise SyncError(f"git {' '.join(args)}: {(result.stderr or result.stdout).strip()}")
    return result


def sync_with_remote():
    """Yerel main'i uzaktakine eşitler; bot yerelde hiçbir şey biriktirmez."""
    git("fetch", "-q", "origin", "main")
    git("reset", "-q", "--hard", "origin/main")


def commit_and_push(message):
    git("add", *COMMIT_PATHS)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return False
    git("-c", f"user.name={BOT_NAME}", "-c", f"user.email={BOT_EMAIL}", "commit", "-q", "-m", message)
    git("push", "-q", "origin", "HEAD:refs/heads/main")
    return True


# ---------- komutlar ----------

def load_seen():
    try:
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def save_seen(seen, order):
    keep = [c for c in order if c in seen][:SEEN_MAX]
    SEEN_FILE.write_text(json.dumps(keep), encoding="utf-8")


def run(args):
    logs = []

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    if args.push:
        sync_with_remote()
    data = load()
    seen = load_seen() if args.cmd == "discover" else set()
    changed = False
    message = "chore(data): sync isig child worker deaths"

    if args.cmd == "discover":
        codes = recent_codes()
        known = {(r.get("isig") or {}).get("kod") for _, r in all_records(data)}
        todo = [c for c in codes if c not in known and c not in seen]
        log(f"son paylaşım: {len(codes)}, işlenecek: {len(todo)}")
        changed = process_codes(data, todo, seen, log)
        if not args.dry_run:
            save_seen(seen, codes + sorted(seen))
    elif args.cmd == "codes":
        changed = process_codes(data, args.codes, seen, log)
        message = "feat(data): backfill isig child worker deaths"
    elif args.cmd == "verify":
        changed = verify(data, log)
        message = "chore(data): update child worker deaths from isig"
    elif args.cmd == "gaps":
        year_no = datetime.now(ISTANBUL).year
        missing = gaps(data, year_no)
        print(f"{year_no} için eksik İSİG numaraları: {missing or 'yok'}")
        return 0

    if not changed:
        log("değişiklik yok.")
        return 0
    if args.dry_run:
        log("--dry-run: hiçbir şey yazılmadı.")
        return 0
    write(data)
    if args.push and commit_and_push(message):
        log("main'e gönderildi.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["discover", "verify", "codes", "gaps"])
    ap.add_argument("codes", nargs="*", help="codes komutu için gönderi kodları")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--push", action="store_true", help="commit et ve main'e gönder")
    args = ap.parse_args()
    if args.cmd == "codes" and not args.codes:
        ap.error("codes komutu en az bir gönderi kodu ister")
    try:
        return run(args)
    except (SyncError, subprocess.CalledProcessError) as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
