"""Instagram veri kaynağı — oturumsuz, tarayıcısız.

Eski `/api/v1/feed/user/<id>/` uç noktası kapandı: oturum olmadan artık
`{"require_login": true}` dönüyor. Yerine iki **public** kaynak kullanılıyor:

1. Profil sayfası HTML'i → son ~12 gönderinin kısa kodu (`/p/<code>/`,
   `/reel/<code>/` linkleri sunucu tarafında basılıyor).
2. `https://www.instagram.com/p/<code>/embed/captioned/` → o gönderinin tüm
   metadatası (`contextJSON` içindeki `gql_data.shortcode_media`): caption,
   medya URL'leri, video URL'i, beğeni/yorum sayısı.

İkisi de çerez/oturum istemiyor. **Ama tam tarayıcı başlık seti şart:** eksik
`sec-fetch-*` / `sec-ch-ua` başlıklarıyla Instagram giriş duvarı HTML'i
döndürüyor (HTTP 200, ama içinde gönderi yok). Başlıklar bu yüzden tek yerde
toplandı; bir gün veri gelmemeye başlarsa ilk bakılacak yer burası.

`taken_at` embed yanıtında yok; Instagram medya id'sinin üst bitlerinden
çıkarılıyor (ölçümde arşivdeki gerçek değerle ±1 sn uyumlu).
"""
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

USERNAME = "mesemligencler"
PROFILE_URL = f"https://www.instagram.com/{USERNAME}/"
PROFILE_EMBED_URL = f"https://www.instagram.com/{USERNAME}/embed/"
EMBED_URL = "https://www.instagram.com/p/{code}/embed/captioned/"
REEL_URL = "https://www.instagram.com/reel/{code}/"
HTTP_TIMEOUT = 60

# Embed bazı Reels'lerde `is_video: true` verip `video_url`'ü saklıyor (lisanslı
# müzikli olanlarda, ama bazen müziksizlerde de). Dosya adresi o zaman yt-dlp
# ile çözülür. `best[ext=mp4]` ses+görüntü birlikte tek mp4 verir (DASH'in
# ayrı video/ses parçalarını değil).
YTDLP_FORMAT = "best[ext=mp4]/best"
YTDLP_TIMEOUT_SEC = 120

# Instagram id şeması: üst bitler = bu epoch'tan (ms) beri geçen süre.
ID_EPOCH_MS = 1314220021721
ID_TIMESTAMP_SHIFT = 23
MS_PER_SEC = 1000

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
# Bu blok "gerçek Chrome" sinyali; eksiltilirse giriş duvarına düşülür.
BROWSER_HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}
DOCUMENT_HEADERS = {
    **BROWSER_HEADERS,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "upgrade-insecure-requests": "1",
}
EMBED_HEADERS = {
    **BROWSER_HEADERS,
    "Accept": "*/*",
    "Referer": PROFILE_URL,
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

SHORTCODE_RE = re.compile(r"/(?:p|reel)/([A-Za-z0-9_-]{5,15})/")
CONTEXT_KEY = '"contextJSON":"'


class InstaError(RuntimeError):
    """Instagram'dan veri alınamadı."""


def _get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as e:
        raise InstaError(f"{url} alınamadı: {e}") from e


def _codes_from_profile_page():
    """Profil sayfası HTML'indeki `/p/<code>/` linkleri (son ~12 gönderi).

    Ev/mobil IP'lerinden çalışıyor; datacenter IP'lerinde (ör. Oracle VM)
    Instagram giriş duvarı döndürüyor ve liste boş geliyor.
    """
    html = _get(PROFILE_URL, DOCUMENT_HEADERS)
    return SHORTCODE_RE.findall(html)


def _codes_from_profile_embed():
    """Profil embed sayfasındaki gönderi ızgarası (son 6 gönderi).

    Datacenter IP'lerinden de çalışıyor — asıl dayanak bu.
    """
    ctx = _extract_context(_get(PROFILE_EMBED_URL, DOCUMENT_HEADERS))
    grid = (ctx.get("context") or {}).get("graphql_media") or []
    return [
        code
        for item in grid
        if (code := (item.get("shortcode_media") or {}).get("shortcode"))
    ]


def profile_counts():
    """Profil embed'indeki takipçi ve gönderi sayısı; datacenter IP'lerinden de geliyor.

    Neden: profil HTML'i (fetch_media.profile_info) sunucudan giriş duvarına düşüyor; embed düşmüyor.
    """
    ctx = _extract_context(_get(PROFILE_EMBED_URL, DOCUMENT_HEADERS)).get("context") or {}
    counts = {"takipci": ctx.get("followers_count"), "gonderiSayisi": ctx.get("posts_count")}
    return {k: v for k, v in counts.items() if isinstance(v, int) and v > 0}


def recent_shortcodes():
    """Son gönderilerin kısa kodlarını (yeniden eskiye) döndürür.

    İki kaynak da denenir ve birleştirilir: biri engellenirse diğeri yeter.
    """
    seen, codes, errors = set(), [], []
    for source in (_codes_from_profile_embed, _codes_from_profile_page):
        try:
            found = source()
        except InstaError as e:
            errors.append(f"{source.__name__}: {e}")
            continue
        for code in found:
            if code in seen:
                continue
            seen.add(code)
            codes.append(code)

    if not codes:
        detail = " | ".join(errors) or "her iki kaynak da boş döndü"
        raise InstaError(
            f"Gönderi kodu bulunamadı — giriş duvarına düşmüş olabiliriz ({detail})."
        )
    return codes


def _extract_context(html):
    """Embed HTML'ine gömülü JSON'u çıkarır (kaçışlı string içinde string)."""
    start = html.find(CONTEXT_KEY)
    if start < 0:
        raise InstaError("embed yanıtında contextJSON yok — giriş duvarı ya da şema değişikliği.")
    start += len(CONTEXT_KEY)
    i = start
    while i < len(html):
        if html[i] == "\\":
            i += 2
            continue
        if html[i] == '"':
            break
        i += 1
    try:
        return json.loads(json.loads('"' + html[start:i] + '"'))
    except (json.JSONDecodeError, ValueError) as e:
        raise InstaError(f"contextJSON çözümlenemedi: {e}") from e


def _taken_at(media_id):
    """Medya id'sinden gönderi zamanını (unix saniye) çıkarır."""
    try:
        return ((int(media_id) >> ID_TIMESTAMP_SHIFT) + ID_EPOCH_MS) // MS_PER_SEC
    except (TypeError, ValueError):
        return 0


def _node_media(node):
    """Tek medya düğümünü {type,url,thumb} sözlüğüne indirger."""
    if node.get("is_video") and node.get("video_url"):
        return {
            "type": "video",
            "url": node["video_url"],
            "thumb": node.get("thumbnail_src") or node.get("display_url") or "",
        }
    return {"type": "image", "url": node.get("display_url") or "", "thumb": ""}


def _ytdlp_video_url(code):
    """Embed'in vermediği Reel videosunun doğrudan mp4 adresini yt-dlp ile çözer.

    Sadece adresi alır (`--get-url`), indirmeyi `download_media` yapar. Çözemezse
    `InstaError` fırlatır: çağıran gönderiyi atlar ve sonraki çalıştırmada
    tekrar dener — video kapağı yanlışlıkla "görsel" diye arşive girmesin.
    """
    command = [
        sys.executable, "-m", "yt_dlp",
        "--no-playlist", "--no-warnings",
        "-f", YTDLP_FORMAT,
        "--get-url", REEL_URL.format(code=code),
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=YTDLP_TIMEOUT_SEC, check=False
        )
    except subprocess.TimeoutExpired as e:
        raise InstaError(f"{code}: yt-dlp zaman aşımı ({YTDLP_TIMEOUT_SEC} sn).") from e
    except OSError as e:
        raise InstaError(f"{code}: yt-dlp başlatılamadı: {e}") from e

    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()[-1:] or ["bilinmeyen hata"]
        hint = " (kurulum: python3 -m pip install --user yt-dlp)" if "No module named" in result.stderr else ""
        raise InstaError(f"{code}: yt-dlp başarısız: {detail[0]}{hint}")

    urls = [line for line in result.stdout.splitlines() if line.startswith("http")]
    if not urls:
        raise InstaError(f"{code}: yt-dlp video adresi döndürmedi.")
    return urls[0]


def _reel_media(code, node):
    """`video_url`'ü olmayan tek videolu gönderi (Reel) için video kaydı."""
    return {
        "type": "video",
        "url": _ytdlp_video_url(code),
        "thumb": node.get("thumbnail_src") or node.get("display_url") or "",
    }


def fetch_post(code):
    """Bir gönderiyi arşiv şemasında döndürür.

    {code, taken_at, caption, like_count, comment_count, media[]} — doğrudan
    `sync_latest.process_post()`'a verilebilir.
    """
    ctx = _extract_context(_get(EMBED_URL.format(code=code), EMBED_HEADERS))
    node = (ctx.get("gql_data") or {}).get("shortcode_media")
    if not isinstance(node, dict):
        raise InstaError(f"{code}: shortcode_media yok — embed şeması değişmiş olabilir.")

    children = [e["node"] for e in (node.get("edge_sidecar_to_children") or {}).get("edges", [])]
    if not children and node.get("is_video") and not node.get("video_url"):
        media = [_reel_media(code, node)]
    else:
        media = [_node_media(n) for n in (children or [node])]
    caption_edges = (node.get("edge_media_to_caption") or {}).get("edges") or []

    return {
        "code": node.get("shortcode") or code,
        "taken_at": _taken_at(node.get("id")),
        "caption": (caption_edges[0]["node"]["text"] if caption_edges else ""),
        "like_count": (node.get("edge_liked_by") or {}).get("count"),
        "comment_count": (node.get("edge_media_to_comment") or {}).get("count"),
        "media": [m for m in media if m.get("url")],
    }
