// Edição de vídeo gravado (pessoa falando) no estilo "análise política": zoom a cada frase, legenda palavra a palavra,
// fotos/números animados, tarja azul no gancho e efeitos sonoros (whoosh, pop, tique, impacto).
// Uso: node video/editar.mjs video/edicoes/<nome>.json [saida.mp4]
// Pré: transcrição com tempo por palavra (faster-whisper) em E.palavras. Ver video/transcrever.py.
import { createRequire } from "module";
import http from "http";
import fs from "fs";
import os from "os";
import path from "path";
import { spawn, execFileSync as run } from "child_process";
const require = createRequire(import.meta.url);
let pw; try { pw = require("playwright"); } catch { pw = require("/opt/node-tools/node_modules/playwright"); }
const RAIZ = path.resolve(path.dirname(new URL(import.meta.url).pathname), ".."), FPS = 30, W = 1080, H = 1920;
const arq = process.argv[2], E = JSON.parse(fs.readFileSync(arq, "utf8")), saida = process.argv[3] || path.join(RAIZ, "entregas", path.basename(arq, ".json") + "-editado.mp4");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "edicao-")), ff = (...a) => run("ffmpeg", ["-v", "error", "-y", ...a], { stdio: "inherit" });
const src = path.join(RAIZ, E.video);

// 1 · base: cada trecho com seu zoom (punch-in), em 1080×1920
const dur = +run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).toString();
const Z = E.zooms || [[0, 1]], partes = [];
Z.forEach(([t0, z], i) => { const t1 = Z[i + 1] ? Z[i + 1][0] : dur, o = path.join(tmp, `z${i}.mp4`);
  ff("-ss", String(t0), "-to", String(t1), "-i", src, "-vf", `scale=${Math.round(W * z)}:${Math.round(H * z)}:force_original_aspect_ratio=increase,crop=${W}:${H}:(iw-${W})/2:(ih-${H})/2*0.6,fps=${FPS},setsar=1`, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", o); partes.push(o); });
fs.writeFileSync(path.join(tmp, "l.txt"), partes.map((p) => `file '${p}'`).join("\n"));
const base0 = path.join(tmp, "base0.mp4"), base = path.join(tmp, "base.mp4"), extra = E.extra || 0, total = dur + extra;
ff("-f", "concat", "-safe", "0", "-i", path.join(tmp, "l.txt"), "-c", "copy", base0);
if (extra) ff("-i", base0, "-vf", `tpad=stop_mode=clone:stop_duration=${extra}`, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", base); else fs.renameSync(base0, base);

// 2 · camada animada (PNG com transparência) desenhada no navegador
const tipos = { ".html": "text/html", ".json": "application/json", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".woff2": "font/woff2" };
const srv = http.createServer((q, r) => { const f = path.join(RAIZ, decodeURIComponent(q.url.split("?")[0])); if (!f.startsWith(RAIZ) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { "content-type": tipos[path.extname(f).toLowerCase()] || "application/octet-stream" }); fs.createReadStream(f).pipe(r); });
await new Promise((ok) => srv.listen(0, ok));
const b = await pw.chromium.launch(), p = await b.newPage({ viewport: { width: W, height: H } });
await p.goto(`http://127.0.0.1:${srv.address().port}/video/cena-edicao.html?d=${encodeURIComponent("../" + path.relative(RAIZ, path.resolve(arq)))}`);
await p.waitForFunction(() => window.pronto === true, null, { timeout: 60000 });
const camada = path.join(tmp, "camada.mov"), n = Math.round(total * FPS);
const enc = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "png", "-i", "-", "-c:v", "qtrle", camada], { stdio: ["pipe", "inherit", "inherit"] });
for (let i = 0; i < n; i++) { const png = Buffer.from((await p.evaluate((t) => { window.render(t); return document.getElementById("c").toDataURL("image/png"); }, i / FPS)).split(",")[1], "base64"); if (!enc.stdin.write(png)) await new Promise((ok) => enc.stdin.once("drain", ok)); }
enc.stdin.end(); await new Promise((ok) => enc.on("close", ok)); await b.close(); srv.close();

// 3 · efeitos sonoros nos momentos das animações (python + numpy, ver video/sfx_edicao.py)
const efeitos = path.join(tmp, "sfx.wav");
run("python3", [path.join(RAIZ, "video/sfx_edicao.py"), arq, efeitos, String(total)], { stdio: "inherit" });

// 4 · junta: base + camada + voz original (limpa e nivelada) + efeitos
ff("-i", base, "-i", camada, "-i", src, "-i", efeitos, "-filter_complex",
  `[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]apad,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=1.0[voz];[3:a]volume=${E.volEfeitos ?? 0.55}[fx];[voz][fx]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5[a]`,
  "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "24", "-maxrate", "2200k", "-bufsize", "4400k", "-preset", "medium", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", String(total), saida);
fs.rmSync(tmp, { recursive: true, force: true });
console.log("✔", saida);
