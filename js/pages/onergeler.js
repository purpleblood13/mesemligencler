/* Meclis önergeleri: her önerge, Emek Partisi'nin "SORU ÖNERGESİ" Instagram
   şablonundaki gibi kaydırmalı bir gönderi. Kapak (koyu zemin, beyaz etiket,
   kırmızı şerit, büyük cümle), sorular (açık zemin, kırmızı başlık) ve künye. */
(() => {
  "use strict";
  const mount = document.querySelector("[data-list]");
  const all = window.MG_DATA?.onergeler;
  if (!mount) return;
  const items = Array.isArray(all) ? all.filter((o) => !o.dogrulanmadi) : [];
  if (!items.length) {
    mount.innerHTML = '<p class="empty">Önerge listesi henüz derlenmedi.</p>';
    return;
  }

  const upper = (s) => String(s || "").toLocaleUpperCase("tr");
  const LABEL = {
    "Yazılı soru": "SORU ÖNERGESİ",
    "Meclis araştırması": "ARAŞTIRMA ÖNERGESİ",
    "Kanun teklifi": "KANUN TEKLİFİ",
  };
  const PARTY = {
    CHP: { short: "CHP", color: "#e30a17" },
    "DEM Parti": { short: "DEM", color: "#7b3fa0" },
    EMEP: { short: "EMEP", color: "#d7261e" },
    "DEVA Partisi": { short: "DEVA", color: "#1f6fb2" },
    "Saadet Partisi": { short: "SP", color: "#b5121b" },
    TİP: { short: "TİP", color: "#e0211d" },
  };
  const LINK_LABEL = { TBMM: "TBMM kaydını aç", Haber: "Haberini oku", "Vekil sitesi": "Açıklamayı oku" };

  const byDateDesc = (a, b) => String(b.tarih || "").localeCompare(String(a.tarih || ""));

  /** "Milli Eğitim Bakanı" -> "MİLLİ EĞİTİM BAKANINA SORDU!"; başka biçimlerde genel başlık. */
  function questionsHeading(o) {
    const m = o.muhatap || "";
    if (o.tur === "Yazılı soru" && /Bakanı$/.test(m)) return `${upper(m)}NA SORDU!`;
    return o.tur === "Meclis araştırması" ? "ARAŞTIRILMASINI İSTEDİĞİ KONULAR" : "ÖNERGEDEKİ SORULAR";
  }

  function partyMark(o, party) {
    const logo = MG.logoFor(o.parti);
    if (!logo) return "";
    return `<span class="tpl__party"><img src="${MG.esc(logo)}" alt="" width="64" height="64"><b>${MG.esc(party.short)}</b></span>`;
  }

  function coverSlide(o) {
    const party = PARTY[o.parti] || { short: (o.parti || "").slice(0, 4) };
    return `
      <section class="carousel__slide tpl tpl--cover" aria-label="Kapak">
        <span class="tpl__label">${MG.esc(LABEL[o.tur] || "MECLİS ÖNERGESİ")}</span>
        <span class="tpl__handle">mesemligencler</span>
        <div class="tpl__center">
          <span class="tpl__ribbon">${MG.esc(upper(o.vekil))}${o.parti ? ` <small>${MG.esc(upper(o.parti))}</small>` : ""}</span>
          <p class="tpl__panel">${MG.esc(o.konu)}</p>
        </div>
        ${partyMark(o, party)}
      </section>`;
  }

  function questionsSlide(o) {
    if (!Array.isArray(o.sorular) || !o.sorular.length) return "";
    return `
      <section class="carousel__slide tpl tpl--paper" aria-label="Sorular">
        <h4 class="tpl__title">${MG.esc(questionsHeading(o))}</h4>
        ${o.sorular.map((s) => `<p>${MG.esc(s)}</p>`).join("")}
        <span class="tpl__foot" aria-hidden="true"></span>
      </section>`;
  }

  function infoSlide(o) {
    const rows = [
      ["Önergeyi veren", `${o.vekil}${o.parti ? `, ${o.parti}` : ""}${o.il ? ` (${o.il})` : ""}`],
      ["Türü", o.tur],
      ["Esas no", o.esasNo],
      ["Tarih", MG.formatDate(o.tarih)],
      ["Muhatap", o.muhatap],
    ].filter(([, v]) => v);
    return `
      <section class="carousel__slide tpl tpl--paper tpl--info" aria-label="Künye">
        <h4 class="tpl__title">ÖNERGENİN KÜNYESİ</h4>
        <dl>${rows.map(([k, v]) => `<div><dt>${MG.esc(k)}</dt><dd>${MG.esc(v)}</dd></div>`).join("")}</dl>
        <span class="tpl__sign"><img src="assets/logo/profile.jpg" alt="" width="44" height="44">Mesemli Gençler</span>
      </section>`;
  }

  function renderItem(o) {
    const party = PARTY[o.parti] || { short: (o.parti || "?").slice(0, 3), color: "var(--surface-2)" };
    const url = MG.safeUrl(o.url);
    const where = [o.parti, o.il].filter(Boolean).join(", ");
    return `
      <article class="post post--motion">
        <header class="post__head">
          <span class="avatar avatar--party${MG.logoFor(o.parti) ? " avatar--logo" : ""}" style="--party:${party.color}" aria-hidden="true">${
            MG.logoFor(o.parti) ? `<img src="${MG.esc(MG.logoFor(o.parti))}" alt="" width="38" height="38">` : MG.esc(party.short)
          }</span>
          <span class="post__who"><b>${MG.esc(o.vekil)}</b><span>${MG.esc(where)}</span></span>
          ${o.tarih ? `<time class="post__time" datetime="${MG.esc(o.tarih)}">${MG.esc(MG.formatDate(o.tarih))}</time>` : ""}
        </header>
        <div class="carousel post__media post__media--tpl">
          <div class="carousel__track" tabindex="0" aria-label="${MG.esc(o.vekil)} önergesi, slaytlar">
            ${coverSlide(o)}${questionsSlide(o)}${infoSlide(o)}
          </div>
          <span class="carousel__count"></span>
          <button class="carousel__prev" type="button" aria-label="Önceki slayt"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg></button>
          <button class="carousel__next" type="button" aria-label="Sonraki slayt"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg></button>
          <div class="carousel__dots" aria-hidden="true"></div>
        </div>
        <div class="post__body">
          <p><b>${MG.esc(o.vekil)}</b> ${MG.esc(o.konu)}</p>
          ${url ? `<a class="post__more" href="${MG.esc(url)}" target="_blank" rel="noopener">${MG.esc(LINK_LABEL[o.kaynakTuru] || "Kaynağı aç")}</a>` : ""}
        </div>
      </article>`;
  }

  MG.feed({
    items: [...items].sort(byDateDesc),
    mount,
    groupOf: (o) => o.parti,
    textOf: (o) => `${o.vekil} ${o.parti} ${o.il || ""} ${o.konu} ${(o.sorular || []).join(" ")}`,
    renderItem,
    onRender: (els) => els.forEach((el) => MG.bindCarousels(el)),
    searchLabel: "Vekil adı ya da konu ara",
    noun: "önerge",
    batch: 8,
  });
})();
