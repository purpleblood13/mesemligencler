"""Mesemli Gençler: Instagram artımlı senkron (oturumsuz, tarayıcısız).

Neden: akış elle `collect.py` + `fetch_media.py` ile yenileniyordu. Bu betik Oracle VM'inde
saatlik çalışır (Genç Hayat'ın düzeneğiyle aynı) ve yalnızca yeni gönderileri ekler.

Kaynak: `insta_embed.py` (public embed sayfaları; giriş, şifre, çerez gerekmez). Datacenter
IP'sinden profil HTML'i boş gelir; keşif yalnızca embed ızgarasından yapılır (son 6 gönderi).
Eski bir gönderiyi yenilemek için `--refetch KOD`.

Akış: depoyu güncelle → yeni kodları bul → medyayı indir, WebP/H.264'e çevir →
data/instagram.json → js/data.js → commit → push. Push, Pages iş akışını tetikler.

Kullanım:
    python3 scripts/insta/sync_latest.py              # senkronla, commit et, push'la
    python3 scripts/insta/sync_latest.py --dry-run    # yeni gönderileri listele, hiçbir şey yazma
    python3 scripts/insta/sync_latest.py --no-push    # yerelde üret ve commit et, push'lama
    python3 scripts/insta/sync_latest.py --refetch KOD1 KOD2

Çıkış kodu 0 = başarılı (yeni gönderi olmasa da), 1 = hata.
"""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fetch_media as fm  # noqa: E402
import insta_embed as ie  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data/instagram.json"
MEDIA_DIR = ROOT / "assets/insta"
BUILD_DATA = ROOT / "scripts/build_data.py"
COMMIT_PATHS = ["data/instagram.json", "js/data.js", "assets/insta"]
BOT_NAME = "mesemli-sync"
BOT_EMAIL = "mesemli-sync@users.noreply.github.com"
EMBED_DELAY_SEC = 1.0
# Akış yalnızca son gönderileri gösterir; eskilerin medyası silinir. Neden: her video 4–9 MB ve
# hesabın çoğu gönderisi video; arşiv büyürse depo ve Pages sitesi (1 GB sınır) kısa sürede dolar.
KEEP_POSTS = 12
SHORTCODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


class SyncError(RuntimeError):
    """Senkron akışında kurtarılamayan hata."""


class PushRejected(SyncError):
    """Bu sırada main'e başka bir commit geldi; iş güncel main üzerinde baştan yapılmalı."""


def git(*args, check=True):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SyncError(f"git {' '.join(args)} başarısız: {detail}")
    return result


def update_repo():
    """Elle çalıştırma (--no-push) için: elle yapılmış commit'lerin üstüne biner; çakışırsa durur."""
    if git("pull", "--rebase", "--autostash", "-q", check=False).returncode != 0:
        git("rebase", "--abort", check=False)
        raise SyncError("depo güncellenemedi (çakışma olabilir); elle bakın.")


def sync_with_remote():
    """Bot klonunu uzaktaki main'e eşitler, önceki çalıştırmadan kalan her şeyi atar.

    Neden: botun yerelde biriktirdiği bir commit main'le çakışırsa, rebase'le kurtarmaya çalışmak
    klonu kalıcı olarak takar (her saat aynı çakışma). Botun kendine ait bir işi yok; her çalıştırma
    güncel main'den baştan üretir.
    """
    git("fetch", "-q", "origin", "main")
    git("reset", "-q", "--hard", "origin/main")
    git("clean", "-fdq", "--", "assets/insta")


def taken_from_code(code):
    """Kısa koddan gönderi zamanı (unix saniye); indirmeden yaşını bilmek için."""
    media_id = 0
    for ch in code[:11]:
        media_id = media_id * 64 + SHORTCODE_ALPHABET.index(ch)
    return ie._taken_at(media_id)


def prune(posts):
    """En yeni KEEP_POSTS gönderiyi tutar; düşenlerin medyasını diskten siler."""
    kept, dropped = posts[:KEEP_POSTS], posts[KEEP_POSTS:]
    for post in dropped:
        for path in MEDIA_DIR.glob(f"{post['code']}[._]*"):
            path.unlink()
        print(f"  - {post['code']} ({post['tarih']}) akıştan çıktı", flush=True)
    return kept


def discover(known, refetch):
    wanted = list(dict.fromkeys(refetch))
    try:
        found = [c for c in ie.recent_shortcodes() if c not in known]
    except ie.InstaError:
        if not wanted:
            raise
        print("  ! keşif başarısız, yalnızca --refetch kodları işlenecek", flush=True)
        found = []
    return wanted + [c for c in found if c not in wanted]


def discard_media(code):
    """Yarım kalan yeni gönderinin dosyaları commit'e sızmasın."""
    for path in MEDIA_DIR.glob(f"{code}_*"):
        path.unlink()


def build_record(code):
    """Gönderiyi çekip medyasını indirir. (kayıt, yayın zamanı) döner; medya yoksa None."""
    post = fm.resolve_post(code)
    if not post["media"]:
        return None
    taken = post["taken_at"] or int(time.time())
    first = post["media"][0]
    base = {
        "code": code,
        "tarih": datetime.fromtimestamp(taken, timezone.utc).strftime("%Y-%m-%d"),
        "caption": post["caption"],
        "tur": "carousel" if len(post["media"]) > 1 else first["type"],
        # Izgara kapağı, ilk medyanın WebP'si (video ise kapak karesi); ayrı dosya üretilmez.
        "gorsel": f"assets/insta/{code}_0.webp",
        "url": f"https://www.instagram.com/p/{code}/",
    }
    return fm.build_post(base, post), taken


def process(code, is_new):
    try:
        return build_record(code)
    except (ie.InstaError, OSError, ValueError, subprocess.CalledProcessError) as e:
        # Okunamayan kod arşive girmez; sonraki çalıştırmada yeniden denenir.
        print(f"  ! {code} işlenemedi: {e}", flush=True)
        if is_new:
            discard_media(code)
        return None


def merge(existing, added):
    """Yeni kayıtlar aynı koddaki eskinin yerine geçer; aynı günde yeniler öne gelir."""
    replaced = {r["code"] for r in added}
    kept = [p for p in existing if p["code"] not in replaced]
    return sorted(added + kept, key=lambda p: p["tarih"], reverse=True)


def write_data(data):
    """Atomik yazım: yarıda kesilirse bozuk JSON kalmaz."""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=DATA.parent, suffix=".json", delete=False) as tmp:
        tmp.write(json.dumps(data, ensure_ascii=False, indent=2))
    Path(tmp.name).replace(DATA)


def commit_and_push(records, push):
    git("add", *COMMIT_PATHS)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        print("değişiklik yok.", flush=True)
        return
    body = "\n".join(f"- {r['code']} ({r['tarih']})" for r in records)
    git("-c", f"user.name={BOT_NAME}", "-c", f"user.email={BOT_EMAIL}",
        "commit", "-q", "-m", "chore(data): sync new instagram posts", "-m", body)
    if not push:
        print("push atlandı (--no-push).", flush=True)
        return
    if git("push", "-q", "origin", "HEAD:refs/heads/main", check=False).returncode != 0:
        raise PushRejected("push reddedildi; main'de yeni commit var.")
    print("push tamam.", flush=True)


def dry_run(codes):
    for code in codes:
        post = fm.resolve_post(code)
        print(f"  yeni: {code} ({len(post['media'])} medya) {post['caption'][:60]!r}")
        time.sleep(EMBED_DELAY_SEC)


def run(is_dry, push, refetch):
    if push and not is_dry:
        sync_with_remote()
    elif not is_dry:
        update_repo()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    known = {p["code"] for p in data["gonderiler"]}
    print(f"arşiv: {len(known)} gönderi", flush=True)
    codes = discover(known, refetch)
    if len(data["gonderiler"]) >= KEEP_POSTS:
        # Akıştaki en eskiden de eski bir gönderi (ör. sabitlenmiş) eklense bile hemen düşerdi;
        # her saat medyasını boşuna indirmemek için baştan atla. --refetch ile istenen hariç.
        oldest = min(taken_from_code(p["code"]) for p in data["gonderiler"])
        codes = [c for c in codes if c in refetch or taken_from_code(c) >= oldest]
    if not codes:
        print("yeni gönderi yok.", flush=True)
        return
    if is_dry:
        dry_run(codes)
        return

    built = []
    for i, code in enumerate(codes):
        if i:
            time.sleep(EMBED_DELAY_SEC)
        result = process(code, code not in known)
        if result:
            built.append(result)
            print(f"  + {code} ({len(result[0]['medya'])} medya)", flush=True)
    if not built:
        print("işlenebilen yeni gönderi yok.", flush=True)
        return

    records = [r for r, _ in sorted(built, key=lambda b: b[1], reverse=True)]
    added = sum(1 for r in records if r["code"] not in known)
    profil = {**data["profil"], "gonderiSayisi": data["profil"]["gonderiSayisi"] + added}
    write_data({**data, "profil": profil, "gonderiler": prune(merge(data["gonderiler"], records))})
    subprocess.run([sys.executable, str(BUILD_DATA)], check=True)
    if fm.failed:
        print("  ! videosu indirilemeyenler (yalnızca kapak yayında):", fm.failed, flush=True)
    commit_and_push(records, push)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--refetch", nargs="*", default=[])
    args = ap.parse_args()
    try:
        try:
            run(args.dry_run, not args.no_push, args.refetch)
        except PushRejected as e:
            # Bir kez, güncel main üzerinde baştan dene (run başta klonu main'e eşitler).
            print(f"  ! {e} Yeniden deneniyor.", flush=True)
            run(args.dry_run, not args.no_push, args.refetch)
    except (SyncError, ie.InstaError, subprocess.CalledProcessError) as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
