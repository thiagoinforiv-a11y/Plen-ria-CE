// Grava video/cena.html quadro a quadro em MP4 (1080×1920).
// Uso: node video/gravar.mjs [saida.mp4] [fps]      ou   node video/gravar.mjs --provas pasta t1,t2,...
import { createRequire } from "module";
import http from "http";
import fs from "fs";
import path from "path";
import { spawn } from "child_process";
const require = createRequire(import.meta.url);
let pw; try { pw = require("playwright"); } catch { pw = require("/opt/node-tools/node_modules/playwright"); }
const raiz = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const tipos = { ".html": "text/html", ".json": "application/json", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".js": "text/javascript" };
const srv = http.createServer((q, r) => { const f = path.join(raiz, decodeURIComponent(q.url.split("?")[0])); if (!f.startsWith(raiz) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { "content-type": tipos[path.extname(f).toLowerCase()] || "application/octet-stream" }); fs.createReadStream(f).pipe(r); });
await new Promise((ok) => srv.listen(0, ok));
const argv = process.argv.slice(2), ic = argv.indexOf("--cena"), cena = ic >= 0 ? argv.splice(ic, 2)[1] : "cena.html";
const it = argv.indexOf("--trilha"), FX = it >= 0 ? JSON.parse(fs.readFileSync(argv.splice(it, 2)[1], "utf8")) : null; // pós-efeitos de imersão
const b = await pw.chromium.launch();
const p = await b.newPage({ viewport: { width: 540, height: 960 } });
await p.goto(`http://127.0.0.1:${srv.address().port}/video/${cena}`);
await p.waitForFunction(() => window.pronto === true, null, { timeout: 60000 });
const quadro = async (t) => Buffer.from((await p.evaluate(([t, fx]) => { window.render(t); if (fx && window.posEfeitos) window.posEfeitos(t, fx); return document.getElementById("c").toDataURL("image/jpeg", 0.93); }, [t, FX])).split(",")[1], "base64");
const args = argv;
if (args[0] === "--provas") {
  fs.mkdirSync(args[1], { recursive: true });
  for (const t of args[2].split(",").map(Number)) fs.writeFileSync(path.join(args[1], `t${String(t).padStart(5, "0")}.jpg`), await quadro(t));
} else {
  // opcional: --mapa mapa.json (tempo da animação × tempo do vídeo) e --audio trilha.wav
  const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : null; };
  const mapa = opt("--mapa"), audio = opt("--audio");
  const saida = args[0] || "varjota-raio-x.mp4", fps = +(args[1] || 30);
  const M = mapa ? JSON.parse(fs.readFileSync(mapa, "utf8")) : null;
  const dur = M ? M.V[M.V.length - 1] : await p.evaluate(() => window.DURACAO);
  const ts = (t) => { if (!M) return t; let k = 0; while (k + 2 < M.V.length && t >= M.V[k + 1]) k++; return Math.min(M.S[k + 1], M.S[k] + ((t - M.V[k]) * (M.S[k + 1] - M.S[k])) / (M.V[k + 1] - M.V[k])); };
  const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-", ...(audio ? ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"] : []), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", saida], { stdio: ["pipe", "inherit", "inherit"] });
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) { const buf = await quadro(ts(i / fps)); if (!ff.stdin.write(buf)) await new Promise((ok) => ff.stdin.once("drain", ok)); if (i % 300 === 0) console.log(`${i}/${n}`); }
  ff.stdin.end(); await new Promise((ok) => ff.on("close", ok));
  console.log("✔", saida);
}
await b.close(); srv.close();
