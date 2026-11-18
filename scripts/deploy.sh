#!/usr/bin/env bash
#
# Siteyi voltran.space/mesemli-gencler/ adresine yayınlar (SSH + rsync).
#
# Voltran'ın web kökü başka uygulamalarla paylaşılıyor, bu yüzden:
#   - yalnızca kendi alt klasörüne (mesemli-gencler/) yazar, kökteki hiçbir dosyaya dokunmaz;
#   - --delete KULLANMAZ, sunucuda hiçbir şey silmez.
#
# Önkoşul: ~/.ssh/config içinde "voltran" takma adı (Voltran/DEPLOYMENT.md).
#
# Kullanım:
#   scripts/deploy.sh --dry-run   # neyin gideceğini göster, hiçbir şey gönderme
#   scripts/deploy.sh             # yayınla
set -euo pipefail

SSH_ALIAS="voltran"
REMOTE_DIR="domains/voltran.space/public_html/mesemli-gencler/"
LIVE_URL="https://voltran.space/mesemli-gencler/"

DRY_RUN=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    *) echo "Bilinmeyen seçenek: $arg" >&2; exit 2 ;;
  esac
done

cd "$(dirname "$0")/.."

for required in index.html css/site.css js/data.js js/common.js og.jpg css/fonts.css; do
  [[ -f "$required" ]] || { echo "HATA: $required yok, yayın durduruldu." >&2; exit 1; }
done

# Her yayında css/js adreslerinin sürüm numarasını yenile; ziyaretçilerin tarayıcısı eski dosyayı kullanmasın.
if [[ -z "$DRY_RUN" ]]; then
  VERSION="$(date +%Y%m%d%H%M)"
  sed -i '' -E "s/\?v=[0-9]+/?v=$VERSION/g" ./*.html css/site.css css/tokens.css
fi

# iletisim.php (form uç noktası) form verisinin nereye gideceğine karar verilene kadar yayınlanmaz;
# yayınlamak için aşağıdaki --exclude='iletisim.php' satırını sil.
# Yayına yalnızca sitenin kendisi gider; veri JSON'ları, betikler ve ham mektup slaytları gitmez.
rsync -avz $DRY_RUN \
  --exclude='.DS_Store' \
  --exclude='.claude/' \
  --exclude='.git/' \
  --exclude='scripts/' \
  --exclude='data/' \
  --exclude='assets/mektup/' \
  --exclude='iletisim.php' \
  "./" "$SSH_ALIAS:$REMOTE_DIR"

if [[ -z "$DRY_RUN" ]]; then
  echo "==> Yayınlandı: $LIVE_URL"
fi
