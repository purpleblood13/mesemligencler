# insta

Akış sayfasının verisi: `data/instagram.json` (kayıtlar) ve `assets/insta/` (WebP görseller, H.264 videolar). Hepsi oturumsuz çalışır: giriş, şifre ve çerez kullanılmaz, yalnızca Instagram'ın public embed sayfaları okunur (`insta_embed.py`). Tarayıcı başlık seti olduğu gibi korunmalı, yoksa giriş duvarı gelir.

## Elle yenileme (tek seferlik)

- `collect.py`: son gönderileri ve profil fotoğrafını çeker, `data/instagram.json`'u baştan yazar.
- `fetch_media.py`: mevcut gönderilerin tüm medyasını indirir, profil bilgisini yeniler. Profil HTML'i yalnızca ev IP'sinden gelir.

## Otomatik senkron: `sync_latest.py`

Oracle VM'inde saatlik çalışır (Emek Gençliği botunun ve Genç Hayat senkronunun makinesi). Yalnızca **yeni** gönderileri ekler:

1. Klonu uzaktaki `main`'e eşitler (`fetch` + `reset --hard`); önceki çalıştırmadan kalan hiçbir şey taşınmaz.
2. Profil embed ızgarasından son 6 gönderinin kodunu okur, arşivde olmayanları bulur.
3. Her yeni gönderinin medyasını indirir, WebP/H.264'e çevirir.
4. `data/instagram.json` ve `js/data.js` (`build_data.py`) güncellenir. Akışta yalnızca en yeni 12 gönderi kalır; düşen gönderinin medyası silinir.
5. `chore(data): sync new instagram posts` commit'i `main`'e push edilir. Push, `pages.yml` iş akışını tetikler ve site kendiliğinden yenilenir. Bu sırada `main`'e başka bir commit geldiyse push reddedilir; bot güncel `main` üzerinde işi bir kez baştan yapar.

```
python3 scripts/insta/sync_latest.py --dry-run         # yeni gönderileri listele, hiçbir şey yazma
python3 scripts/insta/sync_latest.py --no-push         # yerelde üret ve commit et
python3 scripts/insta/sync_latest.py --refetch KOD     # bir gönderiyi baştan çek (beğeni sayısı, kapak vb.)
```

### VM kurulumu (bir kez, `ubuntu@VM`)

1. Paketler: `sudo apt install -y ffmpeg python3-venv git`
2. Yalnızca bu iş için bir deploy anahtarı üret:
   ```
   ssh-keygen -t ed25519 -N "" -C mesemli-sync -f ~/.ssh/mesemli_deploy
   cat ~/.ssh/mesemli_deploy.pub
   ```
   Çıkan açık anahtarı **repo sahibi** repo Settings → Deploy keys → Add deploy key ekranına, "Allow write access" işaretli olarak ekler.
3. Klonla ve anahtarı klona bağla:
   ```
   GIT_SSH_COMMAND="ssh -i ~/.ssh/mesemli_deploy -o IdentitiesOnly=yes" git clone git@github.com:<sahip>/mesemligencler.git ~/mesemli-sync
   git -C ~/mesemli-sync config core.sshCommand "ssh -i ~/.ssh/mesemli_deploy -o IdentitiesOnly=yes"
   ```
4. Python ortamı:
   ```
   cd ~/mesemli-sync && python3 -m venv .venv && .venv/bin/pip install pillow yt-dlp
   ```
5. Dene: `.venv/bin/python scripts/insta/sync_latest.py --dry-run`
6. Zamanlayıcı (systemd **user** birimi, `linger` açık olmalı):
   ```
   mkdir -p ~/.config/systemd/user
   cp scripts/insta/systemd/mesemli-insta-sync.* ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now mesemli-insta-sync.timer
   loginctl enable-linger "$USER"
   ```

Log: `journalctl --user -u mesemli-insta-sync`. Betikler klondan çalışır; güncellemek için VM'de `git pull` yeter (bot da her çalıştırmada kendisi çeker).

### Bilinmesi gerekenler

- **`main` kuralı:** `CLAUDE.md` "kimse `main`'e doğrudan pushlamaz" der. Bu bot, kayıplar botuyla birlikte iki istisnadan biridir, çünkü saatlik PR açıp onaylatmak mümkün değil. `main` için PR zorunlu kılan ruleset eklenirse deploy anahtarı ruleset'in **bypass listesine** eklenmelidir, yoksa push reddedilir. Bot kimliği `mesemli-sync` (noreply adresi), commit'lerden kolayca ayırt edilir.
- **VM sınırı:** Datacenter IP'sinden profil HTML'i boş gelir, keşif yalnızca ızgaradaki son 6 gönderiden yapılır. Bir saatte 6'dan fazla gönderi atılmazsa kayıp olmaz. Arada kalan olursa `--refetch KOD` ile (Mac'ten ya da VM'den) eklenir.
- **Reels videosu:** Embed bazı Reels'lerde video adresini vermez; `yt-dlp` çözemezse (giriş isterse) gönderi yalnızca kapakla yayına girer ve Akış'ta "Videoyu Instagram'da izle" düğmesi görünür. Sonradan Mac'ten `--refetch KOD` çalıştırılıp commit'lenirse video tamamlanır.
- **Sayılar:** Beğeni ve yorum sayısı gönderi eklendiği anda yazılır, sonradan güncellenmez. Profildeki gönderi sayısı yeni gönderi başına 1 artar; takipçi sayısı yalnızca `fetch_media.py` ile yenilenir.
- **Depolama:** Akış yalnızca en yeni 12 gönderiyi (`KEEP_POSTS`) gösterir, eskilerin medyası diskten silinir. Bu yüzden yayınlanan site küçük kalır. Silinen videolar git geçmişinde durur: hesap ayda ~20 video paylaşırsa geçmiş yılda birkaç yüz MB büyür. Sabitlenmiş eski bir gönderi, akıştaki en eskiden de eskiyse hiç indirilmez.
- Hesap adı `insta_embed.py` içindeki `USERNAME`'dir.
