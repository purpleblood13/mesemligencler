# Mesemli Gençler: kampanya sitesi

MESEM'de okuyan ve çalışan liselilerin haberleşme ve dayanışma ağının sitesi. Canlı adres: https://mesemligencler.com/ (GitHub Pages). Domain Hostinger'de kayıtlı; Hostinger'de hosting paketi yok, yalnızca DNS orada yönetilir.

Repo: https://github.com/purpleblood13/mesemli-gencler (herkese açık, varsayılan dal `main`). Ücretsiz GitHub hesabında Pages yalnızca herkese açık repoda çalışır; repo gizlenirse site yayından düşer.

## Yapı

Derleme aracı ve framework yok: düz HTML, CSS ve JS. Python betikleri veriyi ve ortak HTML parçalarını önceden üretir.

- `*.html`: sayfalar (index, biz-kimiz, kayiplar, mektuplar, haberler, onergeler, akis, iletisim). Her sayfanın `<body data-page="...">` değeri `js/pages/<sayfa>.js` ile eşleşir.
- `css/`: `tokens.css` (palet, yazı tipleri, ölçüler; renkler logodan türetildi), `site.css` ana stil, diğerleri bileşen başına.
- `js/common.js`: ortak yardımcılar (`esc`, `safeUrl`, `formatDate`) ve menü davranışı. `js/pages/*.js`: sayfaya özel kod.
- `data/*.json`: içeriğin kaynağı (kayıplar, önergeler, haberler, mektuplar, Instagram, logolar). `*.backup*.json` dosyaları eski kopyalar, siteye girmez.
- `assets/`: yazı tipleri (gömülü woff2), Instagram medyası, haber görselleri, logolar.
- `iletisim.html`: "Bize ulaş" sayfası. Form yok; ziyaretçiyi sosyal medya hesaplarına DM atmaya yönlendirir. Hesaplar `scripts/build_chrome.py` içindeki `SOCIAL` listesiyle aynı tutulur.
- `scripts/`: üretici betikler.
- `.github/workflows/pages.yml`: `main`'i GitHub Pages'e yayınlar.

## Üretilen dosyalar: elle düzenleme

| Dosya / bölüm | Üreten | Ne zaman çalıştır |
|---|---|---|
| `js/data.js` | `scripts/build_data.py` | `data/*.json` değişince |
| HTML içindeki `<!--header-->`, `<!--footer-->`, `<!--meta-->` blokları | `scripts/build_chrome.py` | menü, bağlantı, başlık ya da açıklama değişince |
| `data/mektuplar.json` | `scripts/build_letters.py` (ardından `build_data.py`) | yeni mektup eklenince (`LETTERS` listesine satır) |
| `data/instagram.json`, `assets/insta/` | `scripts/insta/collect.py`, `fetch_media.py` | Instagram akışını yenilerken |
| `js/logo-points.js` | `scripts/logo_points.py` | logo değişince |
| `og.jpg` | `scripts/make_og.py` | paylaşım görseli değişince |
| `css/fonts.css`, `assets/fonts/` | `scripts/fetch_fonts.py` | yazı tipi değişince (tek seferlik) |

Bu dosyaları elle değiştirme; kaynağı (JSON ya da betik) düzelt, betiği çalıştır, iki değişikliği birlikte commit et.

Bu makinede (Windows) Python komutu `python`; betiklerdeki `python3` örneklerini `python` diye çalıştır. `logo_points.py`, `make_og.py` ve Instagram betikleri Pillow ister.

## Kod kuralları

- Arayüz metinleri, yorumlar, docstring'ler ve hata mesajları Türkçe. Ziyaretçiye "sen" diye hitap edilir ("Adını ve soyadını yaz.").
- Yorumlar "neden"i anlatır; mevcut betiklerin başındaki "Neden:" açıklamaları örnek.
- Dışarıdan gelen her veri HTML'e `esc()` ile, her bağlantı `safeUrl()` ile girer.
- Site JS olmadan da okunabilmeli: header, menü ve footer HTML'de durur, JS yalnızca davranış ekler.
- Dış kaynak yükleme yok. Sunucunun CSP kuralı yalnızca aynı kökene izin veriyor; font, görsel ve betikler repoda durur.
- Renk ve ölçüleri `css/tokens.css` değişkenlerinden al, sabit renk yazma.
- `file://` altında da çalışmalı: veri `fetch()` ile değil `js/data.js` üzerinden okunur.

## Yerelde bakmak

Sayfayı doğrudan açmak yeterli. İstersen kökten statik sunucu çalıştır:

```
python -m http.server 8000
```

Site tamamen statik; sunucu tarafında çalışan kod yok. GitHub Pages PHP çalıştırmaz, bu yüzden sunucu kodu eklenmez.

## Dal, commit ve PR rutini

Bir iş = bir dal = bir PR. `main` her zaman yayınlanabilir durumda kalır ve kimse ona doğrudan pushlamaz. Her değişiklik kısa ömürlü bir daldan PR ile gelir ve squash ile birleşir. Issue açmak zorunlu değil.

Commit ve push yalnızca kullanıcı isteyince yapılır.

### Sözlük (dal ve commit ortak)

Türler: `feat` yeni özellik, `fix` hata düzeltme, `refactor` davranışı değiştirmeyen yeniden düzenleme, `style` biçim ve CSS, `docs` belgeler, `chore` bakım ve yapılandırma, `test` test ekleme.

Bu projenin alanları:

| Alan | Kapsam |
|---|---|
| `frontend` | `*.html`, `css/`, `js/` (üretilen `js/data.js` hariç), yazı tipleri ve arayüz görselleri |
| `data` | `data/*.json`, `assets/insta/`, `assets/news/`, `assets/logos/` ve bunları üreten betikler (`build_data.py`, `build_letters.py`, `scripts/insta/`) |
| `devops` | `.github/workflows/`, `.gitignore`, DNS ve repo ayarları |
| `docs` | `CLAUDE.md`, README ve diğer belgeler |

Proje büyüdükçe alan eklenebilir; eklenen alan bu tabloya yazılır.

### Dal adı

- Biçim: `tür/alan/kisa-ad`. Örnek: `feat/frontend/mektup-sayfasi`, `fix/data/haber-tarihleri`.
- Kısa ad küçük harf, tireyle ayrılmış, en fazla 4 kelime ve işin konusunu söyler (fiil değil). Boşluk, alt çizgi, büyük harf yok.
- Yasak: `feature/...`, kişi adları, `...-patch-1`, alansız adlar (`feat/buton`).
- Dal her zaman güncel `main`'den açılır:
  ```
  git switch main && git pull --ff-only && git switch -c feat/frontend/mektup-sayfasi
  ```
- Dallar saatler ya da birkaç gün yaşar, başka bir özellik dalının üstüne açılmaz. İş büyüdüyse ikiye bölünür.

### Commit

- Biçim: `tür(alan): kısa açıklama`. Örnek: `feat(frontend): add letters page with source links`. Birden fazla alan virgülle: `fix(frontend,data): fix news date format`.
- Açıklama İngilizce, emir kipinde, küçük harfle başlar, sonunda nokta yok; başlık en fazla 72 karakter. Squash sırasında GitHub sona `(#123)` ekler.
- `Update stuff`, `Frontend: ...` gibi başlıklar kabul edilmez.
- Her commit tek bir amaç taşır. PR birden fazla iş içeriyorsa her iş ayrı commit olur ve PR gövdesi commit commit anlatır.
- Gerekçe gerekiyorsa başlıktan sonra boş satır bırakıp gövdeye yaz: ne yapıldığını değil, neden yapıldığını.
- Üretilen dosyalar (`js/data.js`, HTML blokları vb.) kaynaklarıyla aynı commit'e girer.
- Commit ve PR metinlerine AI imza satırı (`Co-Authored-By: Claude ...`, "Generated with Claude Code") eklenmez.

### PR açmak

- Push: `git push -u origin <dal>`. PR her zaman `main`'i hedefler: `gh pr create --base main`.
- PR başlığı commit biçimindedir. Tek commit varsa o commit'in başlığının aynısıdır.
- Gövde bölümleri:
  - **Summary**: neyin bozuk olduğu ve ne yapıldığı, bileşen bileşen.
  - Issue varsa her biri için ayrı satır: `Closes #N`.
  - Gerekirse **Out of scope**.
  - **Test plan**: `- [ ]` kutuları. Ziyaret edilecek sayfa, yapılacak adım, beklenen sonuç ve bir regresyon kontrolü. Bu projede otomatik test yok; kutulara yerel kontrol komutları yazılır, örneğin `python scripts/build_data.py` hatasız çalışıyor, `python -m http.server 8000` ile sayfa açılıyor, tarayıcı konsolunda hata yok, mobil genişlikte menü çalışıyor.
- En az bir gözden geçiren (kendin değil) ve etiketler eklenir: `area: <alan>` ve tür. Hazır değilse taslak (draft) açılır.
- PR küçük tutulur, yaklaşık 400 satırı geçmez. Geçecekse commit'ler işe göre bölünür. Üretilen dosyalar ve medya bu sayıma girmez ama gövdede belirtilir.

### PR kapatmak

- Birleştirme koşulları: en az 1 onay (yazar kendi PR'ını onaylayamaz), Test plan kutuları işaretli, `main` ile çakışma yok. Çakışma varsa: `git fetch && git rebase origin/main`.
- Yöntem: **Squash and merge**. Squash başlığı PR başlığıdır; her PR `main`'de tek commit olur.
- Ekip çalışmasında birleştiren onaylayan kişidir, yazar değil. Gözden geçiren yoksa (tek kişilik çalışma) yazar kendi PR'ını birleştirir; onayın yerini Test plan'daki yerel kontroller alır, PR yine zorunludur.
- Birleştirme: `gh pr merge --squash --delete-branch`, ardından yerelde `git switch main && git pull --ff-only && git branch -d <dal>`.
- Terk edilen PR, nedenini açıklayan bir yorumla kapatılır ve dalı silinir. Birleşmiş bir PR'ı geri almak için GitHub'ın Revert düğmesi kullanılır (yeni PR açar).
- İş bitince commit'lenmemiş ya da pushlanmamış değişiklik kalmaz. Bitmemiş iş taslak PR olarak pushlanır.

### Repoya girmeyenler

`.env` ve her tür anahtar, form kayıtları ve kişisel veri, sanal ortamlar, derleme çıktısı, telif hakkı bize ait olmayan büyük medya. `.gitignore`'daki yollar (`assets/mektup/`, `data/instagram_katalog.json`, `.claude/`) commit'e girmez. GitHub 100 MB üstü dosyayı reddeder; bir kez commit'e giren büyük dosya geçmişten temizlenmeden pushlanamaz. Şu an en büyük dosya `assets/insta/Dfpb20ptNhg_0.mp4` (~19 MB); yeni video eklerken boyuta dikkat et.

### Repo ayarları (yapılacak)

Settings → General → Pull Requests altında yalnızca squash açık olmalı ve "Automatically delete head branches" işaretli olmalı. `main` için PR zorunlu kılan bir ruleset eklenmeli. Bu ayarları repo sahibi yapar.

Repodaki ilk commit (`feat: Mesemli Gençler kampanya sitesi ilk sürüm`) ilk içe aktarma istisnasıdır ve doğrudan `main`'e girdi. Sonraki her değişiklik PR ile gelir.

## Yayın (deploy)

Yayın otomatik: `main`'e her birleşmede `.github/workflows/pages.yml` çalışır ve siteyi GitHub Pages'e gönderir. Elle yayın yapılmaz, bir daldan yayın yapılmaz.

Sıra: PR birleşir → Actions sekmesinde "Deploy to GitHub Pages" iş akışı yeşil biter → https://mesemligencler.com/ açılıp değişiklik kontrol edilir. GitHub'da olmayan hiçbir değişiklik canlıda bulunmaz.

- İş akışı yalnızca sitenin dosyalarını kopyalar: `scripts/`, `data/`, `assets/mektup/`, `.github/` ve `*.md` yayına gitmez. Yeni bir site dışı klasör eklenirse `pages.yml`'deki hariç tutma listesine eklenir.
- css/js adreslerindeki `?v=` damgası yayında commit zamanıyla yenilenir; depodaki `?v=` değerleri önemli değil, elle değiştirilmez.
- `og.jpg` yeniden üretilecekse Pillow ve Poppins ExtraBold TTF gerekir: `python scripts/make_og.py --font <yol>`. Font depoya girmez (`scripts/fonts/` yok sayılır).
- Domain ayarları: repo Settings → Pages'te kaynak "GitHub Actions", özel domain `mesemligencler.com`, "Enforce HTTPS" açık. Hostinger DNS'inde `@` için GitHub Pages A kayıtları, `www` için `purpleblood13.github.io` CNAME kaydı var. DNS'i değiştirmeden önce kullanıcıya sorulur.
