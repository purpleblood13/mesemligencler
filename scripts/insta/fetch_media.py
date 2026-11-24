"""Mevcut gönderilerin tüm medyasını indirir, profil bilgisini çeker, data/instagram.json'u yeniden yazar.

Oturumsuz: public embed + profil HTML'i; embed video_url vermezse yt-dlp.
"""
import html, io, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import insta_embed as ie
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/insta"
DATA = ROOT / "data/instagram.json"
IMG_MAX, IMG_Q = 1080, 80
VID_MAX_W = 720
failed = []


def get_bytes(url):
    import urllib.request
    req = urllib.request.Request(url, headers=ie.BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save_image(data, rel):
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((IMG_MAX, IMG_MAX))
    img.save(ROOT / rel, "WEBP", quality=IMG_Q, method=6)
    return img.size


def save_video(raw_bytes, rel):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.bin"
        src.write_bytes(raw_bytes)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
            "-vf", f"scale='min({VID_MAX_W},iw)':-2",
            "-c:v", "libx264", "-crf", "26", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(ROOT / rel),
        ], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", str(ROOT / rel)],
                         capture_output=True, text=True, check=True).stdout.strip().split(",")
    return int(out[0]), int(out[1])


def resolve_post(code):
    """Embed'den medya listesi; video_url yoksa yt-dlp ile çöz (başarısızsa video_url=None)."""
    orig = ie._reel_media
    def lenient(c, node):
        try:
            return orig(c, node)
        except ie.InstaError as e:
            print("  yt-dlp:", e)
            return {"type": "video", "url": "failed:" + c,
                    "thumb": node.get("thumbnail_src") or node.get("display_url") or ""}
    ie._reel_media = lenient
    try:
        return ie.fetch_post(code)
    finally:
        ie._reel_media = orig


def build_post(old, p=None):
    """`p` (resolve_post çıktısı) verilirse embed'e ikinci kez gidilmez."""
    code = old["code"]
    p = p or resolve_post(code)
    # fetch_post url'siz medyayı eler; yt-dlp başarısızsa tek video kapakla kalır
    medya = []
    items = p["media"]
    for i, m in enumerate(items):
        webp = f"assets/insta/{code}_{i}.webp"
        if m["type"] == "image":
            w, h = save_image(get_bytes(m["url"]), webp)
            medya.append({"tur": "image", "src": webp, "poster": None, "en": w, "boy": h})
            continue
        w, h = save_image(get_bytes(m["thumb"]), webp)
        mp4 = f"assets/insta/{code}_{i}.mp4"
        try:
            if m["url"].startswith("failed:"):
                raise RuntimeError("video adresi çözülemedi (yt-dlp: giriş gerekli)")
            w, h = save_video(get_bytes(m["url"]), mp4)
            medya.append({"tur": "video", "src": mp4, "poster": webp, "en": w, "boy": h})
        except Exception as e:
            failed.append(f"{code}_{i}: {e}")
            medya.append({"tur": "image", "src": webp, "poster": None, "en": w, "boy": h})
    return {
        **old,
        "begeni": p["like_count"] if p["like_count"] is not None else None,
        "yorum": p["comment_count"] if p["comment_count"] is not None else None,
        "medya": medya,
    }


def profile_info():
    page = ie._get(ie.PROFILE_URL, ie.DOCUMENT_HEADERS)
    def grab(pat, cast=str):
        m = re.search(pat, page)
        return cast(m.group(1)) if m else None
    bio = json.loads('"' + grab(r'"biography":"((?:[^"\\]|\\.)*)"') + '"')
    ad = json.loads('"' + grab(r'"biography":"(?:[^"\\]|\\.)*","full_name":"((?:[^"\\]|\\.)*)"') + '"')
    og = html.unescape(grab(r'og:description" content="([^"]*)"'))
    posts = re.search(r"([\d.,]+K?) Posts", og).group(1)
    return {"ad": ad, "bio": bio, "gonderiSayisi": int(posts.replace(",", "")),
            "takipci": grab(r'"follower_count":(\d+)', int),
            "takip": grab(r'"following_count":(\d+)', int), "link": None}


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    posts = []
    for old in data["gonderiler"]:
        print(old["code"])
        posts.append(build_post({k: v for k, v in old.items() if k not in ("medya", "begeni", "yorum")}))
    out = {**data, "profil": profile_info(), "gonderiler": posts}
    DATA.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FAILED:", failed)


if __name__ == "__main__":
    main()
