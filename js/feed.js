/* Sosyal medya tarzı akış: süzgeç çipleri, arama, bölüm başlıkları (ör. gün)
   ve kaydırdıkça yüklenen kartlar. Haberler ve önergeler sayfaları kullanır.

   MG.feed({
     items, mount, groupOf, textOf, renderItem, searchLabel, noun,
     groupOrder?: string[],                  // çiplerin öncelik sırası
     sectionOf?: (item) => string,           // aynı bölümdeki kartlar tek başlık altında
     renderSection?: (key, items) => string, // bölüm başlığının HTML'i
     batch?: number,
     onRender?: (elements) => void,          // yeni kartlar eklendikten sonra
   }) */
(() => {
  "use strict";

  const ALL = "Tümü";
  const DEFAULT_BATCH = 20;
  const PRELOAD_MARGIN = "1200px 0px";
  const SEARCH_DELAY_MS = 150;

  /** Türkçe büyük/küçük harf ve aksan farkını yok sayan arama anahtarı. */
  function normalize(text) {
    return String(text || "").toLocaleLowerCase("tr").normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function groupsByCount(items, groupOf, order) {
    const counts = new Map();
    for (const item of items) {
      const g = groupOf(item);
      if (g) counts.set(g, (counts.get(g) || 0) + 1);
    }
    const rank = (g) => (order && order.includes(g) ? order.indexOf(g) : 99);
    return [...counts.keys()].sort((a, b) => rank(a) - rank(b) || counts.get(b) - counts.get(a));
  }

  function controlsHtml(groups, searchLabel) {
    const chips = groups
      .map((g) => `<button class="chip" type="button" data-group="${MG.esc(g)}" aria-pressed="${g === ALL}">${MG.esc(g)}</button>`)
      .join("");
    return `
      <div class="feed-controls" id="feed-controls">
        <input class="search" type="search" placeholder="${MG.esc(searchLabel)}" aria-label="${MG.esc(searchLabel)}">
        <div class="filters" role="group" aria-label="Süzgeç">${chips}</div>
      </div>
      <p class="count visually-hidden" aria-live="polite"></p>
      <div class="feed-list"></div>
      <div class="feed-sentinel" aria-hidden="true"></div>`;
  }

  function feed(opts) {
    const { items, mount, groupOf, textOf, renderItem, searchLabel, noun } = opts;
    const batch = opts.batch || DEFAULT_BATCH;
    const index = items.map((item) => ({ item, key: normalize(textOf(item)) }));
    const view = { group: ALL, query: "", visible: [], shown: 0, lastSection: null };

    mount.innerHTML = controlsHtml([ALL, ...groupsByCount(items, groupOf, opts.groupOrder)], searchLabel);
    const list = mount.querySelector(".feed-list");
    const count = mount.querySelector(".count");
    const sentinel = mount.querySelector(".feed-sentinel");

    const sectionItems = (key) => view.visible.filter((i) => opts.sectionOf(i) === key);

    const sectionHead = (item) => {
      if (!opts.sectionOf) return "";
      const key = opts.sectionOf(item);
      if (key === view.lastSection) return "";
      view.lastSection = key;
      return opts.renderSection(key, sectionItems(key));
    };

    const appendBatch = () => {
      const next = view.visible.slice(view.shown, view.shown + batch);
      if (!next.length) return;
      const html = next.map((item) => sectionHead(item) + renderItem(item)).join("");
      const frag = document.createRange().createContextualFragment(html);
      const added = [...frag.children];
      list.append(frag);
      view.shown += next.length;
      if (opts.onRender) opts.onRender(added);
    };

    const render = () => {
      const q = normalize(view.query.trim());
      view.visible = index
        .filter(({ item, key }) => (view.group === ALL || groupOf(item) === view.group) && (!q || key.includes(q)))
        .map(({ item }) => item);
      view.shown = 0;
      view.lastSection = null;
      list.innerHTML = "";
      count.textContent = `${view.visible.length} ${noun}`;
      if (!view.visible.length) {
        list.innerHTML = `<p class="empty">Bu aramaya uyan ${noun} yok. Süzgeci "Tümü" yapıp yeniden dene.</p>`;
        return;
      }
      appendBatch();
    };

    new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) appendBatch();
    }, { rootMargin: PRELOAD_MARGIN }).observe(sentinel);

    mount.querySelector(".filters").addEventListener("click", (e) => {
      const btn = e.target.closest(".chip");
      if (!btn) return;
      view.group = btn.dataset.group;
      mount.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", String(c === btn)));
      render();
    });

    // Dar ekranda header'daki arama düğmesi paneli açar/kapatır
    const toggle = document.querySelector(".search-btn");
    const panel = mount.querySelector(".feed-controls");
    if (toggle) {
      toggle.addEventListener("click", () => {
        const open = !panel.classList.contains("is-open");
        panel.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Aramayı kapat" : "Aramayı aç");
      });
    }

    let timer = 0;
    mount.querySelector(".search").addEventListener("input", (e) => {
      clearTimeout(timer);
      timer = setTimeout(() => { view.query = e.target.value; render(); }, SEARCH_DELAY_MS);
    });

    render();
    return list;
  }

  window.MG = { ...window.MG, feed, normalize };
})();
