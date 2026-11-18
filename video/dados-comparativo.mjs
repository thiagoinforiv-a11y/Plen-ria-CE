// MDB em Varjota, 2022 × 2026: federal (Eunício → Yury do Paredão) e estadual (Danniel Oliveira). Só TSE.
import { createRequire } from "module"; import fs from "fs";
const require = createRequire(import.meta.url); global.window = {}; require("../data/ce/varjota.js");
const D = window.PLENARIA_DATA["ce/varjota"];
const fix = (b) => b.replace(/Olho D.gua.*/i, "Olho d'Água dos Trajanos").replace(/Balneario/i, "Balneário").replace(/Acampamento Dnocs/i, "Acampamento DNOCS");
const cand = (ano, cargo, re) => D.eleicoes[ano].cargos[cargo].candidatos.find((x) => re.test(x.urna));
const fotoDe = (pid) => { let f = null; for (const a of Object.keys(D.eleicoes).sort()) for (const c of Object.values(D.eleicoes[a].cargos)) for (const x of c.candidatos) if (x.pid === pid && x.foto) f = x.foto; return f; };
const por = (ano, c) => { const e = D.eleicoes[ano], o = {}; for (const [s, v] of Object.entries(c.secoes || {})) { const l = e.locais[e.secoes[s].local], b = fix(l.bairro); o[b] = o[b] || { v: 0, lat: 0, lon: 0, n: 0 }; o[b].v += v; if (l.lat) { o[b].lat += l.lat; o[b].lon += l.lon; o[b].n++; } } return o; };
const E = cand("2022", "deputado_federal", /Eun[ií]cio/), Y = cand("2026", "deputado_federal", /Yury/), D2 = cand("2022", "deputado_estadual", /Danniel/), D6 = cand("2026", "deputado_estadual", /Danniel/);
const pE = por("2022", E), pY = por("2026", Y), pD2 = por("2022", D2), pD6 = por("2026", D6);
const bs = [...new Set([...Object.keys(pE), ...Object.keys(pY)])].filter((b) => !/n.o informado|contendas/i.test(b));
const bairros = bs.map((b) => { const g = pY[b] || pE[b]; return { b, e22: pE[b]?.v || 0, y26: pY[b]?.v || 0, d22: pD2[b]?.v || 0, d26: pD6[b]?.v || 0, lat: g.n ? g.lat / g.n : null, lon: g.n ? g.lon / g.n : null }; })
  .map((x) => ({ ...x, df: x.y26 - x.e22, de: x.d26 - x.d22 })).sort((a, b) => a.df - b.df);
const giord = (() => { const e = D.eleicoes["2026"], c = cand("2026", "deputado_federal", /Giordanna/); let v = 0; for (const [s, n] of Object.entries(c.secoes)) if (/Croat/.test(e.locais[e.secoes[s].local].bairro)) v += n; return { votos: v, foto: c.foto }; })();
const p = (c, ano, cargo) => ({ urna: c.urna, partido: c.partido, votos: c.votos, foto: c.foto || fotoDe(c.pid), pct: c.votos / D.eleicoes[ano].cargos[cargo].totais.validos });
const out = { eun: p(E, "2022", "deputado_federal"), yury: p(Y, "2026", "deputado_federal"), dan22: p(D2, "2022", "deputado_estadual"), dan26: p(D6, "2026", "deputado_estadual"), giordanna: giord, bairros };
fs.writeFileSync(new URL("./dados-comparativo.json", import.meta.url), JSON.stringify(out, null, 1));
console.log(out.eun.votos, out.yury.votos, out.dan22.votos, out.dan26.votos, out.eun.foto, out.dan26.foto, out.giordanna);
bairros.forEach((x) => console.log(x.b, x.df, x.de, x.lat ? "geo" : "SEM GEO"));
