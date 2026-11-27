"""Header, mobil menü ve footer'ı her sayfanın HTML'ine yazar.

Neden: bunlar JavaScript ile eklenince betik çalışmayan yerde (statik önizleme,
arama motoru, JS kapalı tarayıcı) sayfa başsız ve ayaksız görünüyordu. Artık
HTML'de duruyorlar; js/common.js yalnızca menü düğmesini ve kaydırma gölgesini bağlar.

Kullanım: python3 scripts/build_chrome.py   (menü ya da bağlantı değişince yeniden çalıştır)
Sayfalar <!--header-->...<!--/header--> ve <!--footer-->...<!--/footer--> işaretleri arasını kullanır;
işaret yoksa body açılışından hemen sonra ve </main>'den hemen sonra eklenir.
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "biz-kimiz.html", "kayiplar.html", "mektuplar.html", "haberler.html", "onergeler.html", "akis.html", "iletisim.html"]

NAV = [
    ("biz-kimiz.html", "Biz Kimiz?", "biz-kimiz"),
    ("kayiplar.html", "Kayıplarımız", "kayiplar"),
    ("mektuplar.html", "Mektuplarımız", "mektuplar"),
    ("haberler.html", "Haberler", "haberler"),
    ("onergeler.html", "Meclis Önergeleri", "onergeler"),
    ("akis.html", "Instagram Akışı", "akis"),
]

SOCIAL = [
    ("Instagram", "https://www.instagram.com/mesemligencler/", "instagram"),
    ("TikTok", "https://www.tiktok.com/@mesemligencler", "tiktok"),
    ("YouTube", "https://www.youtube.com/@MESEMliGencler2024", "youtube"),
    ("X", "https://x.com/mesemligencler", "x"),
]

ICONS = {
    "instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>',
    "tiktok": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.6 3c.4 2.2 1.8 3.7 4 4v3.1c-1.5 0-2.9-.4-4-1.1v6.3a5.7 5.7 0 1 1-5.7-5.7c.3 0 .6 0 .9.1v3.2a2.6 2.6 0 1 0 1.8 2.4V3h3Z"/></svg>',
    "youtube": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2C2 8.8 2 12 2 12s0 3.2.4 4.8a2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8c.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8ZM10 15V9l5.2 3L10 15Z"/></svg>',
    "x": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.8 3h3.1l-6.8 7.7L22 21h-6.2l-4.9-6.3L5.3 21H2.2l7.3-8.3L2 3h6.4l4.4 5.8L17.8 3Zm-1.1 16.2h1.7L7.4 4.7H5.6l11.1 14.5Z"/></svg>',
}

SITE_URL = "https://mesemligencler.com/"
OG_IMAGE_ALT = "MESEM'li Gençler: MESEM çocuk işçiliğidir."
HOME_HREF = "./"  # ana sayfa: adres çubuğunda index.html görünmesin

BRAND = f'<a class="brand" href="{HOME_HREF}"><img src="assets/logo/profile.jpg" alt="" width="38" height="38">MESEM\'li Gençler</a>'
CURRENT_ATTR = ' aria-current="page"'


def social_links():
    items = []
    for label, href, icon in SOCIAL:
        if not href:
            continue  # adresi verilmemiş hesap (TikTok) canlı sitede ölü bağlantı olmasın
        attrs = f'href="{html.escape(href)}" target="_blank" rel="noopener"'
        items.append(f"<a {attrs}>{ICONS[icon]}<span>{label}</span></a>")
    return "".join(items)


def nav_links(current):
    return "".join(
        f'<a href="{href}"{CURRENT_ATTR if page == current else ""}>{label}</a>'
        for href, label, page in NAV
    )


SEARCH_PAGES = {"haberler", "onergeler"}
SEARCH_BUTTON = (
    '<button class="search-btn" type="button" aria-expanded="false" aria-controls="feed-controls" aria-label="Aramayı aç">'
    '<svg class="search-btn__find" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg>'
    '<svg class="search-btn__close" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
    "</button>"
)


def header_html(current):
    home_attr = CURRENT_ATTR if current == "home" else ""
    search = SEARCH_BUTTON if current in SEARCH_PAGES else ""
    cta_attr = CURRENT_ATTR if current == "iletisim" else ""
    return f"""<!--header-->
  <header class="site-header">
    <div class="wrap site-header__inner">
      {BRAND}
      <nav class="nav" aria-label="Ana menü">{nav_links(current)}</nav>
      <div class="header-actions">
        <a class="nav-cta" href="iletisim.html"{cta_attr}>Bize ulaş</a>
        {search}
        <button class="menu-btn" type="button" aria-expanded="false" aria-controls="mobile-menu" aria-label="Menüyü aç"><span></span><span></span><span></span></button>
      </div>
    </div>
  </header>
  <div class="mobile-menu" id="mobile-menu">
    <nav aria-label="Mobil menü"><a href="{HOME_HREF}"{home_attr}>Talepler</a>{nav_links(current)}</nav>
    <a class="mobile-menu__cta" href="iletisim.html"{cta_attr}>Bize ulaş</a>
    <div class="social">{social_links()}</div>
  </div>
  <!--/header-->"""


def footer_html():
    return f"""<!--footer-->
  <footer class="site-footer">
    <div class="wrap">
      <div class="site-footer__top">
        <div class="site-footer__brand">
          {BRAND}
          <p>MESEM'de okuyan ve çalışan liselilerin haberleşme ve dayanışma ağı.</p>
        </div>
        <div class="social">{social_links()}</div>
      </div>
    </div>
  </footer>
  <!--/footer-->"""


def meta_html(page, title, description):
    """Paylaşım (Open Graph / Twitter) etiketleri ve kanonik adres; adresler mutlak."""
    url = SITE_URL if page == "index.html" else SITE_URL + page
    attr = lambda value: html.escape(value, quote=True)
    return f"""<!--meta-->
  <link rel="canonical" href="{attr(url)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="tr_TR">
  <meta property="og:site_name" content="MESEM'li Gençler">
  <meta property="og:title" content="{attr(title)}">
  <meta property="og:description" content="{attr(description)}">
  <meta property="og:url" content="{attr(url)}">
  <meta property="og:image" content="{SITE_URL}og.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{attr(OG_IMAGE_ALT)}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="css/bot.css?v=5">
  <!--/meta-->"""


def replace_or_insert(text, name, block, anchor_pattern, after=True):
    marked = re.compile(rf"<!--{name}-->.*?<!--/{name}-->", re.S)
    if marked.search(text):
        return marked.sub(lambda _: block, text, count=1)
    match = re.search(anchor_pattern, text)
    if not match:
        sys.exit(f"hata: {name} için yer bulunamadı")
    pos = match.end() if after else match.start()
    return text[:pos] + "\n  " + block + "\n" + text[pos:]


def bot_html():
    """Sohbet botu betikleri: ağaç (içerik) ve motor. Düğmeyi motor sayfaya ekler."""
    return """<!--bot-->
  <script src="js/reveal.js?v=5"></script>
  <script src="js/bot-tree.js?v=5"></script>
  <script src="js/bot.js?v=5"></script>
  <!--/bot-->"""


def build(page):
    path = os.path.join(ROOT, page)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    found = re.search(r'<body[^>]*data-page="([^"]+)"', text)
    if not found:
        sys.exit(f"hata: {page} body etiketinde data-page yok")
    title = re.search(r"<title>(.*?)</title>", text, re.S).group(1).strip()
    description = re.search(r'<meta name="description" content="([^"]*)"', text).group(1)
    text = replace_or_insert(text, "meta", meta_html(page, html.unescape(title), html.unescape(description)), r"</head>", after=False)
    text = replace_or_insert(text, "header", header_html(found.group(1)), r"<body[^>]*>")
    text = replace_or_insert(text, "footer", footer_html(), r"</main>")
    text = replace_or_insert(text, "bot", bot_html(), r"</body>", after=False)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("güncellendi:", page)


if __name__ == "__main__":
    for name in PAGES:
        build(name)
