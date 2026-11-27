// Números do raio-X "Yury do Paredão em Varjota (2026)" — só TSE (votação por seção, deputado federal 2026).
import { createRequire } from "module"; import fs from "fs";
const require = createRequire(import.meta.url); global.window = {}; require("../data/ce/varjota.js");
const D = window.PLENARIA_DATA["ce/varjota"], e = D.eleicoes["2026"], F = e.cargos.deputado_federal;
const C = [...F.candidatos].sort((a, b) => b.votos - a.votos), y = C.find((c) => /Yury/.test(c.urna));
const tot = {}; for (const c of F.candidatos) for (const [s, v] of Object.entries(c.secoes || {})) tot[s] = (tot[s] || 0) + v;
const loc = {}; for (const [s, t] of Object.entries(tot)) { const id = e.secoes[s].local, l = e.locais[id]; loc[id] = loc[id] || { nome: l.nome, bairro: l.bairro, lat: l.lat, lon: l.lon, v: 0, t: 0, urnas: 0 }; loc[id].v += y.secoes[s] || 0; loc[id].t += t; loc[id].urnas++; }
const locais = Object.values(loc).map((l) => ({ ...l, pct: l.v / l.t })).sort((a, b) => b.v - a.v);
const pcts = Object.keys(tot).map((s) => (y.secoes[s] || 0) / tot[s]).sort((a, b) => a - b);
const curto = (n) => n.replace(/^E\.?\s*e\.?\s*(i\.?)?\s*f\.?\s*/i, "").replace(/^Cheche Pro-inf[aâ]ncia /i, "Creche ").replace(/ - Varjota$/, "").trim();
const out = { urna: y.urna, partido: y.partido, foto: y.foto, votos: y.votos, validos: F.totais.validos, pct: y.votos / F.totais.validos,
  top3: C.slice(0, 3).map((c) => ({ urna: c.urna, partido: c.partido, votos: c.votos, foto: c.foto })),
  urnas: pcts.length, comVoto: Object.keys(y.secoes).length, min: pcts[0], mediana: pcts[Math.floor(pcts.length / 2)], max: pcts[pcts.length - 1],
  locais: locais.map((l) => ({ ...l, curto: curto(l.nome) })) };
fs.writeFileSync(new URL("./dados-yury.json", import.meta.url), JSON.stringify(out, null, 1));
console.log(out.votos, (out.pct * 100).toFixed(1), out.top3.map((c) => c.urna + " " + c.votos).join(" | "), out.comVoto, out.urnas);
out.locais.slice(0, 6).forEach((l) => console.log(l.v, (l.pct * 100).toFixed(1) + "%", l.curto, "|", l.bairro));
const mx = out.locais.reduce((a, b) => (b.pct > a.pct ? b : a)); console.log("maior %:", mx.curto, (mx.pct * 100).toFixed(1));
