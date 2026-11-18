/* Mektuplarımız: haber akışı gibi kayan kartlar. Her kart, mektubun yayımlandığı sitedeki
   görselle gelir; "Mektubun tamamını oku" ile metin ve kaynakça açılır.
   Veri: data/mektuplar.json -> window.MG_DATA.mektuplar (scripts/build_data.py, gorsel alanını ekler).
   Mektup: {id, baslik, tarih, kaynakAdi, gorsel, metin: [paragraf], instagram, kaynakca: [{metin, url}]} */
(() => {
  "use strict";
  const mount = document.querySelector("[data-letters]");
  const letters = window.MG_DATA?.mektuplar;
  if (!mount) return;
  if (!Array.isArray(letters) || !letters.length) {
    mount.innerHTML = '<p class="empty">Mektuplar henüz derlenmedi.</p>';
    return;
  }

  const EXCERPT_MIN = 120;
  const EXCERPT_MAX = 230;
  // Türkçe bulunma eki kaynağa göre değişir
  const READ_AT = { "Genç Hayat": "Genç Hayat'ta", Bianet: "Bianet'te", Evrensel: "Evrensel'de", BirGün: "BirGün'de", "Artı Gerçek": "Artı Gerçek'te", T24: "T24'te" };
  const INSTAGRAM = /instagram\.com/;

  const byDateDesc = (a, b) => String(b.tarih || "").localeCompare(String(a.tarih || ""));
  const sourceName = (l) => String(l.kaynakAdi || "").split(",")[0].replace(/ haberi$/, "").trim();
  const sourceDetail = (l) => {
    const rest = String(l.kaynakAdi || "").split(",").slice(1).join(",").trim();
    return rest || (/haberi$/.test(l.kaynakAdi || "") ? "Haber" : "");
  };

  /** İlk paragraf(lar)dan, kelime ortasında kesmeden kısa bir özet. */
  function excerpt(paragraphs) {
    let text = "";
    for (const p of paragraphs || []) {
      text += (text ? " " : "") + p;
      if (text.length >= EXCERPT_MIN) break;
    }
    return text.length <= EXCERPT_MAX ? text : text.slice(0, EXCERPT_MAX).replace(/\s+\S*$/, "") + "…";
  }

  function avatarHtml(source) {
    const logo = MG.logoFor(source);
    return logo
      ? `<span class="avatar avatar--logo" aria-hidden="true"><img src="${MG.esc(logo)}" alt="" width="38" height="38"></span>`
      : `<span class="avatar" aria-hidden="true">${MG.esc(source.slice(0, 1))}</span>`;
  }

  function sourcesHtml(l) {
    const list = Array.isArray(l.kaynakca) ? l.kaynakca.slice() : [];
    const insta = MG.safeUrl(l.instagram);
    if (insta) list.push({ metin: `Mesemli Gençler Instagram hesabı, ${MG.formatDate(l.tarih)} tarihli gönderi.`, url: insta });
    if (!list.length) return "";
    const items = list.map((s) => {
      const url = MG.safeUrl(s.url);
      return `<li>${MG.esc(s.metin)}${url ? ` <a href="${MG.esc(url)}" target="_blank" rel="noopener">${MG.esc(url)}</a>` : ""}</li>`;
    }).join("");
    return `<footer class="letter__sources"><h4>Kaynakça</h4><ol>${items}</ol></footer>`;
  }

  function letterHtml(l) {
    const source = sourceName(l);
    const detail = sourceDetail(l);
    const original = (l.kaynakca || []).map((k) => MG.safeUrl(k.url)).find((u) => u && !INSTAGRAM.test(u));
    const media = l.gorsel
      ? `<div class="post__media"><img src="${MG.esc(l.gorsel)}" alt="" loading="lazy" decoding="async"></div>`
      : "";
    return `
      <article class="post letter${l.gorsel ? "" : " post--text"}" id="${MG.esc(l.id)}">
        <header class="post__head">
          ${avatarHtml(source)}
          <span class="post__who"><b>${MG.esc(source)}</b>${detail ? `<span>${MG.esc(detail)}</span>` : ""}</span>
          ${l.tarih ? `<time class="post__time" datetime="${MG.esc(l.tarih)}">${MG.esc(MG.formatDate(l.tarih))}</time>` : ""}
        </header>
        ${media}
        <div class="post__body">
          <h3>${MG.esc(l.baslik)}</h3>
          <p class="letter__excerpt">${MG.esc(excerpt(l.metin))}</p>
          <div class="letter__full" id="tam-${MG.esc(l.id)}" hidden>
            <div class="letter__body">${(l.metin || []).map((p) => `<p>${MG.esc(p)}</p>`).join("")}</div>
            ${sourcesHtml(l)}
          </div>
          <div class="letter__actions">
            <button class="letter__toggle" type="button" aria-expanded="false" aria-controls="tam-${MG.esc(l.id)}">Mektubun tamamını oku</button>
            ${original ? `<a class="letter__orig" href="${MG.esc(original)}" target="_blank" rel="noopener">${MG.esc(READ_AT[source] || "Asıl yazıyı")} oku</a>` : ""}
          </div>
        </div>
      </article>`;
  }

  mount.innerHTML = [...letters].sort(byDateDesc).map(letterHtml).join("");

  mount.addEventListener("click", (e) => {
    const btn = e.target.closest(".letter__toggle");
    if (!btn) return;
    const card = btn.closest(".letter");
    const open = btn.getAttribute("aria-expanded") !== "true";
    card.querySelector(".letter__full").hidden = !open;
    card.classList.toggle("is-open", open);
    btn.setAttribute("aria-expanded", String(open));
    btn.textContent = open ? "Kapat" : "Mektubun tamamını oku";
    if (!open) card.scrollIntoView({ block: "nearest" });
  });
})();
