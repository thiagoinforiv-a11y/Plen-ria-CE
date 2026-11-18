// Tarja de notícia do @plenariace (padrão dos vídeos que mais performaram): vídeo real + selo "@PLENARIACE"
// (branco, letra azul) + título em caixa alta numa tarja azul (letra branca, fonte condensada).
// Uso: node video/tarja.mjs entrada.mp4 "TÍTULO DA NOTÍCIA" saida.mp4 [--pos 0.66] [--ini 3.2] [--fim 27] [--zoom 1.0] [--ate 4]
//   --ate  a tarja some depois desses segundos (gancho/capa em vídeos de dados)
//   --pos  altura do centro da tarja (0 = topo, 1 = base)      --ini/--fim  corte do trecho (segundos)
//   --zoom aproxima o vídeo (vídeo deitado vira em pé com fundo desfocado; zoom > 1 corta as bordas)
import { createRequire } from "module";
import fs from "fs";
import os from "os";
import path from "path";
import { execFileSync } from "child_process";
const require = createRequire(import.meta.url);
let pw; try { pw = require("playwright"); } catch { pw = require("/opt/node-tools/node_modules/playwright"); }

const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : d; };
const pos = +opt("--pos", 0.66), ini = opt("--ini", null), fim = opt("--fim", null), zoom = +opt("--zoom", 1), ate = opt("--ate", null);
const [entrada, titulo, saida] = args;
if (!entrada || !titulo || !saida) { console.error('uso: node video/tarja.mjs entrada.mp4 "TÍTULO" saida.mp4 [--pos 0.66] [--ini s] [--fim s]'); process.exit(1); }
const W = 1080, H = 1920, AZUL = "#1f3fae", FONTES = path.join(path.dirname(new URL(import.meta.url).pathname), "fontes");
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tarja-")), png = path.join(tmp, "tarja.png");

// 1 · arte da tarja (PNG transparente 1080×1920) desenhada no navegador, com a fonte condensada
const html = `<!doctype html><meta charset="utf-8"><style>
@font-face { font-family: Oswald; font-weight: 700; src: url(data:font/woff2;base64,${fs.readFileSync(path.join(FONTES, "oswald-latin-700-normal.woff2")).toString("base64")}); }
html, body { margin: 0; width: ${W}px; height: ${H}px; background: transparent; }
.bloco { position: absolute; left: 0; right: 0; top: ${Math.round(pos * H)}px; transform: translateY(-50%); display: flex; flex-direction: column; align-items: center; }
.selo { background: #fff; color: ${AZUL}; font: 700 44px/1 Oswald; padding: 8px 16px 9px; letter-spacing: .5px; }
.titulo { background: ${AZUL}; color: #fff; font: 700 54px/1.08 Oswald; text-transform: uppercase; text-align: center;
  max-width: 900px; padding: 14px 26px 16px; box-shadow: 0 6px 24px rgba(0,0,0,.35); letter-spacing: .3px; text-wrap: balance; }
</style><div class="bloco"><div class="selo">@PLENARIACE</div><div class="titulo">${esc(titulo)}</div></div>`;
const b = await pw.chromium.launch(), p = await b.newPage({ viewport: { width: W, height: H } });
await p.setContent(html); await p.evaluate(() => document.fonts.ready);
// título comprido: reduz a fonte até caber em 3 linhas
await p.evaluate(() => { const t = document.querySelector(".titulo"); let f = 54; while (t.getBoundingClientRect().height > 3 * f * 1.08 + 34 && f > 34) { f -= 2; t.style.fontSize = f + "px"; } });
await p.screenshot({ path: png, omitBackground: true }); await b.close();

// 2 · vídeo em pé 1080×1920: deitado ganha fundo desfocado; em pé é cortado para preencher
const info = JSON.parse(execFileSync("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_side_data=rotation", "-of", "json", entrada]).toString()).streams[0];
let vw = info.width, vh = info.height; const rot = Math.abs(((info.side_data_list || [])[0] || {}).rotation || 0); if (rot === 90 || rot === 270) [vw, vh] = [vh, vw];
const emPe = vh / vw > 1.4;
const filtro = emPe
  ? `[0:v]scale=${W * zoom}:${H * zoom}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1[v];[v][1:v]overlay=0:0${ate ? `:enable='lte(t,${ate})'` : ""},format=yuv420p[o]`
  : `[0:v]split[a][b];[a]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=28:2,eq=brightness=-0.12[f];` +
    `[b]scale=${Math.round(W * zoom)}:-2,crop='min(iw,${W})':ih[c];[f][c]overlay=(W-w)/2:${Math.round(H * 0.36)}-h/2[v];[v][1:v]overlay=0:0,format=yuv420p[o]`;
const corte = [...(ini ? ["-ss", ini] : []), ...(fim ? ["-to", fim] : [])];
execFileSync("ffmpeg", ["-v", "error", "-y", ...corte, "-i", entrada, "-i", png, "-filter_complex", filtro, "-map", "[o]", "-map", "0:a?",
  "-c:v", "libx264", "-crf", "23", "-maxrate", "2200k", "-bufsize", "4400k", "-preset", "medium", "-r", "30", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", saida], { stdio: "inherit" });
fs.rmSync(tmp, { recursive: true, force: true });
console.log("✔", saida);
