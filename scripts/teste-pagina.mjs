#!/usr/bin/env node
// Teste de fumaça: abre a página num navegador sem tela e falha se houver erro de JavaScript
// ou se as seções principais não renderizarem. Roda no GitHub Actions e no pre-commit (se houver Playwright).
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const req = createRequire(import.meta.url);
let chromium;
for (const m of ["playwright", "/opt/node-tools/node_modules/playwright"]) { try { ({ chromium } = req(m)); break; } catch (e) { /* tenta o próximo */ } }
if (!chromium) { console.log("(Playwright não instalado: teste da página pulado)"); process.exit(0); }

const tipos = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg" };
const srv = http.createServer((q, r) => {
  const f = path.join(RAIZ, decodeURIComponent(q.url.split("?")[0]) === "/" ? "index.html" : decodeURIComponent(q.url.split("?")[0]));
  if (!f.startsWith(RAIZ) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { "content-type": tipos[path.extname(f)] || "application/octet-stream" }); fs.createReadStream(f).pipe(r);
}).listen(0);
const url = `http://localhost:${srv.address().port}/`;
const erros = [];
const b = await chromium.launch(fs.existsSync("/opt/pw-browsers/chromium") ? {} : {});
for (const vp of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
  const p = await b.newPage({ viewport: vp });
  p.on("pageerror", (e) => erros.push(`${vp.width}px: ${e.message}`));
  await p.addInitScript(() => localStorage.setItem("plenaria.intro.v1", "1"));
  await p.goto(url); await p.waitForTimeout(1500);
  const r = await p.evaluate(() => ({
    falhou: document.body.innerText.includes("Não foi possível carregar"),
    titulo: (document.querySelector("#hero-title") || {}).textContent || "",
    secoes: ["quem", "ficha", "ranking", "trajetoria", "historico"].filter((id) => !(document.getElementById(id) || {}).innerHTML),
    largura: document.documentElement.scrollWidth,
  }));
  if (r.falhou) erros.push(`${vp.width}px: página mostrou "Não foi possível carregar os dados"`);
  if (!r.titulo) erros.push(`${vp.width}px: título vazio`);
  if (r.secoes.length) erros.push(`${vp.width}px: seções vazias: ${r.secoes.join(", ")}`);
  if (r.largura > vp.width + 2) erros.push(`${vp.width}px: rolagem horizontal (${r.largura}px)`);
  await p.close();
}
await b.close(); srv.close();
for (const e of erros) console.log("ERRO   " + e);
console.log(erros.length ? `✘ Página com ${erros.length} problema(s).` : "✔ Página abre sem erros (computador e celular).");
process.exit(erros.length ? 1 : 0);
