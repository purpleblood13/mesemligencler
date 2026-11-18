"""mesemligencler gönderilerini + profil fotoğrafını çeker, data/instagram.json üretir."""
import html, io, json, re, sys, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import insta_embed as ie
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MAX_PX = 1080
CODES_EXTRA = []


def fetch_bytes(url):
    req = urllib.request.Request(url, headers=ie.BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def save_cover(code, data):
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((MAX_PX, MAX_PX))
    out = ROOT / "assets/insta" / f"{code}.webp"
    img.save(out, "WEBP", quality=82)
    return f"assets/insta/{code}.webp"


def palette(img, n=6):
    q = img.convert("RGB").resize((200, 200)).quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    counts = Counter(q.getdata())
    return ["#%02x%02x%02x" % tuple(pal[i*3:i*3+3]) for i, _ in counts.most_common(n)]


def _cover_only_reel(code, node):
    # Video indirilmiyor; yt-dlp gerekmez, yalnızca kapak kullanılır.
    return {"type": "video", "url": "reel:" + code,
            "thumb": node.get("thumbnail_src") or node.get("display_url") or ""}


ie._reel_media = _cover_only_reel


def main():
    codes = ie.recent_shortcodes() + CODES_EXTRA
    posts = []
    for code in dict.fromkeys(codes):
        try:
            p = ie.fetch_post(code)
        except ie.InstaError as e:
            print("HATA", code, e); continue
        m = p["media"][0]
        src = m["thumb"] or m["url"] if m["type"] == "video" else m["url"]
        try:
            gorsel = save_cover(code, fetch_bytes(src))
        except Exception as e:
            print("GORSEL HATA", code, e); continue
        tur = "carousel" if len(p["media"]) > 1 else m["type"]
        tarih = datetime.fromtimestamp(p["taken_at"], timezone.utc).strftime("%Y-%m-%d")
        posts.append({"code": code, "tarih": tarih, "caption": p["caption"], "tur": tur,
                      "gorsel": gorsel, "url": f"https://www.instagram.com/p/{code}/"})
        print("ok", code, tarih, tur)
    posts.sort(key=lambda x: x["tarih"], reverse=True)

    page = ie._get(ie.PROFILE_URL, ie.DOCUMENT_HEADERS)
    pic = html.unescape(re.search(r'og:image" content="([^"]*)', page).group(1))
    raw = fetch_bytes(pic)
    (ROOT / "assets/logo/profile.jpg").write_bytes(raw)
    img = Image.open(io.BytesIO(raw))
    print("logo", img.size)
    out = {"kullanici": "mesemligencler", "profilFoto": "assets/logo/profile.jpg",
           "palet": palette(img), "gonderiler": posts}
    (ROOT / "data/instagram.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out["palet"], len(posts))


main()
