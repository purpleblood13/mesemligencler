/* Haberler: haftalık başlıklarla kayan, görselli haber akışı.
   Hafta pazartesi başlar; başlık "9 – 15 Kasım 2026 arasındaki haberler" biçimindedir.
   Hafta içinde sıra: günler yeniden eskiye, aynı gün içinde önce Evrensel ve Genç Hayat, sonra diğerleri.
   Saat dikkate alınmaz. */
(() => {
  "use strict";
  const mount = document.querySelector("[data-list]");
  const items = window.MG_DATA?.haberler;
  if (!mount) return;
  if (!Array.isArray(items) || !items.length) {
    mount.innerHTML = '<p class="empty">Haber listesi henüz derlenmedi.</p>';
    return;
  }

  const SOURCE_ORDER = ["Evrensel", "Genç Hayat", "BirGün", "Artı Gerçek", "Bianet", "T24"];
  const MONOGRAM = { Evrensel: "E", "Genç Hayat": "GH", BirGün: "B", "Artı Gerçek": "A+", Bianet: "bi", T24: "24" };
  // Türkçe bulunma eki kaynağa göre değişir
  const READ_AT = { Evrensel: "Evrensel'de", "Genç Hayat": "Genç Hayat'ta", BirGün: "BirGün'de", "Artı Gerçek": "Artı Gerçek'te", Bianet: "Bianet'te", T24: "T24'te" };
  const MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
  const UNDATED = "tarihsiz";
  const WEEK_DAYS = 7;

  const sourceRank = (s) => (SOURCE_ORDER.includes(s) ? SOURCE_ORDER.indexOf(s) : SOURCE_ORDER.length);
  const dayOf = (h) => (/^\d{4}-\d{2}-\d{2}$/.test(h.tarih || "") ? h.tarih : UNDATED);

  const sorted = items
    .map((h, i) => ({ h, i }))
    .sort((a, b) => {
      const da = dayOf(a.h), db = dayOf(b.h);
      if (da !== db) return da === UNDATED ? 1 : db === UNDATED ? -1 : db.localeCompare(da);
      return sourceRank(a.h.kaynak) - sourceRank(b.h.kaynak) || a.i - b.i;
    })
    .map(({ h }) => h);

  /* ---------- Hafta hesabı ---------- */
  const parseDay = (iso) => {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d);
  };
  const isoOf = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  /** Günün ait olduğu haftanın pazartesisi (yerel saat). */
  const weekStart = (date) => {
    const d = new Date(date);
    d.setDate(d.getDate() - ((d.getDay() + 6) % WEEK_DAYS));
    return d;
  };
  const weekOf = (h) => {
    const day = dayOf(h);
    return day === UNDATED ? UNDATED : isoOf(weekStart(parseDay(day)));
  };

  /** "9 – 15 Kasım 2026", "26 Ekim – 1 Kasım 2026", "29 Aralık 2025 – 4 Ocak 2026" */
  function weekLabel(startIso) {
    const s = parseDay(startIso);
    const e = new Date(s);
    e.setDate(e.getDate() + WEEK_DAYS - 1);
    const part = (d, month, year) => `${d.getDate()}${month ? ` ${MONTHS[d.getMonth()]}` : ""}${year ? ` ${d.getFullYear()}` : ""}`;
    if (s.getFullYear() !== e.getFullYear()) return `${part(s, true, true)} – ${part(e, true, true)}`;
    if (s.getMonth() !== e.getMonth()) return `${part(s, true, false)} – ${part(e, true, true)}`;
    return `${part(s, false, false)} – ${part(e, true, true)}`;
  }

  const currentWeek = isoOf(weekStart(new Date()));

  function renderSection(key, weekItems) {
    const count = `${weekItems.length} haber`;
    if (key === UNDATED) return `<h2 class="day"><span>Tarihi belirsiz haberler</span><small>${count}</small></h2>`;
    const note = key === currentWeek ? `Bu hafta, ${count}` : count;
    return `<h2 class="day" id="hafta-${key}"><span>${MG.esc(weekLabel(key))} arasındaki haberler</span><small>${note}</small></h2>`;
  }

  /* ---------- Kart ---------- */
  function avatarHtml(source) {
    const logo = MG.logoFor(source);
    return logo
      ? `<span class="avatar avatar--logo" aria-hidden="true"><img src="${MG.esc(logo)}" alt="" width="38" height="38"></span>`
      : `<span class="avatar" aria-hidden="true">${MG.esc(MONOGRAM[source] || source.slice(0, 1))}</span>`;
  }

  function renderItem(h) {
    const url = MG.safeUrl(h.url);
    const href = url ? `href="${MG.esc(url)}" target="_blank" rel="noopener"` : "";
    const media = h.gorsel
      ? `<div class="post__media"><img src="${MG.esc(h.gorsel)}" alt="" loading="lazy" decoding="async"></div>`
      : "";
    return `
      <article class="post${h.gorsel ? "" : " post--text"}">
        <header class="post__head">
          ${avatarHtml(h.kaynak)}
          <span class="post__who"><b>${MG.esc(h.kaynak)}</b></span>
          ${h.tarih ? `<time class="post__time" datetime="${MG.esc(h.tarih)}">${MG.esc(MG.formatDate(h.tarih))}</time>` : ""}
        </header>
        ${media}
        <div class="post__body">
          <h3><a class="post__link" ${href}>${MG.esc(h.baslik)}</a></h3>
          ${h.ozet ? `<p>${MG.esc(h.ozet)}</p>` : ""}
          ${url ? `<span class="post__more" aria-hidden="true">${MG.esc(READ_AT[h.kaynak] || "Haberin tamamını")} oku</span>` : ""}
        </div>
      </article>`;
  }

  MG.feed({
    items: sorted,
    mount,
    groupOf: (h) => h.kaynak,
    groupOrder: SOURCE_ORDER,
    textOf: (h) => `${h.baslik} ${h.ozet || ""} ${h.kaynak}`,
    sectionOf: weekOf,
    renderSection,
    renderItem,
    searchLabel: "Haberlerde ara",
    noun: "haber",
  });
})();
