/* Akış: Instagram profilinin kopyası. Profil başlığı + ızgara; bir kareye
   tıklayınca gönderi penceresi açılır (masaüstünde medya + açıklama paneli,
   oklarla gönderiler arası geçiş; mobilde tam ekran, alt alta kayan akış). */
(() => {
  "use strict";
  const mount = document.querySelector("[data-ig]");
  const data = window.MG_DATA?.instagram;
  const posts = data?.gonderiler;
  if (!mount) return;
  if (!Array.isArray(posts) || !posts.length) {
    mount.innerHTML = '<p class="empty">Gönderiler henüz çekilmedi.</p>';
    return;
  }

  const USER = data.kullanici || "mesemligencler";
  const PROFILE_URL = `https://www.instagram.com/${USER}/`;
  const AVATAR = data.profilFoto || "assets/logo/profile.jpg";
  const MOBILE = window.matchMedia("(max-width: 760px)");
  const MIN_RATIO = 4 / 5;
  const MAX_RATIO = 1.91;

  const ICON = {
    carousel: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19 15V5a3 3 0 0 0-3-3H6a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3Zm2-8.9V15a5 5 0 0 1-5 5H7.1A3 3 0 0 0 10 22h7a5 5 0 0 0 5-5v-7a3 3 0 0 0-1-2.9Z"/></svg>',
    reel: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm4.5 5.2v7.6c0 .5.5.8.9.5l6-3.8a.6.6 0 0 0 0-1l-6-3.8c-.4-.3-.9 0-.9.5Z"/></svg>',
    heart: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.8 3.5c2.8 0 5 2.3 5 5.3 0 4.8-6.6 9.7-9.3 11.6a.9.9 0 0 1-1 0C8.8 18.5 2.2 13.6 2.2 8.8c0-3 2.2-5.3 5-5.3 2 0 3.6 1.1 4.8 3 1.2-1.9 2.8-3 4.8-3Z"/></svg>',
    comment: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.7 16.4A9.5 9.5 0 1 0 17 20.3l4.3 1.3-1.3-4.3a1 1 0 0 1 .7-.9Z"/></svg>',
    dots: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="1.7"/><circle cx="12" cy="12" r="1.7"/><circle cx="19" cy="12" r="1.7"/></svg>',
    grid: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><rect x="3" y="3" width="18" height="18"/><path d="M9 3v18M15 3v18M3 9h18M3 15h18"/></svg>',
    close: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"/></svg>',
    left: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>',
    right: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>',
    like: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><path d="M16.8 3.5c2.8 0 5 2.3 5 5.3 0 4.8-6.6 9.7-9.3 11.6a.9.9 0 0 1-1 0C8.8 18.5 2.2 13.6 2.2 8.8c0-3 2.2-5.3 5-5.3 2 0 3.6 1.1 4.8 3 1.2-1.9 2.8-3 4.8-3Z"/></svg>',
    talk: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><path d="M20.7 16.4A9.5 9.5 0 1 0 17 20.3l4.3 1.3-1.3-4.3"/></svg>',
    send: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><path d="M22 3 9.2 10.1M22 3l-7 18-3.7-8.4L3 9.6 22 3Z"/></svg>',
    save: '<svg viewBox="0 0 24 24" class="ig-icon" aria-hidden="true"><path d="M19 21 12 15.8 5 21V3h14v18Z"/></svg>',
  };

  const num = (n) => Number(n || 0).toLocaleString("tr-TR");
  /** Instagram'ın kısaltması: 52.302 -> "52,3 B", 1.250.000 -> "1,2 Mn". */
  const short = (n) => {
    if (n >= 1e6) return `${(n / 1e6).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} Mn`;
    if (n >= 1e4) return `${(n / 1e3).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} B`;
    return num(n);
  };
  const isVideoPost = (p) => p.tur === "video" || p.tur === "clips";
  const mediaOf = (p) => (Array.isArray(p.medya) && p.medya.length ? p.medya : [{ tur: "image", src: p.gorsel }]);

  /** Açıklamayı güvenli HTML'e çevirir; @kullanıcı ve #etiket bağlantı olur. */
  function captionHtml(text) {
    return MG.esc(text).replace(/(^|[\s(])([@#])([\p{L}\p{N}_.]+)/gu, (m, pre, sign, word) => {
      const href = sign === "@" ? `https://www.instagram.com/${word}/` : `https://www.instagram.com/explore/tags/${encodeURIComponent(word)}/`;
      return `${pre}<a href="${href}" target="_blank" rel="noopener">${sign}${word}</a>`;
    });
  }

  /* ---------- Profil + ızgara ---------- */
  function profileHtml() {
    const p = data.profil || {};
    return `
      <header class="ig-profile">
        <div class="ig-avatar"><img src="${MG.esc(AVATAR)}" alt="${MG.esc(USER)} profil fotoğrafı" width="150" height="150"></div>
        <div class="ig-info">
          <div class="ig-row">
            <h2 class="ig-user">${MG.esc(USER)}</h2>
            <a class="ig-dots" href="${PROFILE_URL}" target="_blank" rel="noopener" aria-label="Instagram'da aç">${ICON.dots}</a>
          </div>
          <ul class="ig-stats">
            <li><b>${num(p.gonderiSayisi || posts.length)}</b> gönderi</li>
            <li><b>${short(p.takipci)}</b> takipçi</li>
            <li><b>${num(p.takip)}</b> takip</li>
          </ul>
          <div class="ig-bio"><b>${MG.esc(p.ad || "Mesemli Gençler")}</b>${p.bio ? `<span>${MG.esc(p.bio)}</span>` : ""}</div>
        </div>
      </header>
      <nav class="ig-tabs" aria-label="Profil sekmeleri"><span class="ig-tab">${ICON.grid}GÖNDERİLER</span></nav>`;
  }

  function tileHtml(p, i) {
    const type = p.tur === "carousel" ? ICON.carousel : isVideoPost(p) ? ICON.reel : "";
    const first = (p.caption || "").split("\n").find((l) => l.trim()) || "Gönderi";
    return `
      <button class="ig-tile" type="button" data-index="${i}" aria-label="${MG.esc(first)}">
        <img src="${MG.esc(p.gorsel)}" alt="" loading="lazy" decoding="async">
        ${type ? `<span class="ig-tile__type">${type}</span>` : ""}
        <span class="ig-tile__hover" aria-hidden="true">
          <span>${ICON.heart}${short(p.begeni)}</span><span>${ICON.comment}${short(p.yorum)}</span>
        </span>
      </button>`;
  }

  /* ---------- Gönderi ---------- */
  function slideHtml(m, p) {
    if (m.tur === "video" && m.src) {
      return `<div class="carousel__slide"><video src="${MG.esc(m.src)}"${m.poster ? ` poster="${MG.esc(m.poster)}"` : ""} controls playsinline loop muted preload="metadata"></video></div>`;
    }
    return `<div class="carousel__slide"><img src="${MG.esc(m.src)}" alt="" loading="lazy" decoding="async"></div>`;
  }

  function ratioOf(p) {
    const m = mediaOf(p)[0];
    if (!m.en || !m.boy) return MIN_RATIO;
    return Math.min(MAX_RATIO, Math.max(MIN_RATIO, m.en / m.boy));
  }

  function postHtml(p, i) {
    const media = mediaOf(p);
    // Videosu indirilemeyen Reels'te kapak gösterilir, izlemek için Instagram'a bağlanır
    const missingVideo = isVideoPost(p) && !media.some((m) => m.tur === "video");
    const watch = missingVideo ? `<a class="ig-btn ig-watch" href="${MG.esc(p.url)}" target="_blank" rel="noopener">Videoyu Instagram'da izle</a>` : "";
    return `
      <article class="ig-post" data-index="${i}" style="--ratio:${ratioOf(p)}" aria-label="Gönderi ${i + 1}">
        <div class="ig-post__media carousel">
          <div class="carousel__track" tabindex="0">${media.map((m) => slideHtml(m, p)).join("")}</div>
          ${watch}
          <span class="carousel__count"></span>
          <button class="carousel__prev" type="button" aria-label="Önceki">${ICON.left}</button>
          <button class="carousel__next" type="button" aria-label="Sonraki">${ICON.right}</button>
          <div class="carousel__dots" aria-hidden="true"></div>
        </div>
        <div class="ig-post__side">
          <div class="ig-head"><img src="${MG.esc(AVATAR)}" alt=""><b>${MG.esc(USER)}</b></div>
          <div class="ig-cap">
            <img src="${MG.esc(AVATAR)}" alt="">
            <div><p><b>${MG.esc(USER)}</b> ${captionHtml(p.caption || "")}</p><time datetime="${MG.esc(p.tarih)}">${MG.esc(MG.formatDate(p.tarih))}</time></div>
          </div>
          <div class="ig-actions">
            <div class="ig-actions__row" aria-hidden="true">${ICON.like}${ICON.talk}${ICON.send}<span class="ig-save">${ICON.save}</span></div>
            <div class="ig-likes">${num(p.begeni)} beğenme</div>
            <div class="ig-date">${MG.esc(MG.formatDate(p.tarih))}</div>
            <a class="ig-open" href="${MG.esc(p.url)}" target="_blank" rel="noopener">Instagram'da aç</a>
          </div>
        </div>
      </article>`;
  }

  /* ---------- Pencere ---------- */
  mount.innerHTML = `
    ${profileHtml()}
    <div class="ig-grid">${posts.map(tileHtml).join("")}</div>
    <p class="ig-more"><a class="ig-btn ig-btn--ghost" href="${PROFILE_URL}" target="_blank" rel="noopener">Tüm gönderileri Instagram'da gör</a></p>
    <dialog class="ig-modal" aria-label="Gönderi">
      <div class="ig-modal__bar">Gönderiler</div>
      <button class="ig-close" type="button" aria-label="Kapat">${ICON.close}</button>
      <button class="ig-nav ig-nav--prev" type="button" aria-label="Önceki gönderi">${ICON.left}</button>
      <button class="ig-nav ig-nav--next" type="button" aria-label="Sonraki gönderi">${ICON.right}</button>
      <div class="ig-stage"></div>
    </dialog>`;

  const dialog = mount.querySelector(".ig-modal");
  const stage = dialog.querySelector(".ig-stage");
  const prevBtn = dialog.querySelector(".ig-nav--prev");
  const nextBtn = dialog.querySelector(".ig-nav--next");
  let active = 0;
  let built = false;

  const pauseAll = () => stage.querySelectorAll("video").forEach((v) => v.pause());
  const playIn = (el) => { const v = el?.querySelector("video"); if (v) v.play().catch(() => {}); };

  function build() {
    if (built) return;
    stage.innerHTML = posts.map(postHtml).join("");
    MG.bindCarousels(stage);
    // Mobilde ekrana gelen gönderinin videosu oynar, çıkan durur
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (!MOBILE.matches) return;
      const v = e.target.querySelector("video");
      if (!v) return;
      if (e.isIntersecting) v.play().catch(() => {}); else v.pause();
    }), { root: stage, threshold: 0.6 });
    stage.querySelectorAll(".ig-post").forEach((el) => io.observe(el));
    built = true;
  }

  function show(i) {
    active = Math.max(0, Math.min(posts.length - 1, i));
    pauseAll();
    stage.querySelectorAll(".ig-post").forEach((el, n) => el.classList.toggle("is-active", n === active));
    prevBtn.hidden = active === 0;
    nextBtn.hidden = active === posts.length - 1;
    const el = stage.children[active];
    if (MOBILE.matches) el.scrollIntoView({ block: "start" });
    else playIn(el);
  }

  function open(i) {
    build();
    dialog.showModal();
    document.body.style.overflow = "hidden";
    show(i);
  }

  dialog.addEventListener("close", () => { pauseAll(); document.body.style.overflow = ""; });
  dialog.querySelector(".ig-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  prevBtn.addEventListener("click", () => show(active - 1));
  nextBtn.addEventListener("click", () => show(active + 1));
  dialog.addEventListener("keydown", (e) => {
    if (MOBILE.matches || e.target.closest(".carousel__track")) return;
    if (e.key === "ArrowRight") show(active + 1);
    if (e.key === "ArrowLeft") show(active - 1);
  });
  mount.querySelector(".ig-grid").addEventListener("click", (e) => {
    const tile = e.target.closest(".ig-tile");
    if (tile) open(Number(tile.dataset.index));
  });
})();
