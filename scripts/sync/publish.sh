#!/usr/bin/env bash
# Veri botlarının ortak yayın adımı: değişen veri dosyalarını main'e commit'ler ve Pages yayınını başlatır.
# Neden ayrı: GITHUB_TOKEN ile yapılan push pages.yml'i tetiklemez; yayın elle başlatılmalı.
# Kullanım: scripts/sync/publish.sh "chore(data): ..." dosya1 dosya2 ...
set -euo pipefail
message="$1"; shift
git add -- "$@"
if git diff --cached --quiet; then
  echo "değişiklik yok"
  exit 0
fi
git -c user.name=mesemli-sync -c user.email=mesemli-sync@users.noreply.github.com commit -q -m "$message"
# Bu sırada main'e başka bir commit geldiyse üstüne al; veri dosyaları çakışırsa iş düşer, sonraki çalıştırma baştan üretir.
git pull -q --rebase origin main
git push -q origin HEAD:main
gh workflow run pages.yml --ref main
echo "main'e gönderildi, yayın başlatıldı"
