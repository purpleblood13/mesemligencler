"""Mektuplar sayfasının verisini (data/mektuplar.json) üretir.

Instagram'daki mektup gönderilerinin açıklaması kaynağı söyler ("Mektup: Genç Hayat,
Sayı 528"). Mektubun metni görselden okunmaz; doğrudan yayımlandığı yerden alınır:
Genç Hayat yazıları canlı API'den (https://genchayat.net/api/articles/<id>), Bianet
hikâyesi için gönderi açıklaması ve haberin bağlantısı kullanılır.

Kullanım: python3 scripts/build_letters.py   ->   sonra python3 scripts/build_data.py
Yeni mektup eklemek için LETTERS listesine bir satır ekleyin.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "mektuplar.json")
API = "https://genchayat.net/api"
SITE = "https://genchayat.net/articles"
# Python'un varsayılan kullanıcı ajanı sitede 403 alıyor
HEADERS = {"User-Agent": "curl/8.7.1", "Accept": "application/json"}
TEXT_TYPES = {"text", "paragraph"}
HEADING_TYPE = "subheading"
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# (Instagram gönderi kodu, Genç Hayat yazı kimliği)
LETTERS = [
    ("Dfu4iIzjRUv", 8491),   # Sayı 528, OSTİM: devlet desteği kesilirken
    ("DemHAErDZzM", 8389),   # Sayı 526, OSTİM: ulaşım
    ("De4jL_JDS2a", 8422),   # Sayı 526, MESEM mezunu Efe
    ("Dd9mCd_jcfC", 8328),   # Sayı 525, OSTİM: hayalimiz kendi atölyemiz
]


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def clean(text):
    text = re.sub(r"<o:p>.*?</o:p>|<[^>]+>", "", text, flags=re.S)
    text = html.unescape(re.sub(r"\s*\n\s*", " ", text)).replace("\xa0", " ").replace("​", "")
    return re.sub(r"\s{2,}", " ", text).strip()


def body(article):
    """Yazının bloklarını paragraf ve ara başlık listesine çevirir."""
    items = []
    for block in article.get("content") or article.get("text") or []:
        bc = block.get("blockContent", {})
        kind, text = bc.get("type"), clean(bc.get("textContent", ""))
        if not text:
            continue
        if kind == HEADING_TYPE:
            items.append({"ara": text})
        elif kind in TEXT_TYPES:
            items.append(text)
    return items


def iso_date(millis):
    return datetime.datetime.fromtimestamp(int(millis) / 1000).strftime("%Y-%m-%d")


def format_tr(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS[m - 1]} {y}"


def issue_dates():
    return {int(i["number"]): i["date"] for i in get_json(f"{API}/issues") if i.get("date")}


def genchayat_letter(code, article_id, dates):
    a = get_json(f"{API}/articles/{article_id}")
    number = int(a["issueNumber"])
    issue_date = dates.get(number) or iso_date(a["createdAt"])
    title = a["title"].strip()
    who = ", ".join(x for x in [a.get("author"), a.get("place") or a.get("school")] if x)
    return {
        "id": a["slug"],
        "baslik": title,
        "yazar": who,
        "tarih": issue_date,
        "kaynakAdi": f"Genç Hayat, {number}. sayı",
        "metin": body(a),
        "instagram": f"https://www.instagram.com/p/{code}/",
        "kaynakca": [{
            "metin": f"{who}. “{title}”. Genç Hayat, {number}. sayı, {format_tr(issue_date)}.",
            "url": f"{SITE}/{a['slug']}",
        }],
    }


def bianet_story():
    """Gebze'deki Metin'in hikâyesi: gönderi açıklaması + Bianet haberi."""
    return {
        "id": "gebzeli-metin",
        "baslik": "Gebze'de berberde çalışan 16 yaşındaki Metin",
        "yazar": "Nalin Öztekin'in Bianet haberinden",
        "tarih": "2026-11-06",
        "kaynakAdi": "Bianet",
        "metin": [
            "Gebze'de 16 yaşında bir MESEM öğrencisi. Adı Metin. İki yıldır bir berber dükkânında “meslek öğreniyor”.",
            "Hafta içi her gün sabah 9'da başlıyor, gece 22.30'da çıkıyor. Müşteriye çay vermeyi unuttuğu için tokat yiyor. Eylül ve Ekim maaşları hâlâ ödenmedi, işveren bir açıklama bile yapmadı. Saç kesmeyi denemesine izin verilmiyor, günleri temizlik ve ayak işiyle geçiyor. İki yılda iş yerine yalnızca bir öğretmen uğradı. Okula gitmediği günleri soran olmadı.",
            "Metin'in yaşadıkları tek bir dükkânın, tek bir ustanın hikâyesi değil. “Eğitim” adı altında çocuk emeğini ucuz iş gücüne çeviren bir düzenin hikâyesi. Bu düzende denetim yok, okul yok, maaş bile garanti değil.",
            "Metin'in kendi sözleriyle: “Bence bu sistem değişmeli.”",
        ],
        "instagram": "https://www.instagram.com/p/DfaIelKjVDw/",
        "kaynakca": [{
            "metin": "Nalin Öztekin. “16 yaşındaki MESEM öğrencisi: 13 saat çalışıyorum, 2 aydır maaş alamıyorum”. Bianet, 6 Kasım 2026.",
            "url": "https://bianet.org/haber/16-yasindaki-mesem-ogrencisi-13-saat-calisiyorum-2-aydir-maas-alamiyorum-325158",
        }],
    }


def main():
    dates = issue_dates()
    letters = [genchayat_letter(code, aid, dates) for code, aid in LETTERS]
    letters.append(bianet_story())
    letters.sort(key=lambda l: l["tarih"], reverse=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(letters, f, ensure_ascii=False, indent=1)
    for l in letters:
        words = sum(len(p.split()) for p in l["metin"] if isinstance(p, str))
        print(f"{l['tarih']}  {l['id']}  ({words} kelime)  {l['kaynakAdi']}")
    print(len(letters), "mektup yazıldı ->", OUT)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # ağ ya da biçim hatası: sessizce geçme
        sys.exit(f"hata: {err}")
