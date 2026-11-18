/* Mesemli Gençler — logo ağ animasyonu.
   Sahne: noktalar sol alttan bir akıntıyla gelir ve logoyu kurar (haberleşme
   ve dayanışma ağı). Kurulduktan sonra bazı noktalar haberci olur: ekranın
   öbür ucuna gidip logoya iplik çekerek döner. Sayfa kaydırılınca logo sağ
   üste doğru çözülerek akar. Veri: window.MG_LOGO (js/logo-points.js). */
(() => {
  "use strict";

  const PALETTE = ["#ef5a43", "#c2402f", "#f3e9e4", "#ff9a5c"];
  const LINK_ALPHA = [0.55, 0.5, 0.22, 0.6];
  const BG = "#1a1514";
  const MAX_DPR = 2;
  const INTRO_MIN_MS = 1500;
  const INTRO_SPREAD_MS = 1600;
  const INTRO_TAIL_MS = 1400;
  const MESSENGER_SHARE = 0.018;
  const MESSENGER_FIRST_MS = [600, 9000]; // ilk yolculuklar yayılsın, hepsi aynı anda çıkmasın
  const MESSENGER_TRIP_MS = [2600, 4200];
  const MESSENGER_REST_MS = [3000, 12000];
  const MOUSE_RADIUS = 120;
  const MOUSE_PUSH = 26;
  const MOBILE_BREAK = 760;
  const NARROW_BREAK = 1180;
  const GRID_KEY = 100000;

  const canvas = document.querySelector("[data-network]");
  if (!canvas || !window.MG_LOGO) return;
  const ctx = canvas.getContext("2d");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const rand = (a, b) => a + Math.random() * (b - a);
  const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const clamp01 = (t) => Math.max(0, Math.min(1, t));
  const bezier = (p0, p1, p2, p3, t) => {
    const u = 1 - t;
    return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3;
  };

  const state = {
    w: 0, h: 0, dpr: 1, size: 0, cx: 0, cy: 0, linkDist: 0, radius: 1.5,
    start: 0, scroll: 0, mouse: { x: -9999, y: -9999 }, running: false, visible: true,
    particles: [],
  };

  /* ---------- Yerleşim ---------- */
  function layout() {
    const rect = canvas.getBoundingClientRect();
    state.w = rect.width;
    state.h = rect.height;
    state.dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
    canvas.width = Math.round(state.w * state.dpr);
    canvas.height = Math.round(state.h * state.dpr);
    ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);

    const isMobile = state.w < MOBILE_BREAK;
    const isNarrow = !isMobile && state.w < NARROW_BREAK;
    if (isMobile) {
      state.size = Math.min(state.w * 0.86, state.h * 0.46);
      state.cx = state.w * 0.5;
      state.cy = state.h * 0.32;
    } else if (isNarrow) {
      // Orta genişlikte logo başlığın üstüne binmesin diye yukarı-sağa çekilir
      state.size = Math.min(state.h * 0.56, state.w * 0.46);
      state.cx = state.w * 0.7;
      state.cy = state.h * 0.36;
    } else {
      state.size = Math.min(state.h * 0.8, state.w * 0.4);
      state.cx = state.w * 0.74;
      state.cy = state.h * 0.48;
    }
    // Kısa bağlantı: yalnızca komşu noktalar birleşir, logo biçimi okunur kalır
    state.linkDist = state.size * 0.026;
    state.radius = Math.max(0.9, (state.size / 150) * 0.42);

    state.particles.forEach(placeHome);
  }

  function placeHome(p) {
    p.hx = state.cx + (p.nx - 0.5) * state.size;
    p.hy = state.cy + (p.ny - 0.5) * state.size;
    // Akıntı yolu: sol alttan başlar, ekranın altını yalayıp logoya kıvrılır
    p.sx = -state.w * rand(0.05, 0.35);
    p.sy = state.h * rand(0.85, 1.25);
    p.c1x = state.w * rand(0.05, 0.4);
    p.c1y = state.h * rand(0.75, 1.05);
    p.c2x = p.hx - state.size * rand(0.4, 0.9);
    p.c2y = p.hy + state.size * rand(-0.1, 0.5);
    // Kaydırınca çözülme yönü: sağ üst, hafif yelpaze
    const angle = -0.75 + rand(-0.45, 0.35);
    const dist = rand(0.5, 1.6) * Math.max(state.w, state.h);
    p.ex = Math.cos(angle) * dist;
    p.ey = Math.sin(angle) * dist;
  }

  function buildParticles() {
    state.particles = window.MG_LOGO.points.map(([nx, ny, ci], id) => {
      const p = {
        id, nx, ny, ci, x: 0, y: 0, px: 0, py: 0, alpha: 0,
        delay: rand(0, INTRO_SPREAD_MS) + nx * 400,
        dur: INTRO_MIN_MS + rand(0, 900),
        phase: rand(0, Math.PI * 2),
        wobble: rand(8, 40),
        messenger: Math.random() < MESSENGER_SHARE,
        trip: null,
        nextTrip: 0,
      };
      placeHome(p);
      p.x = p.px = p.sx;
      p.y = p.py = p.sy;
      return p;
    });
  }

  /* ---------- Haberciler ---------- */
  function startTrip(p, now) {
    const toLeft = Math.random() < 0.6;
    p.trip = {
      t0: now,
      dur: rand(MESSENGER_TRIP_MS[0], MESSENGER_TRIP_MS[1]),
      tx: (toLeft ? rand(0.02, 0.35) : rand(0.1, 0.95)) * state.w,
      ty: (toLeft ? rand(0.08, 0.9) : rand(-0.05, 0.15)) * state.h,
      bend: rand(-0.35, 0.35) * state.size,
    };
  }

  function tripOffset(p, now) {
    const t = clamp01((now - p.trip.t0) / p.trip.dur);
    if (t >= 1) {
      p.trip = null;
      p.nextTrip = now + rand(MESSENGER_REST_MS[0], MESSENGER_REST_MS[1]);
      return null;
    }
    const out = Math.sin(t * Math.PI);            // git ve dön
    const k = easeInOut(out);
    const dx = (p.trip.tx - p.hx) * k;
    const dy = (p.trip.ty - p.hy) * k;
    const len = Math.hypot(dx, dy) || 1;
    const arc = Math.sin(out * Math.PI) * p.trip.bend;
    return { x: dx + (-dy / len) * arc, y: dy + (dx / len) * arc };
  }

  /* ---------- Konum hesabı ---------- */
  function introPosition(p, elapsed) {
    const t = clamp01((elapsed - p.delay) / p.dur);
    if (t <= 0) return { x: p.sx, y: p.sy, alpha: 0 };
    const e = easeInOut(t);
    const sway = Math.sin(e * Math.PI * 3 + p.phase) * p.wobble * (1 - e);
    return {
      x: bezier(p.sx, p.c1x, p.c2x, p.hx, e) + sway * 0.4,
      y: bezier(p.sy, p.c1y, p.c2y, p.hy, e) + sway,
      alpha: Math.min(1, t * 3),
    };
  }

  function settledPosition(p, now) {
    let x = p.hx + Math.sin(now * 0.0012 + p.phase) * state.radius * 0.9;
    let y = p.hy + Math.cos(now * 0.001 + p.phase) * state.radius * 0.9;
    if (p.messenger) {
      if (!p.nextTrip) p.nextTrip = now + rand(MESSENGER_FIRST_MS[0], MESSENGER_FIRST_MS[1]);
      if (!p.trip && now > p.nextTrip) startTrip(p, now);
      const off = p.trip ? tripOffset(p, now) : null;
      if (off) { x += off.x; y += off.y; }
    }
    const s = Math.pow(state.scroll, 1.4);
    x += p.ex * s + Math.sin(s * 6 + p.phase) * 30 * s;
    y += p.ey * s;
    return { x, y, alpha: 1 - clamp01(state.scroll * 1.1 - 0.2) };
  }

  function mouseOffset(p) {
    const dx = p.x - state.mouse.x;
    const dy = p.y - state.mouse.y;
    const d2 = dx * dx + dy * dy;
    if (d2 > MOUSE_RADIUS * MOUSE_RADIUS) return null;
    const d = Math.sqrt(d2) || 1;
    const f = (1 - d / MOUSE_RADIUS) * MOUSE_PUSH;
    return { x: (dx / d) * f, y: (dy / d) * f };
  }

  /* ---------- Çizim ---------- */
  function buildGrid(cell) {
    const grid = new Map();
    for (const p of state.particles) {
      if (p.alpha < 0.05) continue;
      const key = ((p.x / cell) | 0) * GRID_KEY + ((p.y / cell) | 0);
      const bucket = grid.get(key);
      if (bucket) bucket.push(p); else grid.set(key, [p]);
    }
    return grid;
  }

  function collectLinks(p, grid, cell, paths) {
    const gx = (p.x / cell) | 0;
    const gy = (p.y / cell) | 0;
    const maxD2 = cell * cell;
    for (let ox = 0; ox <= 1; ox++) {
      for (let oy = -1; oy <= 1; oy++) {
        if (ox === 0 && oy < 0) continue;
        const bucket = grid.get((gx + ox) * GRID_KEY + (gy + oy));
        if (!bucket) continue;
        for (const q of bucket) {
          if (ox === 0 && oy === 0 && q.id <= p.id) continue;
          const dx = q.x - p.x;
          const dy = q.y - p.y;
          if (dx * dx + dy * dy > maxD2) continue;
          const path = paths[p.ci === 2 ? q.ci : p.ci];
          path.moveTo(p.x, p.y);
          path.lineTo(q.x, q.y);
        }
      }
    }
  }

  function drawLinks() {
    const cell = state.linkDist;
    const grid = buildGrid(cell);
    const paths = PALETTE.map(() => new Path2D());
    for (const p of state.particles) {
      if (p.alpha >= 0.05) collectLinks(p, grid, cell, paths);
    }
    const fade = 1 - clamp01(state.scroll * 1.4);
    ctx.lineWidth = Math.max(0.5, state.radius * 0.45);
    paths.forEach((path, i) => {
      ctx.strokeStyle = PALETTE[i];
      ctx.globalAlpha = LINK_ALPHA[i] * fade;
      ctx.stroke(path);
    });
    ctx.globalAlpha = 1;
  }

  function drawThreads() {
    // Haberci ile evi arasındaki iplik: ağın ekran boyunca gerilmesi
    ctx.lineWidth = 1;
    for (const p of state.particles) {
      if (!p.trip) continue;
      const g = ctx.createLinearGradient(p.hx, p.hy, p.x, p.y);
      g.addColorStop(0, "rgba(239,90,67,0)");
      g.addColorStop(1, PALETTE[p.ci]);
      ctx.strokeStyle = g;
      ctx.globalAlpha = 0.55 * p.alpha;
      ctx.beginPath();
      ctx.moveTo(p.hx, p.hy);
      ctx.quadraticCurveTo((p.hx + p.x) / 2, Math.min(p.hy, p.y) - 40, p.x, p.y);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  function drawParticle(p) {
    const vx = p.x - p.px;
    const vy = p.y - p.py;
    if (Math.hypot(vx, vy) > 2) {
      // Hızlı noktalar kısa bir kuyruk bırakır
      ctx.lineWidth = state.radius * 1.4;
      ctx.beginPath();
      ctx.moveTo(p.px - vx * 2, p.py - vy * 2);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();
      return;
    }
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.messenger ? state.radius * 1.6 : state.radius, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawParticles() {
    PALETTE.forEach((color, i) => {
      ctx.fillStyle = color;
      ctx.strokeStyle = color;
      for (const p of state.particles) {
        if (p.ci !== i || p.alpha < 0.02) continue;
        ctx.globalAlpha = p.alpha;
        drawParticle(p);
      }
    });
    ctx.globalAlpha = 1;
  }

  function paint(withThreads) {
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, state.w, state.h);
    drawLinks();
    if (withThreads) drawThreads();
    drawParticles();
  }

  /* ---------- Döngü ---------- */
  function step(now) {
    const elapsed = now - state.start;
    const introDone = elapsed > INTRO_SPREAD_MS + INTRO_MIN_MS + INTRO_TAIL_MS;
    for (const p of state.particles) {
      p.px = p.x;
      p.py = p.y;
      const settled = introDone || elapsed > p.delay + p.dur;
      const pos = settled ? settledPosition(p, now) : introPosition(p, elapsed);
      p.x = pos.x;
      p.y = pos.y;
      p.alpha = pos.alpha;
      const push = settled ? mouseOffset(p) : null;
      if (push) { p.x += push.x; p.y += push.y; }
    }
    paint(true);
  }

  function loop(now) {
    if (!state.running) return;
    step(now);
    requestAnimationFrame(loop);
  }

  function play() {
    if (state.running || reduceMotion || !state.visible || document.hidden) return;
    state.running = true;
    requestAnimationFrame(loop);
  }

  function pause() { state.running = false; }

  function renderStill() {
    for (const p of state.particles) {
      p.x = p.px = p.hx;
      p.y = p.py = p.hy;
      p.alpha = 1;
    }
    paint(false);
  }

  /* ---------- Olaylar ---------- */
  function onScroll() {
    state.scroll = clamp01(window.scrollY / (state.h || 1));
  }

  function bind() {
    window.addEventListener("resize", () => { layout(); if (reduceMotion) renderStill(); });
    window.addEventListener("scroll", onScroll, { passive: true });
    const host = canvas.parentElement;
    host.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      state.mouse.x = e.clientX - r.left;
      state.mouse.y = e.clientY - r.top;
    });
    host.addEventListener("pointerleave", () => { state.mouse.x = -9999; state.mouse.y = -9999; });
    document.addEventListener("visibilitychange", () => (document.hidden ? pause() : play()));
    new IntersectionObserver(([entry]) => {
      state.visible = entry.isIntersecting;
      if (state.visible) play(); else pause();
    }).observe(canvas);
  }

  buildParticles();
  layout();
  bind();
  onScroll();
  state.start = performance.now();
  if (reduceMotion) renderStill(); else play();
})();
