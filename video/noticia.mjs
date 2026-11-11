// Vídeo-notícia com imagens/vídeos reais + tarja azul @PLENARIACE (identidade do perfil). Um comando por vídeo.
// Uso: node video/noticia.mjs video/noticias/<pauta>.json [saida.mp4]
// Pauta: { id, fontes, cenas: [{ fala, tarja, midia?, ini?, credito?, grande?, sub?, semTarja?, original? (com ini e fim: fala original do vídeo, sem narração) }] }
//   midia: imagem ou vídeo local (vídeo deitado/foto ganha fundo desfocado; foto ganha zoom lento). Sem midia: cartão escuro
//   com "grande"/"sub" (número de impacto). A narração vem de video/audio/<id>/antonio/NN.mp3 (Action narracao.yml).
// Regras visuais: só a tarja azul na tela (+ crédito pequeno), cortes curtos (a duração de cada cena = a fala), sem efeitos extras.
import { createRequire } from "module";
import fs from "fs";
import os from "os";
import path from "path";
import { execFileSync as run } from "child_process";
const require = createRequire(import.meta.url);
let pw; try { pw = require("playwright"); } catch { pw = require("/opt/node-tools/node_modules/playwright"); }

const RAIZ = path.resolve(path.dirname(new URL(import.meta.url).pathname), ".."), W = 1080, H = 1920, AZUL = "#1f3fae", TEMPO = 1.12;
const arq = process.argv[2], D = JSON.parse(fs.readFileSync(arq, "utf8")), saida = process.argv[3] || path.join(RAIZ, "entregas", D.id + ".mp4");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "noticia-")), q = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/\n/g, "<br>");
const ff = (...a) => run("ffmpeg", ["-v", "error", "-y", ...a], { stdio: "inherit" });
const dur = (f) => +run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).toString();
const fonte = (n) => `data:font/woff2;base64,${fs.readFileSync(path.join(RAIZ, "video/fontes", n)).toString("base64")}`;

// 1 · artes transparentes de cada cena (tarja, crédito, número de impacto) num só navegador
const b = await pw.chromium.launch(), p = await b.newPage({ viewport: { width: W, height: H } });
const css = `@font-face{font-family:O;font-weight:700;src:url(${fonte("oswald-latin-700-normal.woff2")})}
@font-face{font-family:A;src:url(${fonte("anton-latin-400-normal.woff2")})}
html,body{margin:0;width:${W}px;height:${H}px;background:transparent}
.t{position:absolute;left:0;right:0;top:${Math.round(H * (D.tarjaY || 0.72))}px;display:flex;flex-direction:column;align-items:center}
.s{background:#fff;color:${AZUL};font:700 42px/1 O;padding:8px 16px 9px}
.x{background:${AZUL};color:#fff;font:700 54px/1.08 O;text-transform:uppercase;text-align:center;max-width:900px;padding:14px 26px 16px;box-shadow:0 6px 24px rgba(0,0,0,.35);text-wrap:balance}
.c{position:absolute;right:40px;bottom:70px;color:rgba(255,255,255,.75);font:700 24px O;text-shadow:0 1px 4px #000}
.g{position:absolute;left:50%;transform:translateX(-50%);top:${Math.round(H * 0.28)}px;text-align:center;color:#fff;font:400 230px/1 A;text-shadow:0 8px 40px rgba(0,0,0,.5);background:rgba(8,12,30,.72);padding:30px 44px 34px;border-radius:24px;border-bottom:10px solid ${AZUL};white-space:nowrap}
.n{font:inherit}.g small{display:block;font:700 56px O;letter-spacing:6px;margin-top:18px;color:#fff}`;
for (const [i, c] of D.cenas.entries()) {
  await p.setContent(`<style>${css}</style>${c.grande ? `<div class="g"><span class="n">${q(c.grande)}</span>${c.sub ? `<small>${q(c.sub)}</small>` : ""}</div>` : ""}` +
    (D.semTarja || c.semTarja ? "" : `<div class="t"><div class="s">@PLENARIACE</div><div class="x">${q(c.tarja)}</div></div>`) + `${c.credito || (i === D.cenas.length - 1 && D.fontes) ? `<div class="c">${q(c.credito || D.fontes)}</div>` : ""}`);
  await p.evaluate(() => document.fonts.ready);
  await p.evaluate(() => { const g = document.querySelector(".n"); if (g) { let f = 230; while (g.getBoundingClientRect().width > 980 && f > 90) { f -= 10; g.style.fontSize = f + "px"; } } });
  await p.evaluate(() => { const t = document.querySelector(".x"); if (!t) return; let f = 54; while (t.getBoundingClientRect().height > 3 * f * 1.08 + 34 && f > 34) { f -= 2; t.style.fontSize = f + "px"; } });
  await p.screenshot({ path: path.join(tmp, `a${i}.png`), omitBackground: true });
}
await b.close();

// 2 · cada cena: fala (acelerada) + fundo real + arte, com a duração exata da fala
const partes = []; let kv = 0;
for (const [i, c] of D.cenas.entries()) {
  const wav = path.join(tmp, `v${i}.wav`);
  if (c.original) { // trecho com a fala original da pessoa (sem narração): áudio do próprio vídeo, de ini a fim
    ff("-ss", String(c.ini), "-t", String(c.fim - c.ini), "-i", path.resolve(RAIZ, c.midia), "-vn", "-af", "apad=pad_dur=0.15", "-ar", "48000", "-ac", "2", wav);
  } else {
    const voz = path.join(RAIZ, "video/audio", D.id, "antonio", String(kv++).padStart(2, "0") + ".mp3");
    ff("-i", voz, "-af", `atempo=${TEMPO},apad=pad_dur=0.25`, "-ar", "48000", "-ac", "2", wav);
  }
  const T = dur(wav).toFixed(2), out = path.join(tmp, `c${i}.mp4`), arte = path.join(tmp, `a${i}.png`);
  const m = c.midia && path.resolve(RAIZ, c.midia), video = m && /\.(mp4|mov|webm|mkv)$/i.test(m);
  const fundo = `split[a][b];[a]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=30:2,eq=brightness=-0.15[f];[b]scale=${W}:${H}:force_original_aspect_ratio=decrease[c];[f][c]overlay=(W-w)/2:(H-h)/2*0.8`;
  let ent, vf;
  if (!m && D.fundo) { ent = ["-loop", "1", "-t", T, "-i", path.resolve(RAIZ, D.fundo)]; vf = `scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=40:3,eq=brightness=-0.32:saturation=1.2,zoompan=z='min(1+0.0006*on,1.06)':d=1:s=${W}x${H}:fps=30`; }
  else if (!m) { ent = ["-f", "lavfi", "-i", `color=c=0x0b0f1f:s=${W}x${H}:r=30:d=${T}`]; vf = "null"; }
  else if (video) { ent = ["-ss", String(c.ini || 0), "-t", T, "-i", m]; vf = `${fundo},fps=30`; }
  else { ent = ["-loop", "1", "-t", T, "-i", m]; vf = `scale=${W * 1.2}:${H * 1.2}:force_original_aspect_ratio=increase,${fundo.replace(`scale=${W}:${H}:force_original_aspect_ratio=decrease`, `scale=${W}:${H}:force_original_aspect_ratio=decrease`)},zoompan=z='min(1+0.0009*on,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${W}x${H}:fps=30`; }
  const fc = `[0:v]${vf},setsar=1,format=yuv420p[v];[v][1:v]overlay=0:0[o];` + (video && !c.original ? `[0:a]volume=0.12,aresample=48000,aformat=channel_layouts=stereo[x];[2:a][x]amix=inputs=2:duration=first:normalize=0[s]` : `[2:a]anull[s]`);
  try { ff(...ent, "-i", arte, "-i", wav, "-filter_complex", fc, "-map", "[o]", "-map", "[s]", "-t", T, "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-ar", "48000", out); }
  catch (e) { // vídeo sem áudio: refaz só com a fala
    ff(...ent, "-i", arte, "-i", wav, "-filter_complex", fc.replace(/\[0:a\].*$/, "[2:a]anull[s]"), "-map", "[o]", "-map", "[s]", "-t", T, "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-ar", "48000", out); }
  partes.push(out);
}

// 3 · junta, normaliza o volume e comprime no padrão de entrega (leve, salva no celular)
fs.writeFileSync(path.join(tmp, "l.txt"), partes.map((f) => `file '${f}'`).join("\n"));
fs.mkdirSync(path.dirname(saida), { recursive: true });
ff("-f", "concat", "-safe", "0", "-i", path.join(tmp, "l.txt"), "-af", "loudnorm=I=-14:TP=-1.5", "-c:v", "libx264", "-crf", "25", "-maxrate", "2200k", "-bufsize", "4400k", "-preset", "medium", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", saida);
fs.rmSync(tmp, { recursive: true, force: true });
console.log("✔", saida, dur(saida).toFixed(1) + "s");
