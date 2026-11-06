/* Apresentação de abertura (1920x1080, ~15s, GSAP).
 * Roda sozinha na primeira visita do dispositivo; depois, pelo botão "Apresentação". */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const KEY = "plenaria.intro.v1";
  const intro = $("#intro"), stage = $("#stage"), ui = $("#intro-ui");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let tl = null, done = false;

  const visto = () => { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } };
  const marcar = () => { try { localStorage.setItem(KEY, "1"); } catch (e) { /* ok */ } };

  function fit() {
    const s = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(-50%, -50%) scale(${s})`;
  }

  function finish() {
    if (done) return;
    done = true;
    marcar();
    if (tl) tl.pause();
    window.App.show();
    const out = () => { intro.style.display = "none"; ui.style.display = "none"; document.body.style.overflow = ""; };
    if (window.gsap) gsap.to([intro, ui], { opacity: 0, duration: 0.6, ease: "power2.inOut", onComplete: out });
    else out();
  }

  function hideAll() {
    intro.style.display = "none"; ui.style.display = "none";
    $("#app").style.opacity = 1;
  }

  const fmtInt = (n) => Math.round(n).toLocaleString("pt-BR");
  const fmtPct = (n) => n.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  function fill(d) {
    const val = {
      aptos: d ? d.aptos : 0, secoes: d ? d.secoes : 0,
      comparecimento: d ? d.comparecimento : 0, abstencoes: d ? d.abstencoes : 0,
      pct: d && d.aptos ? (100 * d.comparecimento) / d.aptos : 0,
    };
    $$("[data-txt]").forEach((el) => (el.textContent = fmtInt(val[el.dataset.txt] || 0)));
    $$("[data-src]").forEach((el) => (el.textContent = d ? `Fonte: TSE · ${d.municipio}/${d.uf} · eleições ${d.ano}, 1º turno` : ""));
    $$("[data-yr]").forEach((el) => (el.textContent = d ? `${d.ano} · 1º turno` : ""));
    // grade com uma bolinha por seção
    const grid = $(".dotgrid");
    const n = Math.min(val.secoes || 0, 132);
    grid.innerHTML = "<i></i>".repeat(n);
    grid.style.gridTemplateColumns = `repeat(${n > 96 ? 12 : 10}, 40px)`;
    // pontos do radar (decorativos: um por seção, em espiral áurea)
    const g = $("#s2 .dots");
    let pts = "";
    for (let i = 0; i < (val.secoes || 60); i++) {
      const r = 250 * Math.sqrt((i + 0.5) / (val.secoes || 60)), a = i * 2.39996;
      pts += `<circle cx="${(380 + r * Math.cos(a)).toFixed(1)}" cy="${(380 + r * Math.sin(a)).toFixed(1)}" r="6" fill="#d4ff3a"/>`;
    }
    g.innerHTML = pts;
    return val;
  }

  function counter(tlx, el, to, at, dur, pct) {
    const o = { v: 0 };
    tlx.to(o, { v: to, duration: dur, ease: "power2.out", onUpdate: () => (el.textContent = pct ? fmtPct(o.v) : fmtInt(o.v)) }, at);
  }

  function build(val) {
    if (tl) tl.kill();
    gsap.killTweensOf([".ring", "#s2 .sweep"]);
    // estado inicial
    const line = $("#line"), slot = $("#oslot"), word = $("#word");
    const ox = word.offsetLeft + slot.offsetLeft + slot.offsetWidth / 2;
    const oy = 540;
    const oxp = (ox / 1920) * 100, oyp = (oy / 1080) * 100;
    gsap.set(line, { left: 960, top: 540, width: 0, height: 8, borderRadius: 999, backgroundColor: "#d4ff3a", border: "0px solid #d4ff3a", xPercent: -50, yPercent: -50, x: 0, y: 0, rotation: 0, opacity: 1 });
    gsap.set("#word .mask > span", { yPercent: 110 });
    gsap.set("#word-sub .ws", { y: 40, opacity: 0 });
    gsap.set(["#s2", "#h2", "#s5"], { clipPath: `circle(0% at ${oxp}% ${oyp}%)` });
    gsap.set("#s3", { clipPath: "inset(0% 0% 0% 100%)" });
    gsap.set(["#h1", "#h3"], { clipPath: "inset(100% 0% 0% 0%)" });
    gsap.set(".l2", { y: 80, opacity: 0 });
    gsap.set("#s2 .kicker", { opacity: 0, y: 20 });
    gsap.set("#s2 .emblem", { scale: 0.6, rotation: -40, opacity: 0, transformOrigin: "50% 50%" });
    gsap.set("#s2 .dots circle", { scale: 0, transformOrigin: "50% 50%", transformBox: "fill-box" });
    gsap.set("#s3 .w > *", { yPercent: 115 });
    gsap.set("#s3 .sub", { opacity: 0, y: 20 });
    gsap.set(".hl > div:first-child > *", { y: 50, opacity: 0 });
    gsap.set(".barviz .fill", { width: 0 });
    gsap.set(".dotgrid i", { scale: 0 });
    gsap.set(".donut .arc", { strokeDashoffset: 502.65 });
    gsap.set("#s5 .emblem", { scale: 0, rotation: -90, transformOrigin: "50% 50%" });
    gsap.set(["#s5 .title", "#s5 .cta"], { y: 50, opacity: 0 });
    gsap.set("#btn-enter", { scale: 0, xPercent: 0 });
    gsap.set("#cursor", { left: 1560, top: 1120, scale: 1 });
    gsap.set(".ripple", { scale: 0, opacity: 1 });
    $$("[data-count]").forEach((el) => (el.textContent = "0"));

    // anéis de texto girando o tempo todo
    gsap.to(".ring", { rotation: 360, duration: 18, repeat: -1, ease: "none", svgOrigin: "380 380" });
    gsap.to("#s2 .sweep", { rotation: 360, duration: 3.2, repeat: -1, ease: "none", svgOrigin: "380 380" });

    const t = gsap.timeline({ onUpdate: () => ($("#intro-progress").style.width = t.progress() * 100 + "%"), onComplete: finish });

    // CENA 1 — linha → pílula → "O" de VARJOTA (0 – 3s)
    t.to(line, { width: 1100, duration: 0.8, ease: "power3.inOut" }, 0.15)
      .to(line, { width: 300, height: 110, duration: 0.4, ease: "power3.inOut" }, 0.95)
      .to(line, { left: ox, width: 176, height: 196, borderWidth: 38, backgroundColor: "rgba(212,255,58,0)", duration: 0.55, ease: "power3.inOut" }, 1.35)
      .to("#word .mask > span", { yPercent: 0, duration: 0.6, ease: "power4.out", stagger: { each: 0.05, from: "center" } }, 1.55)
      .to("#word-sub .ws", { y: 0, opacity: 1, duration: 0.5, stagger: 0.07, ease: "power3.out" }, 2.0);

    // CENA 2 — íris a partir do "O" + emblema com texto girando (3 – 5.6s)
    t.to("#s2", { clipPath: `circle(150% at ${oxp}% ${oyp}%)`, duration: 0.9, ease: "power3.inOut" }, 3.0)
      .to("#s2 .kicker", { opacity: 1, y: 0, duration: 0.4 }, 3.45)
      .to(".l2", { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: "power3.out" }, 3.5)
      .to("#s2 .emblem", { scale: 1, rotation: 0, opacity: 1, duration: 1.0, ease: "power3.out" }, 3.4)
      .to("#s2 .dots circle", { scale: 1, duration: 0.3, stagger: { each: 0.008, from: "start" }, ease: "back.out(3)" }, 3.8);

    // CENA 3 — frase de impacto, wipe lateral (5.6 – 8s)
    t.to("#s3", { clipPath: "inset(0% 0% 0% 0%)", duration: 0.7, ease: "power4.inOut" }, 5.6)
      .to("#s3 .w > *", { yPercent: 0, duration: 0.7, stagger: 0.09, ease: "power4.out" }, 6.0)
      .to("#s3 .sub", { opacity: 1, y: 0, duration: 0.5 }, 6.8);

    // CENA 4 — três destaques com infográficos e count-up (8 – 12.4s)
    const comp = val.aptos ? val.comparecimento / val.aptos : 0, abst = val.aptos ? val.abstencoes / val.aptos : 0;
    t.to("#h1", { clipPath: "inset(0% 0% 0% 0%)", duration: 0.6, ease: "power4.inOut" }, 8.0)
      .to("#h1 .hl > div:first-child > *", { y: 0, opacity: 1, duration: 0.5, stagger: 0.07 }, 8.3);
    counter(t, $("#h1 [data-count]"), val.aptos, 8.35, 1.0);
    t.to('#h1 .fill[data-w="1"]', { width: "100%", duration: 0.8, ease: "power3.out" }, 8.4)
      .to('#h1 .fill[data-w="comp"]', { width: comp * 100 + "%", duration: 0.8, ease: "power3.out" }, 8.55)
      .to('#h1 .fill[data-w="abst"]', { width: abst * 100 + "%", duration: 0.8, ease: "power3.out" }, 8.7);

    t.to("#h2", { clipPath: `circle(150% at 75% 50%)`, duration: 0.7, ease: "power3.inOut" }, 9.5)
      .to("#h2 .hl > div:first-child > *", { y: 0, opacity: 1, duration: 0.5, stagger: 0.07 }, 9.75)
      .to(".dotgrid i", { scale: 1, duration: 0.25, stagger: { each: 0.006, grid: "auto", from: "start" }, ease: "back.out(3)" }, 9.8);
    counter(t, $("#h2 [data-count]"), val.secoes, 9.8, 0.8);

    t.to("#h3", { clipPath: "inset(0% 0% 0% 0%)", duration: 0.6, ease: "power4.inOut" }, 11.0)
      .to("#h3 .hl > div:first-child > *", { y: 0, opacity: 1, duration: 0.5, stagger: 0.07 }, 11.25)
      .to(".donut .arc", { strokeDashoffset: 502.65 * (1 - comp), duration: 1.0, ease: "power3.out" }, 11.3);
    counter(t, $("#h3 [data-count]"), val.pct, 11.3, 1.0, true);

    // CENA 5 — fechamento: emblema + nome + CTA com clique (12.4 – 15s)
    t.to("#s5", { clipPath: `circle(150% at 50% 30%)`, duration: 0.8, ease: "power3.inOut" }, 12.4)
      .to("#s5 .emblem", { scale: 1, rotation: 0, duration: 0.9, ease: "back.out(1.4)" }, 12.6)
      .fromTo("#s5 .pfoto", { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.8, ease: "back.out(1.6)" }, 12.95)
      .to("#s5 .title", { y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }, 12.8)
      .to("#s5 .cta", { y: 0, opacity: 1, duration: 0.5 }, 13.0)
      .to("#btn-enter", { scale: 1, duration: 0.5, ease: "back.out(2)" }, 13.15)
      .to("#cursor", { left: 990, top: 870, duration: 0.8, ease: "power3.inOut" }, 13.55)
      .to("#cursor", { scale: 0.82, duration: 0.1, yoyo: true, repeat: 1 }, 14.4)
      .to("#btn-enter", { scale: 0.93, duration: 0.1, yoyo: true, repeat: 1 }, 14.4)
      .to(".ripple", { scale: 26, opacity: 0, duration: 0.6, ease: "power2.out" }, 14.45)
      .to({}, { duration: 0.3 }, 14.75);
    return t;
  }

  function play() {
    if (!window.gsap) { hideAll(); return; }
    done = false;
    document.body.style.overflow = "hidden";
    window.scrollTo(0, 0);
    intro.style.display = ""; ui.style.display = "";
    gsap.set([intro, ui], { opacity: 1 });
    fit();
    const dados = window.App.introData();
    const val = fill(dados);
    // foto do prefeito no centro do emblema final (some sozinha se não carregar)
    const pf = document.querySelector("#s5 .pfoto"), img = pf && pf.querySelector("img");
    if (pf && dados && dados.fotoPrefeito) { img.src = dados.fotoPrefeito; img.referrerPolicy = "no-referrer"; img.onerror = () => pf.classList.add("off"); pf.querySelector(".pnome").textContent = "Prefeito " + (dados.prefeito || ""); pf.classList.remove("off"); }
    else if (pf) pf.classList.add("off");
    if (reduce) {
      // sem movimento: só o quadro final, com o botão
      gsap.set(["#s2", "#s3", "#h1", "#h2", "#h3"], { clipPath: "inset(0% 0% 100% 0%)" });
      gsap.set("#s5", { clipPath: "none" });
      gsap.set(["#s5 .title", "#s5 .cta"], { opacity: 1, y: 0 });
      gsap.set("#btn-enter", { scale: 1 });
      gsap.set("#cursor", { display: "none" });
      return;
    }
    tl = build(val);
  }

  addEventListener("resize", fit);
  $("#btn-skip").addEventListener("click", finish);
  $("#btn-enter").addEventListener("click", finish);
  $("#btn-replay").addEventListener("click", () => { if (tl) { done = false; tl.restart(); } });
  addEventListener("keydown", (e) => { if (e.key === "Escape" && intro.style.display !== "none") finish(); });

  window.Intro = { play };

  window.App.ready.then(() => {
    const forcar = /[?&]intro\b/.test(location.search);
    if (visto() && !forcar) { hideAll(); return; }
    (document.fonts ? document.fonts.ready : Promise.resolve()).then(play);
  });
})();
