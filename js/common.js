/* Ortak davranış: mobil menü, kaydırınca header gölgesi ve küçük yardımcılar.
   Header, menü ve footer HTML'de durur (scripts/build_chrome.py yazar);
   bu dosya yüklenmese bile sayfa tam görünür, yalnızca menü düğmesi çalışmaz. */
(() => {
  "use strict";

  const MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
  const SCROLLED_PX = 24;

  /** HTML'e girecek her dış veri buradan geçer. */
  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  /** Yalnızca http(s) bağlantılarına izin verir; diğerleri boş döner. */
  function safeUrl(value) {
    try {
      const url = new URL(String(value || ""), location.href);
      return url.protocol === "http:" || url.protocol === "https:" ? url.href : "";
    } catch {
      return "";
    }
  }

  /** "2026-11-16" -> "16 Kasım 2026"; tarih yoksa boş. */
  function formatDate(iso) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!m) return "";
    return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
  }

  function bindMenu(header, menu) {
    const btn = header.querySelector(".menu-btn");
    if (!btn) return;
    const setOpen = (open) => {
      document.body.classList.toggle("menu-open", open);
      btn.setAttribute("aria-expanded", String(open));
      btn.setAttribute("aria-label", open ? "Menüyü kapat" : "Menüyü aç");
    };
    btn.addEventListener("click", () => setOpen(!document.body.classList.contains("menu-open")));
    menu?.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
  }

  function bindScrollState(header) {
    const update = () => header.classList.toggle("is-scrolled", window.scrollY > SCROLLED_PX);
    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  // Kuruluş adı -> logo anahtarı (data/logolar.json ile aynı)
  const LOGO_SLUG = {
    Evrensel: "evrensel", "Genç Hayat": "genc-hayat", BirGün: "birgun", "Artı Gerçek": "arti-gercek", Bianet: "bianet", T24: "t24",
    CHP: "chp", "DEM Parti": "dem-parti", EMEP: "emep", "DEVA Partisi": "deva", "Saadet Partisi": "saadet", TİP: "tip",
  };

  /** Gazete ya da parti adından logo dosyası; yoksa boş döner. */
  function logoFor(name) {
    const entry = window.MG_DATA?.logolar?.[LOGO_SLUG[name]];
    return entry?.dosya || "";
  }

  window.MG = { esc, safeUrl, formatDate, logoFor };

  const header = document.querySelector(".site-header");
  if (header) {
    bindMenu(header, document.getElementById("mobile-menu"));
    bindScrollState(header);
  }
})();
