// Aplica um estilo de edição (video/estilos/<estilo>.html) sobre um vídeo filmado.
// Uso: node video/estilo.mjs --estilo eletrico --video bruto.mp4 --roteiro roteiro.json --saida final.mp4 [--audio trilha.wav]
// O roteiro diz as batidas (cortes/efeitos), os textos e onde está a pessoa no quadro. Sem --audio, usa o áudio do próprio vídeo.
import { createRequire } from "module"; import http from "http"; import fs from "fs"; import path from "path"; import { spawn, spawnSync } from "child_process";
const require = createRequire(import.meta.url); let pw; try { pw = require("playwright"); } catch { pw = require("/opt/node-tools/node_modules/playwright"); }
const raiz = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const a = process.argv.slice(2), opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const estilo = opt("--estilo", "eletrico"), video = path.resolve(opt("--video")), saida = path.resolve(opt("--saida")), audio = opt("--audio"), fps = +opt("--fps", 30);
const R = JSON.parse(fs.readFileSync(opt("--roteiro"), "utf8"));
const pasta = path.join(raiz, "entregas", "_quadros", path.basename(saida, ".mp4")); fs.rmSync(pasta, { recursive: true, force: true }); fs.mkdirSync(pasta, { recursive: true });
let base = video;
if (R.trechos) { // edição: junta os trechos na ordem (cortes secos), já em 1080×1920
  const lista = R.trechos.map(([arq, ini, fim]) => ["-ss", String(ini), "-to", String(fim), "-i", path.resolve(arq)]).flat();
  const fc = R.trechos.map((_, i) => `[${i}:v]fps=${fps},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v${i}];[${i}:a]aresample=48000,aformat=channel_layouts=stereo[a${i}]`).join(";") + ";" + R.trechos.map((_, i) => `[v${i}][a${i}]`).join("") + `concat=n=${R.trechos.length}:v=1:a=1[v][a]`;
  base = path.join(pasta, "..", path.basename(saida, ".mp4") + ".base.mp4");
  spawnSync("ffmpeg", ["-v", "error", "-y", ...lista, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", base], { stdio: "inherit" });
  let acc = 0; R.cortes = R.trechos.slice(0, -1).map(([, i0, i1]) => (acc += i1 - i0));
}
if (R.palavras === "auto") { const pj = path.join(pasta, "..", path.basename(saida, ".mp4") + ".palavras.json"); spawnSync("python3", [path.join(raiz, "video", "transcrever.py"), "--video", base, "--saida", pj, ...(R.vocab ? ["--vocab", R.vocab] : [])], { stdio: "inherit" }); R.palavras = JSON.parse(fs.readFileSync(pj, "utf8")); }
else if (typeof R.palavras === "string") R.palavras = JSON.parse(fs.readFileSync(R.palavras, "utf8"));
spawnSync("ffmpeg", ["-v", "error", "-i", base, ...(R.ini ? ["-ss", String(R.ini)] : []), ...(R.dur ? ["-t", String(R.dur)] : []), "-vf", `fps=${fps},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`, "-q:v", "3", path.join(pasta, "%05d.jpg")], { stdio: "inherit" });
const nv = fs.readdirSync(pasta).length, n = nv + Math.round((R.extra || 0) * fps); R.frames = path.relative(raiz, pasta) + "/"; R.n = nv; R.fps = fps;
const rot = path.join(pasta, "..", path.basename(saida, ".mp4") + ".roteiro.json"); fs.writeFileSync(rot, JSON.stringify(R));
const tipos = { ".html": "text/html", ".json": "application/json", ".jpg": "image/jpeg", ".woff2": "font/woff2", ".png": "image/png", ".js": "text/javascript" };
const srv = http.createServer((q, r) => { const f = path.join(raiz, decodeURIComponent(q.url.split("?")[0])); if (!f.startsWith(raiz) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { "content-type": tipos[path.extname(f)] || "application/octet-stream" }); fs.createReadStream(f).pipe(r); });
await new Promise((ok) => srv.listen(0, ok));
const b = await pw.chromium.launch(), p = await b.newPage({ viewport: { width: 540, height: 960 } });
await p.goto(`http://127.0.0.1:${srv.address().port}/video/estilos/${estilo}.html?d=/${path.relative(raiz, rot)}`); await p.waitForFunction(() => window.pronto === true, null, { timeout: 60000 });
const temAudio = audio || spawnSync("ffprobe", ["-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", base]).stdout.toString().trim();
const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-", ...(audio ? ["-i", audio] : temAudio ? [...(R.ini ? ["-ss", String(R.ini)] : []), "-i", base] : []), ...(audio || temAudio ? ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", ...(R.extra ? ["-af", `apad=pad_dur=${R.extra}`] : ["-shortest"])] : []), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-maxrate", "4000k", "-bufsize", "8000k", "-preset", "medium", "-movflags", "+faststart", saida], { stdio: ["pipe", "inherit", "inherit"] });
for (let i = 0; i < n; i++) { const d = await p.evaluate(async (t) => { await window.quadro(t); return document.getElementById("c").toDataURL("image/jpeg", 0.92); }, i / fps); const buf = Buffer.from(d.split(",")[1], "base64"); if (!ff.stdin.write(buf)) await new Promise((ok) => ff.stdin.once("drain", ok)); if (i % 90 === 0) console.log(`${i}/${n}`); }
ff.stdin.end(); await new Promise((ok) => ff.on("close", ok)); await b.close(); srv.close(); fs.rmSync(pasta, { recursive: true, force: true }); console.log("✔", saida);
