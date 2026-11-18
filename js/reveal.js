/* Kaydırınca beliren öğeler. İlk ekranda görünenlere dokunulmaz (yanıp sönme olmaz); ekranın altındakiler
   gizlenir ve görüş alanına girince yumuşakça belirir. Aynı anda gelenler sırayla, kısa aralıkla çıkar.
   Sonradan eklenen öğeler (haber akışı, süzgeç sonuçları) de yakalanır. Hareketi azalt ayarı açıksa
   ya da betik çalışmazsa her şey normal görünür. */
(() => {
  "use strict";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;

  const SELECTOR = [
    ".demands li", ".toll", ".section > .wrap > h2",
    ".year", ".post", ".day", ".prose > *", ".ig-tile", ".field", ".site-footer .wrap",
  ].join(",");
  const SCALE_SELECTOR = ".ig-tile";
  const STAGGER_MS = 70;
  const MAX_DELAY_MS = 280;
  const VISIBLE_RATIO = 0.94;     // ilk ekranın bu kadarından yukarıdakiler olduğu gibi kalır
  const CLEANUP_MS = 1400;

  const seen = new WeakSet();

  const reveal = new IntersectionObserver((entries) => {
    const ready = entries
      .filter((e) => e.isIntersecting || e.boundingClientRect.top < 0)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top || a.boundingClientRect.left - b.boundingClientRect.left);
    ready.forEach((entry, i) => {
      const el = entry.target;
      reveal.unobserve(el);
      el.style.setProperty("--reveal-delay", `${Math.min(i * STAGGER_MS, MAX_DELAY_MS)}ms`);
      el.classList.add("is-in");
      // Geçiş bitince öğe eski hâline döner; sonraki hover ve geçişler etkilenmez.
      setTimeout(() => {
        el.classList.remove("reveal", "reveal--scale", "is-in");
        el.style.removeProperty("--reveal-delay");
      }, CLEANUP_MS + MAX_DELAY_MS);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

  function prepare(el) {
    if (seen.has(el)) return;
    seen.add(el);
    const rect = el.getBoundingClientRect();
    if (rect.bottom <= 0 || rect.top < window.innerHeight * VISIBLE_RATIO) return; // ekranda ya da yukarıda kaldı
    el.classList.add("reveal");
    if (el.matches(SCALE_SELECTOR)) el.classList.add("reveal--scale");
    reveal.observe(el);
  }

  function scan(root) {
    if (root.nodeType !== 1) return;
    if (root.matches(SELECTOR)) prepare(root);
    root.querySelectorAll(SELECTOR).forEach(prepare);
  }

  scan(document.body);
  new MutationObserver((mutations) => {
    for (const m of mutations) m.addedNodes.forEach(scan);
  }).observe(document.querySelector("main") || document.body, { childList: true, subtree: true });
})();
