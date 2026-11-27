"""Senkron betiklerinin ortak parçaları: HTTP, JSON okuma/yazma, Türkçe metin yardımcıları.

Neden: tbmm.py, haberler.py ve mektuplar.py aynı biçimde veri dosyası yazar ve aynı kimlikle
istek atar; bir yerde tutulsun ki dosya biçimi ve tarayıcı kimliği tutarlı kalsın.
"""
import html
import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
BUILD_DATA = ROOT / "scripts" / "build_data.py"
# Kendimizi açıkça tanıtırız; site sahipleri kimin okuduğunu görebilsin.
UA = "Mozilla/5.0 (compatible; mesemligencler-bot/1.0; +https://mesemligencler.com)"
HTTP_TIMEOUT = 60


class SyncError(RuntimeError):
    """Kaynağa ulaşılamadı ya da beklenen biçim değişti."""


def fetch(url, data=None, headers=None, opener=None, timeout=HTTP_TIMEOUT):
    """Ham baytları döndürür; hata olursa SyncError."""
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    try:
        with (opener or urllib.request.build_opener()).open(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SyncError(f"{url}: {e}") from e


def fetch_text(url, **kw):
    return fetch(url, **kw).decode("utf-8", "replace")


def strip_tags(fragment):
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", fragment, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()


def tr_lower(text):
    return text.replace("I", "ı").replace("İ", "i").lower()


def tr_title(text):
    """'ÖMER FARUK GERGERLİOĞLU' → 'Ömer Faruk Gergerlioğlu' (Türkçe İ/ı ile)."""
    def word(w):
        low = tr_lower(w)
        first = {"i": "İ", "ı": "I"}.get(low[:1], low[:1].upper())
        return first + low[1:]
    return " ".join(word(w) for w in text.split())


def tr_capitalize(text):
    first = {"i": "İ", "ı": "I"}.get(text[:1], text[:1].upper())
    return first + text[1:]


def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def write_json(name, data):
    """Atomik yazım; dosyaların mevcut biçimi (indent=1, sonda satır sonu yok) korunur."""
    path = DATA / name
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".json", delete=False) as tmp:
        tmp.write(json.dumps(data, ensure_ascii=False, indent=1))
    Path(tmp.name).replace(path)


def rebuild():
    subprocess.run([sys.executable, str(BUILD_DATA)], check=True, capture_output=True)


def norm_url(url):
    """Aynı haberin http/https, www, sorgu ve sondaki / farkları tek anahtara iner."""
    url = re.sub(r"^https?://(www\.)?", "", (url or "").strip().lower())
    return re.sub(r"[?#].*$", "", url).rstrip("/")
