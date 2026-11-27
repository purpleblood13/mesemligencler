# sync

Periyodik veri botları. Hepsi `.github/workflows/veri.yml` içinde GitHub Actions'ta çalışır. Giriş, şifre ve anahtar kullanmazlar; yalnızca herkese açık sayfaları okurlar ve kendilerini `mesemligencler-bot` olarak tanıtırlar.

| Bot | Ne zaman (İstanbul) | Kaynak | Yazdığı |
|---|---|---|---|
| `tbmm.py` | her pazartesi 04:00 | TBMM yazılı soru önergesi araması ("MESEM") | `data/onergeler.json` |
| `haberler.py` | 3 günde bir 04:00 (ayın 1, 4, 7… günü) | Evrensel ve Cumhuriyet arama sayfası; Bianet, BirGün ve T24 RSS | `data/haberler.json`, `assets/news/` |
| `mektuplar.py` | 27 Kasım 2026'dan itibaren 2 haftada bir, cuma 04:00 | Genç Hayat "MESEM" dosyası (`/api/articles?label=MESEM`) | `data/mektuplar.json`, `assets/news/` |

Değişiklik varsa `publish.sh` bot adına (`mesemli-sync`) `main`'e commit atar ve Pages yayınını başlatır. Bütün veri botları, `kayiplar.yml` de dahil, aynı `veri-botlari` concurrency grubundadır. Böylece hiçbiri aynı anda `js/data.js`'i yazamaz.

## Botlar ne yapar

**Önergeler (`tbmm.py`)**
- Son 21 günün önergelerini tarar. Haftalık çalıştığı için bir iki çalıştırma kaçsa da yakalar.
- Esas numarası listede olan önerge atlanır.
- Haberden girilmiş, esas numarası olmayan bir kayıt aynı vekilin ±10 gün içindeki önergesiyse yeni kayıt açılmaz. O kayda yalnızca esas numarası eklenir.
- Kayıt alanları:
  - Konu: TBMM'nin önerge özeti.
  - Muhatap: detay sayfasından alınır.
  - Sorular: önerge PDF'inde numaralı, soru işaretiyle biten maddeler.
  - Parti: TBMM'nin milletvekili listesinden, vekil kimliğiyle okunur.
- PDF metni TBMM'de OCR'lı. Bu yüzden sorularda yazım hatası olabilir; en sık hata olan "MEŞEM" düzeltilir.

**Haberler (`haberler.py`)**
- Başlığında ya da kısa açıklamasında "MESEM" geçen, son 10 günde yayımlanmış haberleri alır.
- Başlık, açıklama, tarih ve görsel haberin kendi paylaşım etiketlerinden okunur. Haber metni kopyalanmaz.
- Görsel 800 px WebP olarak indirilir, `etiket` alanı "diğer" olur.
- **Sınır:** BirGün ve T24'ün RSS'i yalnızca son ~1 günü gösteriyor, BirGün'ün arama sayfası da JavaScript'le çalışıyor. 3 günde bir çalışınca bu iki kaynakta aradaki haberler kaçabilir. Evrensel, Cumhuriyet ve Bianet'te bu sorun yok.

**Mektuplar (`mektuplar.py`)**
- Yalnızca 27 Kasım 2026'dan (`SINCE`) sonra dosyaya eklenen yazıları alır. Mevcut mektuplara dokunmaz.
- `build_letters.py`'nin `main()`'i çağrılmaz, çünkü elle düzenlenmiş `data/mektuplar.json`'u baştan yazar.
- Aynı yazı Genç Hayat'ta iki kimlikle görünebiliyor. Bu yüzden başlık da tekilleştirme anahtarıdır.

## Elle çalıştırma

```
python scripts/sync/tbmm.py --dry-run --days 60
python scripts/sync/haberler.py --dry-run --days 14
python scripts/sync/mektuplar.py --dry-run --since 2026-11-01
```

Ya da GitHub'da Actions → "Veri botları" → Run workflow, `is` alanına `onergeler`, `haberler` ya da `mektuplar` yaz.

Gerekenler: Python 3, Pillow (görseller), pypdf (önerge PDF'leri).
