// Junta os números do vídeo a partir dos dados oficiais (TSE) já carregados no projeto.
import { createRequire } from "module";
import fs from "fs";
const require = createRequire(import.meta.url);
global.window = {};
require("../data/ce/varjota.js");
const D = window.PLENARIA_DATA["ce/varjota"];
const porLocal = (ano, cargo) => {
  const e = D.eleicoes[ano], c = e.cargos[cargo], L = {};
  for (const [sid, s] of Object.entries(e.secoes)) { const l = (L[s.local] ||= { id: s.local, ...e.locais[s.local], aptos: 0, urnas: 0, validos: 0, cand: {} }); l.aptos += s.aptos || 0; l.urnas++; }
  for (const x of c.candidatos) for (const [sid, v] of Object.entries(x.secoes || {})) { const l = L[e.secoes[sid].local]; l.cand[x.urna] = (l.cand[x.urna] || 0) + v; l.validos += v; }
  return { L, c };
};
const pearson = (a, b) => { const n = a.length, ma = a.reduce((s, x) => s + x, 0) / n, mb = b.reduce((s, x) => s + x, 0) / n; let num = 0, da = 0, db = 0; for (let i = 0; i < n; i++) { num += (a[i] - ma) * (b[i] - mb); da += (a[i] - ma) ** 2; db += (b[i] - mb) ** 2; } return num / Math.sqrt(da * db); };
const pf = porLocal("2024", "prefeito"), gv = porLocal("2026", "governador"), est = porLocal("2026", "deputado_estadual"), fed = porLocal("2026", "deputado_federal");
const tot = (c) => c.totais ? c.totais.validos : c.candidatos.reduce((s, x) => s + x.votos, 0);
const cand = (c, n) => c.candidatos.find((x) => x.urna === n);
const g22 = porLocal("2022", "governador");
const ids = Object.keys(gv.L).filter((id) => pf.L[id] && pf.L[id].validos && gv.L[id].validos);
const pts = ids.map((id) => ({ id, nome: gv.L[id].nome, bairro: gv.L[id].bairro, lat: gv.L[id].lat, lon: gv.L[id].lon, aptos: gv.L[id].aptos, urnas: gv.L[id].urnas,
  elmo24: pf.L[id].cand["Elmo Monte"] / pf.L[id].validos, elmano26: (gv.L[id].cand["Elmano de Freitas"] || 0) / gv.L[id].validos, ciro26: (gv.L[id].cand["Ciro Gomes"] || 0) / gv.L[id].validos,
  lia26: (est.L[id].cand["Lia Gomes"] || 0) / (est.L[id].validos || 1),
  elmano22: g22.L[id] && g22.L[id].validos ? (g22.L[id].cand["Elmano de Freitas"] || 0) / g22.L[id].validos : null }));
const p22 = pts.filter((p) => p.elmano22 != null);
const e26 = D.eleicoes["2026"], aptos26 = Object.values(e26.secoes).reduce((s, x) => s + (x.aptos || 0), 0);
const maior = [...pts].sort((a, b) => b.aptos - a.aptos)[0];
const pref = D.eleicoes["2024"].cargos.prefeito, gov = e26.cargos.governador;
const out = {
  cidade: "Varjota", aptos26, secoes26: Object.keys(e26.secoes).length, locais26: Object.keys(e26.locais).length,
  anos: Object.keys(D.eleicoes).filter((a) => D.eleicoes[a].nivel === "secao"),
  prefeito24: pref.candidatos.slice(0, 2).map((x) => ({ nome: x.urna, votos: x.votos, pct: x.votos / tot(pref), foto: x.foto })),
  governador26: gov.candidatos.slice(0, 2).map((x) => ({ nome: x.urna, votos: x.votos, pct: x.votos / tot(gov), foto: x.foto })),
  r_elmo_elmano: pearson(pts.map((p) => p.elmo24), pts.map((p) => p.elmano26)),
  elmano22: (() => { const c = D.eleicoes["2022"].cargos.governador; const x = cand(c, "Elmano de Freitas"); return { votos: x.votos, pct: x.votos / tot(c) }; })(),
  r_elmano22_26: pearson(p22.map((p) => p.elmano22), p22.map((p) => p.elmano26)),
  r_lia_elmano: pearson(pts.map((p) => p.lia26), pts.map((p) => p.elmano26)),
  pontos: pts, maior,
  lia: (({ urna, votos, foto }) => ({ nome: urna, votos, foto }))(cand(e26.cargos.deputado_estadual, "Lia Gomes")),
  yury: (({ urna, votos, foto }) => ({ nome: urna, votos, foto }))(cand(e26.cargos.deputado_federal, "Yury do Paredão")),
  rosa: (({ urna, votos, foto }) => ({ nome: urna, votos, foto }))(cand(D.eleicoes["2024"].cargos.vereador, "Rosa Paulino")),
  comp26: (() => { const v = gov.candidatos.reduce((s, x) => s + x.votos, 0) + gov.totais.brancos + gov.totais.nulos; return v; })(),
};
fs.writeFileSync(new URL("./dados.json", import.meta.url), JSON.stringify(out, null, 1));
console.log({ ...out, pontos: out.pontos.length });
