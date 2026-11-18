/* Ana sayfa: kayıp sayısını veriden hesaplayıp cümleye yerleştirir. */
(() => {
  "use strict";
  const MESEM_SINCE = 2023; // MESEM'in genişletildiği yıl
  const el = document.querySelector("[data-toll]");
  const years = window.MG_DATA?.kayiplar?.yillar;
  if (!el || !Array.isArray(years)) return;

  const count = years
    .filter((y) => y.yil >= MESEM_SINCE)
    .reduce((sum, y) => sum + y.kisiler.filter((k) => k.mesem).length, 0);
  if (!count) return;

  el.innerHTML = `${MESEM_SINCE}'ten bu yana en az <span class="n">${count}</span> MESEM'li arkadaşımız iş cinayetinde hayatını kaybetti.`;
})();
