import { createRequire } from "module"; const require = createRequire(import.meta.url); const { chromium } = require("playwright"); import http from "http"; import fs from "fs"; import path from "path";
const D = "/home/claude/re/work/carro";
const tipos = { ".html": "text/html", ".js": "text/javascript", ".wasm": "application/wasm", ".data": "application/octet-stream", ".tflite": "application/octet-stream", ".binarypb": "application/octet-stream", ".jpg": "image/jpeg" };
const srv = http.createServer((q, r) => { const p = path.join(D, decodeURIComponent(q.url.split("?")[0])); if (!fs.existsSync(p)) { r.writeHead(404); return r.end(); } r.writeHead(200, { "Content-Type": tipos[path.extname(p)] || "application/octet-stream" }); fs.createReadStream(p).pipe(r); }).listen(8765);
const b = await chromium.launch(); const pg = await b.newPage(); await pg.goto("http://localhost:8765/seg.html"); await pg.waitForFunction("window.pronto");
const fs2 = fs.readdirSync(D + "/f").sort();
for (const [i, f] of fs2.entries()) { const u = await pg.evaluate((s) => window.mascara(s), "f/" + f); fs.writeFileSync(D + "/m/" + f.replace(".jpg", ".png"), Buffer.from(u.split(",")[1], "base64")); if (i % 100 === 0) console.log(i); }
await b.close(); srv.close(); console.log("DONE");
