/* Kayıplarımız: iş cinayetinde hayatını kaybeden çocuklar, yıl yıl.
   MESEM'liler büyük, aynı yıl ölen diğer çocuk işçiler küçük yazılır.
   İsme tıklayınca yaş, il, tarih, olay ve kaynak açılır. */
(() => {
  "use strict";
  const mount = document.querySelector("[data-years]");
  const years = window.MG_DATA?.kayiplar?.yillar;
  if (!mount) return;
  if (!Array.isArray(years) || !years.length) {
    mount.innerHTML = '<p class="empty">Kayıt listesi henüz derlenmedi.</p>';
    return;
  }

  const UNKNOWN = "ismi bilinmiyor";
  const people = [];

  const isUnknown = (ad) => !ad || ad.toLocaleLowerCase("tr") === UNKNOWN;
  const displayName = (k) => (isUnknown(k.ad) ? "Adı bilinmeyen bir çocuk" : k.ad);

  const nameButton = (k) => {
    const id = people.push(k) - 1;
    const mark = k.mesem ? '<span class="name__mesem" aria-label="MESEM öğrencisi"></span>' : "";
    return `<li><button class="name" type="button" data-id="${id}" aria-expanded="false">${mark}${MG.esc(displayName(k))}</button></li>`;
  };

  const detail = (k) => {
    const facts = [k.yas ? `<b>${MG.esc(k.yas)} yaşında</b>` : "", MG.esc(k.il || ""), MG.esc(MG.formatDate(k.tarih))].filter(Boolean).join(", ");
    const url = MG.safeUrl(k.kaynakUrl);
    const olay = k.olay ? ` ${MG.esc(k.olay)}${/[.!?]$/.test(k.olay) ? "" : "."}` : "";
    const mesem = k.mesem ? " MESEM öğrencisiydi." : "";
    return `${facts}.${mesem}${olay}${url ? `<br><a href="${MG.esc(url)}" target="_blank" rel="noopener">Kaynak</a>` : ""}`;
  };

  const byDateDesc = (a, b) => String(b.tarih || "").localeCompare(String(a.tarih || ""));

  const yearBlock = (y) => {
    const children = [...y.kisiler].sort(byDateDesc);
    const mesemCount = children.filter((k) => k.mesem).length;
    const counts = [`<span>${children.length} çocuk işçi</span>`];
    if (mesemCount) counts.push(`<span>${mesemCount} MESEM öğrencisi</span>`);
    return `
      <section class="year" aria-labelledby="y${y.yil}">
        <div><h2 id="y${y.yil}">${MG.esc(y.yil)}</h2><p class="year__count">${counts.join("")}</p></div>
        <ul class="names">${children.map(nameButton).join("")}</ul>
      </section>`;
  };

  mount.innerHTML = [...years].sort((a, b) => b.yil - a.yil).map(yearBlock).join("");

  mount.addEventListener("click", (e) => {
    const btn = e.target.closest(".name");
    if (!btn) return;
    const li = btn.parentElement;
    const open = btn.getAttribute("aria-expanded") === "true";
    mount.querySelectorAll(".name-detail").forEach((d) => d.remove());
    mount.querySelectorAll('.name[aria-expanded="true"]').forEach((b) => b.setAttribute("aria-expanded", "false"));
    if (open) return;
    const box = document.createElement("li");
    box.className = "name-detail";
    box.innerHTML = detail(people[Number(btn.dataset.id)]);
    li.after(box);
    btn.setAttribute("aria-expanded", "true");
  });
})();
