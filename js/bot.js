/* Sohbet botu motoru. Ağaç: js/bot-tree.js (window.MG_BOT).
   Durum yalnızca seçilen yolların listesidir (trail); cevaplar, özet ve ekran bu listeden baştan
   oynatılarak kurulur. Böylece "geri", yenileme ve kaldığı yerden devam aynı kodla çalışır.
   Cevaplar yalnızca bu tarayıcı oturumunda (sessionStorage) durur, hiçbir yere gönderilmez. */
(() => {
  "use strict";
  const TREE = window.MG_BOT;
  if (!TREE || !window.MG) return;

  const STORE_KEY = "mg-bot-v1";
  const TYPING_MS = 520;
  const MAX_HOPS = 20;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const wait = (ms) => new Promise((r) => setTimeout(r, reduceMotion ? 0 : ms));

  const ICON = {
    chat: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.5a2.5 2.5 0 0 1-2.5 2.5H9l-5 4v-4H6a2.5 2.5 0 0 1-2.5-2.5v-9A2.5 2.5 0 0 1 6 4h12a2.5 2.5 0 0 1 2.5 2.5Z"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    back: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>',
    restart: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.6-5.9M4 4v4.5h4.5"/></svg>',
  };

  /* ---------- Ağaç mantığı ---------- */
  const matches = (rule, answers) =>
    Object.entries(rule).every(([key, want]) => (Array.isArray(want) ? want : [want]).includes(answers[key]));

  /** Atlanan ve yönlendiren düğümleri geçip gösterilecek düğümün adını verir. */
  function resolve(id, answers) {
    let current = id;
    for (let hop = 0; hop < MAX_HOPS; hop++) {
      const node = TREE.nodes[current];
      if (!node) throw new Error(`bot: "${current}" düğümü yok`);
      const skip = (node.skip || []).find((r) => (r.when ? matches(r.when, answers) : r.unless ? !matches(r.unless, answers) : false));
      if (skip) { current = skip.to; continue; }
      if (node.route) { current = node.route.map[answers[node.route.by]] || node.route.default; continue; }
      return current;
    }
    throw new Error("bot: yönlendirme döngüsü");
  }

  /** Yoldan cevapları, özeti, ekranda görünecek olayları ve gösterilecek sıradaki düğümü kurar. */
  function replay(trail) {
    const answers = {};
    const sums = [];
    const events = [];
    let current = resolve(TREE.start, answers);
    for (const step of trail) {
      const choice = TREE.nodes[step.node]?.choices?.[step.i];
      if (!choice || step.node !== current) break;
      events.push({ type: "node", id: current, sums: sums.slice() });
      events.push({ type: "user", text: choice.label });
      Object.assign(answers, choice.set || {});
      if (choice.sum) sums.push(choice.sum);
      if (choice.say || choice.links) events.push({ type: "reaction", say: choice.say || [], links: choice.links || [] });
      if (choice.action) return { answers, sums, events, current: null, action: choice.action };
      current = resolve(choice.next, answers);
    }
    return { answers, sums, events, current, action: null };
  }

  /* ---------- Kayıt ---------- */
  const load = () => {
    try { return JSON.parse(sessionStorage.getItem(STORE_KEY) || "[]"); } catch { return []; }
  };
  const save = (trail) => {
    try { sessionStorage.setItem(STORE_KEY, JSON.stringify(trail)); } catch { /* özel pencere: kayıt tutulmaz, bot yine çalışır */ }
  };

  /* ---------- Arayüz ---------- */
  const root = document.createElement("div");
  root.className = "bot";
  root.innerHTML = `
    <button class="bot-launch" type="button" aria-expanded="false" aria-controls="bot-panel">${ICON.chat}<span>Bizimle sohbet et</span></button>
    <section class="bot-panel" id="bot-panel" role="dialog" aria-label="Sohbet" hidden>
      <header class="bot-panel__head">
        <button class="bot-icon bot-back" type="button" aria-label="Bir önceki soruya dön">${ICON.back}</button>
        <img src="assets/logo/profile.jpg" alt="" width="36" height="36">
        <div class="bot-panel__who"><b>MESEM'li Gençler</b><small>İsimsiz sohbet</small></div>
        <button class="bot-icon bot-restart" type="button" aria-label="Sohbeti baştan başlat">${ICON.restart}</button>
        <button class="bot-icon bot-close" type="button" aria-label="Sohbeti kapat">${ICON.close}</button>
      </header>
      <div class="bot-log" role="log" aria-live="polite" tabindex="-1"></div>
      <div class="bot-choices"></div>
    </section>`;
  document.body.append(root);

  const launch = root.querySelector(".bot-launch");
  const panel = root.querySelector(".bot-panel");
  const log = root.querySelector(".bot-log");
  const choicesBox = root.querySelector(".bot-choices");
  const backBtn = root.querySelector(".bot-back");

  let trail = load();
  let busy = false;
  let started = false;

  const scrollDown = () => { log.scrollTo({ top: log.scrollHeight, behavior: reduceMotion ? "auto" : "smooth" }); };

  function addBubble(kind, html) {
    const el = document.createElement("div");
    el.className = `bot-msg bot-msg--${kind}`;
    el.innerHTML = html;
    log.append(el);
    return el;
  }
  const textBubble = (kind, text) => addBubble(kind, MG.esc(text));

  function linksHtml(links) {
    return links.map((l) => {
      const url = MG.safeUrl(l.href);
      if (!url) return "";
      const ext = l.ext ? ' target="_blank" rel="noopener"' : "";
      return `<a class="bot-link" href="${MG.esc(url)}"${ext}>${MG.esc(l.label)}</a>`;
    }).join("");
  }

  function summaryHtml(sums) {
    if (!sums.length) return "";
    return `<div class="bot-summary"><ul>${sums.map((s) => `<li>${MG.esc(s)}</li>`).join("")}</ul></div>`;
  }

  /** Bir düğümün mesajlarını (ve varsa özet ile bağlantıları) ekler. animate: yazıyor göstergesiyle. */
  async function showNode(id, sums, animate) {
    const node = TREE.nodes[id];
    for (const line of node.say || []) {
      if (animate) await typing();
      textBubble("bot", line);
      if (animate) scrollDown();
    }
    if (node.summary) addBubble("bot bot-msg--card", summaryHtml(sums) || "<p>Henüz bir cevap vermedin.</p>");
    if (node.links) addBubble("bot bot-msg--links", linksHtml(node.links));
    scrollDown();
  }

  async function typing() {
    const dots = addBubble("bot bot-msg--typing", "<span></span><span></span><span></span>");
    dots.setAttribute("aria-hidden", "true");
    scrollDown();
    await wait(TYPING_MS);
    dots.remove();
  }

  function showChoices(id) {
    const node = TREE.nodes[id];
    choicesBox.innerHTML = (node.choices || [])
      .map((c, i) => `<button class="bot-choice" type="button" data-i="${i}">${MG.esc(c.label)}</button>`).join("");
    backBtn.disabled = trail.length === 0;
    stickToBottom();
  }

  /** Seçenekler gelince mesaj alanı küçülür; son mesaj seçeneklerin altında kalmasın diye en alta kaydırılır. */
  function stickToBottom() {
    log.scrollTop = log.scrollHeight;
    requestAnimationFrame(() => { log.scrollTop = log.scrollHeight; });
  }

  let currentId = null;

  /** Yolu baştan kurar; son düğüm animate ise yazıyor göstergesiyle gelir. */
  async function render(animateLast) {
    const state = replay(trail);
    log.innerHTML = "";
    choicesBox.innerHTML = "";
    for (const ev of state.events) {
      if (ev.type === "node") await showNode(ev.id, ev.sums, false);
      else if (ev.type === "user") textBubble("user", ev.text);
      else {
        for (const line of ev.say) textBubble("bot", line);
        if (ev.links.length) addBubble("bot bot-msg--links", linksHtml(ev.links));
      }
    }
    if (state.action === "restart") { trail = []; save(trail); return render(true); }
    if (state.action === "close") { trail = trail.slice(0, -1); save(trail); closePanel(); return render(false); }
    currentId = state.current;
    await showNode(state.current, state.sums, animateLast);
    showChoices(state.current);
    scrollDown();
  }

  async function choose(i) {
    if (busy) return;
    const node = TREE.nodes[currentId];
    const choice = node.choices[i];
    if (!choice) return;
    busy = true;
    choicesBox.innerHTML = "";
    textBubble("user", choice.label);
    trail = [...trail, { node: currentId, i }];
    save(trail);
    const state = replay(trail);
    if (choice.say) for (const line of choice.say) { await typing(); textBubble("bot", line); }
    if (choice.links) addBubble("bot bot-msg--links", linksHtml(choice.links));
    if (state.action === "restart") { trail = []; save(trail); busy = false; await render(true); return focusFirstChoice(); }
    if (state.action === "close") { trail = trail.slice(0, -1); save(trail); busy = false; closePanel(); return; }
    currentId = state.current;
    await showNode(state.current, state.sums, true);
    showChoices(state.current);
    busy = false;
    focusFirstChoice();
  }

  function focusFirstChoice() {
    if (panel.contains(document.activeElement) || document.activeElement === document.body) {
      choicesBox.querySelector(".bot-choice")?.focus({ preventScroll: true });
    }
  }

  /* ---------- Açma, kapama ---------- */
  async function openPanel() {
    panel.hidden = false;
    root.classList.add("is-open");
    document.body.classList.add("bot-open");
    launch.setAttribute("aria-expanded", "true");
    if (!started) { started = true; busy = true; await render(true); busy = false; }
    log.focus({ preventScroll: true });
  }
  function closePanel() {
    panel.hidden = true;
    root.classList.remove("is-open");
    document.body.classList.remove("bot-open");
    launch.setAttribute("aria-expanded", "false");
    launch.focus({ preventScroll: true });
  }

  launch.addEventListener("click", openPanel);
  root.querySelector(".bot-close").addEventListener("click", closePanel);
  root.querySelector(".bot-restart").addEventListener("click", async () => {
    if (busy) return;
    trail = []; save(trail); busy = true; await render(true); busy = false;
  });
  backBtn.addEventListener("click", async () => {
    if (busy || !trail.length) return;
    trail = trail.slice(0, -1); save(trail); busy = true; await render(false); busy = false;
  });
  choicesBox.addEventListener("click", (e) => {
    const btn = e.target.closest(".bot-choice");
    if (btn) choose(Number(btn.dataset.i));
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) closePanel(); });
})();
