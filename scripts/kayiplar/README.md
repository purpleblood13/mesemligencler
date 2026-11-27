# kayiplar

Kayıplarımız sayfasının verisi `data/kayiplar.json`. Eski kayıtlar bircocukeksik.org'dan elle derlendi. Yeni kayıtları `isig_sync.py` İSİG Meclisi'nin Instagram hesabından (@isigmeclisi) ekler.

## Nasıl çalışır

İSİG her çocuk işçi ölümünü aynı kalıpla paylaşır:

> Bu yıl tespit edebildiğimiz 81. çocuk işçi ölümü.. Ahmet Baytemur.. 16 yaşında.. … Şanlıurfa Karaköprü'de çalıştığı inşaatın 3.katından düşerek hayatını kaybetti..

Betik bu kalıbı okur ve yalnızca şu koşulların hepsi tutarsa kayıt ekler:

- Sayaç ("81. çocuk işçi ölümü") var.
- Tek bir yaş var ve 18'den küçük. "15-16 yaşlarında" gibi aralıklar eklenmez.
- İsim 2–5 büyük harfle başlayan kelimeden oluşuyor.
- Metinde ölüm ifadesi var.

Kalıba uymayan çocuk paylaşımı eklenmez, logda `?` ile görünür. MESEM işareti yalnızca metinde "MESEM" ya da "Mesleki Eğitim Merkezi" geçerse konur. Tarih, paylaşımın yapıldığı gündür.

Aynı kişi listede zaten varsa (aynı isim, ±60 gün) yeni kayıt açılmaz. Mevcut kayda yalnızca `isig` bağlantısı eklenir, elle girilmiş alanlara dokunulmaz.

Giriş, şifre ve çerez kullanılmaz. Yalnızca Instagram'ın herkese açık embed sayfaları okunur.

## Zamanlama: `.github/workflows/kayiplar.yml`

- **Saat başı:** `discover`, profilin son ~6 paylaşımına bakar ve yeni çocuk ölümlerini ekler. İSİG günde ~8 paylaşım yaptığı için saatlik bakmak hiçbir paylaşımı kaçırmamak için yeterli.
- **Her sabah 09:00 (İstanbul):**
  - `verify`, `isig` kodu olan her kaydı yeniden okur. İSİG'de ad, yaş, il, ölüm nedeni ya da MESEM bilgisi değiştiyse kaydı günceller. Gönderi silinmişse kayıt silinmez, logda görünür.
  - `gaps`, sıra numarasında atlanan çocukları bulur ve "Kayıplar: İSİG sırasında eksik çocuk işçi kaydı" adlı bir issue açar ya da günceller.
- Değişiklik varsa bot (`mesemli-sync`) `main`'e commit atar ve Pages yayınını başlatır.

## Elle kullanım

```
python scripts/kayiplar/isig_sync.py discover --dry-run   # yeni paylaşımları göster, yazma
python scripts/kayiplar/isig_sync.py codes KOD1 KOD2      # belirli gönderileri ekle (geçmişe dönük tamamlama)
python scripts/kayiplar/isig_sync.py verify --dry-run     # değişen kayıtları göster
python scripts/kayiplar/isig_sync.py gaps                 # eksik sıra numaraları
```

Gönderi kodu, adresteki `instagram.com/p/KOD/` kısmıdır. Elle eklenen veri bir PR ile gelir.

## `isig` alanı

`{no, kod, ad, yas, il, olay, mesem}`: İSİG paylaşımının en son okunan hali. Doğrulama bu kopyayla karşılaştırır. Bir alanı elle düzeltirsen, İSİG o alanı değiştirmedikçe senin düzeltmen kalır.
