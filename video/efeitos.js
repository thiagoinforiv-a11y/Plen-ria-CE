/* Pós-efeitos de imersão, comuns a todos os vídeos. O gravador chama posEfeitos(t, cfg) depois de render(t).
 * cfg (do arquivo de trilha): S = início das cenas, boom/impactos = revelações (tempos da animação).
 * Tudo depende só de t, então cada quadro sai igual em qualquer gravação. */
(() => {
  const tmp = document.createElement("canvas");
  const hash = (x) => { const s = Math.sin(x * 12.9898) * 43758.5453; return s - Math.floor(s); };
  const desde = (t, lista) => { let d = 1e9; for (const a of lista || []) if (t >= a) d = Math.min(d, t - a); return d; };
  window.posEfeitos = (t, cfg = {}) => {
    const cv = document.getElementById("c"), ctx = cv.getContext("2d"), W = cv.width, H = cv.height;
    tmp.width = W; tmp.height = H; const tc = tmp.getContext("2d"); tc.clearRect(0, 0, W, H); tc.drawImage(cv, 0, 0);
    const cortes = (cfg.S || []).slice(1, -1), imp = [...(cfg.boom || []), ...(cfg.impactos || [])];
    const dc = desde(t, cortes), di = desde(t, imp);
    // câmera: aproximação lenta dentro de cada cena + tremor curto nos impactos
    const ini = Math.max(0, ...[0, ...(cfg.S || [])].filter((a) => a <= t)), fim = (cfg.S || []).find((a) => a > t) || ini + 8;
    const push = 1 + 0.035 * Math.min(1, (t - ini) / Math.max(1, fim - ini));
    const tremor = di < 0.35 ? (1 - di / 0.35) * 9 : 0;
    const sx = (hash(Math.floor(t * 30)) - 0.5) * 2 * tremor, sy = (hash(Math.floor(t * 30) + 7) - 0.5) * 2 * tremor;
    ctx.save(); ctx.fillStyle = "#060606"; ctx.fillRect(0, 0, W, H);
    ctx.translate(W / 2 + sx, H / 2 + sy); ctx.scale(push, push); ctx.drawImage(tmp, -W / 2, -H / 2); ctx.restore();
    // glitch nos cortes: faixas horizontais deslocadas
    if (dc < 0.18) {
      const k = 1 - dc / 0.18; tc.clearRect(0, 0, W, H); tc.drawImage(cv, 0, 0);
      for (let i = 0; i < 9; i++) { const y = hash(i * 3.1 + Math.floor(t * 30)) * H, h = 8 + hash(i * 5.3) * 60, dx = (hash(i * 7.7 + t) - 0.5) * 90 * k;
        ctx.drawImage(tmp, 0, y, W, h, dx, y, W, h); }
      ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.globalAlpha = 0.18 * k; ctx.drawImage(tmp, 10 * k, 0); ctx.restore();
    }
    // faixa de luz cruzando a tela no começo de cada cena
    if (dc < 1.1) { const k = dc / 1.1, x = -W * 0.6 + k * W * 2.2; ctx.save(); ctx.globalCompositeOperation = "lighter";
      const g = ctx.createLinearGradient(x - 220, 0, x + 220, H * 0.25); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, `rgba(235,255,190,${0.09 * (1 - k)})`); g.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    // clarão nas revelações
    if (di < 0.5) { const k = 1 - di / 0.5; ctx.save(); ctx.globalCompositeOperation = "lighter"; const g = ctx.createRadialGradient(W / 2, H * 0.45, 0, W / 2, H * 0.45, H * 0.7);
      g.addColorStop(0, `rgba(255,255,240,${0.22 * k * k})`); g.addColorStop(1, "rgba(255,255,255,0)"); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    // vinheta
    const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.55)"); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  };
})();
