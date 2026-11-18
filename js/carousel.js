/* Kaydırmalı slayt (Instagram carousel'i gibi). Dokunmatikte parmakla,
   masaüstünde oklarla ve klavyeyle gezilir; noktalar ve "1/3" sayacı güncellenir.

   Beklenen yapı:
     .carousel
       .carousel__track      (yatay scroll-snap kabı)
         .carousel__slide …
       button.carousel__prev / button.carousel__next   (isteğe bağlı)
       .carousel__dots                                  (isteğe bağlı, içi boş)
       .carousel__count                                 (isteğe bağlı)
   MG.carousel(root) bir kez bağlar; tekrar çağrılırsa bir şey yapmaz. */
(() => {
  "use strict";

  function currentIndex(track) {
    return Math.round(track.scrollLeft / Math.max(1, track.clientWidth));
  }

  function carousel(root) {
    if (!root || root.dataset.bound) return;
    root.dataset.bound = "1";
    const track = root.querySelector(".carousel__track");
    const total = track.children.length;
    const prev = root.querySelector(".carousel__prev");
    const next = root.querySelector(".carousel__next");
    const dots = root.querySelector(".carousel__dots");
    const counter = root.querySelector(".carousel__count");

    if (total < 2) {
      [prev, next, dots, counter].forEach((el) => el && el.remove());
      return;
    }
    if (dots) dots.innerHTML = Array.from({ length: total }, () => "<span></span>").join("");

    const go = (i) => {
      const target = Math.max(0, Math.min(total - 1, i));
      track.scrollTo({ left: target * track.clientWidth, behavior: "smooth" });
    };

    const update = () => {
      const i = currentIndex(track);
      if (dots) [...dots.children].forEach((d, n) => d.classList.toggle("is-on", n === i));
      if (counter) counter.textContent = `${i + 1}/${total}`;
      if (prev) prev.hidden = i === 0;
      if (next) next.hidden = i === total - 1;
      root.dispatchEvent(new CustomEvent("slidechange", { detail: { index: i } }));
    };

    prev?.addEventListener("click", (e) => { e.stopPropagation(); go(currentIndex(track) - 1); });
    next?.addEventListener("click", (e) => { e.stopPropagation(); go(currentIndex(track) + 1); });
    track.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault();
      e.stopPropagation();
      go(currentIndex(track) + (e.key === "ArrowRight" ? 1 : -1));
    });
    let raf = 0;
    track.addEventListener("scroll", () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(update);
    }, { passive: true });
    update();
  }

  /** Bir kapsayıcının içindeki bütün carousel'leri bağlar. */
  function bindAll(scope) {
    (scope || document).querySelectorAll(".carousel").forEach(carousel);
  }

  window.MG = { ...window.MG, carousel, bindCarousels: bindAll };
})();
