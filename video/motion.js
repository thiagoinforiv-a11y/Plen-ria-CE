/* Acabamento de motion graphics para as cenas (camada por cima do render da cena).
   Uso, no fim da cena:  window.render = Motion.envolver(window.render, ctx, S, { moldura: { serie: "RAIO-X", cta: "Comenta a próxima cidade" } });
   - câmera: empurra devagar (1,00 → 1,045) em cada cena e dá um "soco" de zoom no corte;
   - corte: alterna glitch (fatias deslocadas + separação de cor) e flash branco;
   - respiro: Motion.respiro = [índices de cena] escurece a tela por 0,5 s antes daquela cena (revelação);
   - moldura opcional: tarja da série no topo e chamada para ação nos últimos segundos. */
(() => {
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), eout = (x) => 1 - Math.pow(1 - x, 3);
  const ruido = (n) => { const x = Math.sin(n * 12.9898) * 43758.5453; return x - Math.floor(x); };
  const envolver = (render, ctx, S, o = {}) => {
    const W = ctx.canvas.width, H = ctx.canvas.height, off = document.createElement("canvas"); off.width = W; off.height = H; const oc = off.getContext("2d");
    const cena = (t) => { let k = 0; while (k + 1 < S.length - 1 && t >= S[k + 1]) k++; return k; };
    return (t) => {
      const k = cena(t), p = clamp((t - S[k]) / Math.max(0.1, S[k + 1] - S[k])), dc = t - S[k];
      const soco = k > 0 && dc < 0.45 ? 0.06 * (1 - eout(dc / 0.45)) : 0;
      const z = (o.camera === false ? 1 : 1 + 0.045 * p) + soco, dx = Math.sin(k * 1.7) * 18 * p, dy = Math.cos(k * 1.3) * 12 * p;
      ctx.save(); ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2); render(t); ctx.restore();
      // corte: glitch ou flash nos primeiros 0,28 s de cada cena
      if (k > 0 && dc < 0.28) { const g = 1 - dc / 0.28;
        if (k % 2) { oc.clearRect(0, 0, W, H); oc.drawImage(ctx.canvas, 0, 0); const n = 9;
          for (let i = 0; i < n; i++) { const y = Math.floor(ruido(k * 31 + i) * H), h = 20 + ruido(k * 7 + i) * 120, s = (ruido(k * 13 + i + Math.floor(t * 30)) - 0.5) * 140 * g; ctx.drawImage(off, 0, y, W, h, s, y, W, h); }
          ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = 0.35 * g; ctx.drawImage(off, 10 * g, 0); ctx.fillStyle = `rgba(255,40,60,${0.18 * g})`; ctx.fillRect(0, 0, W, H); ctx.restore();
        } else { ctx.save(); ctx.fillStyle = `rgba(255,255,255,${0.45 * g * g})`; ctx.fillRect(0, 0, W, H); ctx.restore(); } }
      // respiro: escurece antes da revelação
      (o.respiro || []).forEach((i) => { const a = clamp(1 - Math.abs(t - S[i]) / 0.5); if (a > 0) { ctx.save(); ctx.fillStyle = `rgba(0,0,0,${0.85 * a})`; ctx.fillRect(0, 0, W, H); ctx.restore(); } });
      // moldura: tarja da série e chamada final
      if (o.moldura) { const m = o.moldura, F = "Oswald, sans-serif";
        if (m.serie) { ctx.save(); ctx.font = `700 34px ${F}`; ctx.letterSpacing = "6px"; const w = ctx.measureText(m.serie).width + 60; ctx.fillStyle = "rgba(255,209,102,.95)"; ctx.beginPath(); ctx.roundRect(W / 2 - w / 2, 120, w, 58, 10); ctx.fill(); ctx.fillStyle = "#0b1622"; ctx.textAlign = "center"; ctx.fillText(m.serie, W / 2, 161); ctx.restore(); }
        const fim = S[S.length - 1]; if (m.cta && t > fim - 4) { const a = eout(clamp((t - (fim - 4)) / 0.5)); ctx.save(); ctx.globalAlpha = a; ctx.font = `700 40px ${F}`; const w = ctx.measureText(m.cta).width + 70, y = 1560 + (1 - a) * 30; ctx.fillStyle = "#ffffff"; ctx.beginPath(); ctx.roundRect(W / 2 - w / 2, y, w, 76, 38); ctx.fill(); ctx.fillStyle = "#0b1622"; ctx.textAlign = "center"; ctx.fillText(m.cta, W / 2, y + 52); ctx.restore(); } }
    };
  };
  window.Motion = { envolver };
})();
