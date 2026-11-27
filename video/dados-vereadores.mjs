// Números do vídeo "Raio-X da Câmara": vereadores 2020 × 2024 e o voto para governador de 2026 na base de cada um (TSE).
import { createRequire } from "module";
import fs from "fs";
const require = createRequire(import.meta.url);
global.window = {};
require("../data/ce/varjota.js");
const D = window.PLENARIA_DATA["ce/varjota"];
const ok = (x) => /^eleit/i.test(x.situacao || "");
const v20 = D.eleicoes["2020"].cargos.vereador, v24 = D.eleicoes["2024"].cargos.vereador, e24 = D.eleicoes["2024"], e26 = D.eleicoes["2026"];
const gov = e26.cargos.governador, ciro = gov.candidatos.find((x) => x.urna === "Ciro Gomes"), elmano = gov.candidatos.find((x) => x.urna === "Elmano de Freitas");
const valGov = {}; for (const x of gov.candidatos) for (const [s, v] of Object.entries(x.secoes || {})) valGov[s] = (valGov[s] || 0) + v;
const eleitos24 = v24.candidatos.filter(ok), eleitos20 = v20.candidatos.filter(ok);
const base = (x) => { // governador 2026 nas urnas onde o vereador teve voto em 2024 (peso = votos dele)
  let w = 0, el = 0, ci = 0, sec = 0;
  for (const [s, v] of Object.entries(x.secoes || {})) { if (!valGov[s]) continue; w += v; el += v * (elmano.secoes[s] || 0) / valGov[s]; ci += v * (ciro.secoes[s] || 0) / valGov[s]; sec++; }
  // local mais forte
  const porLocal = {}; for (const [s, v] of Object.entries(x.secoes || {})) { const l = e24.secoes[s] && e24.secoes[s].local; if (l) porLocal[l] = (porLocal[l] || 0) + v; }
  const [lid, lv] = Object.entries(porLocal).sort((a, b) => b[1] - a[1])[0] || [];
  let gl = 0, ge = 0; for (const [s, ss] of Object.entries(e26.secoes)) if (ss.local === lid) { gl += valGov[s] || 0; ge += elmano.secoes[s] || 0; }
  return { elmano: el / w, ciro: ci / w, reduto: lid ? { nome: e24.locais[lid].nome, bairro: e24.locais[lid].bairro, votos: lv, elmano26: gl ? ge / gl : null } : null };
};
const QE = Math.round(v24.totais.validos / 11);
const partidos = {}; eleitos24.forEach((x) => (partidos[x.partido] = (partidos[x.partido] || 0) + 1));
const out = {
  cadeiras: 11, candidatos24: v24.candidatos.length, candidatos20: v20.candidatos.length, validos24: v24.totais.validos, qe24: QE,
  partidos, renovados: eleitos24.filter((x) => !eleitos20.some((y) => y.pid === x.pid)).length,
  eleitos: eleitos24.map((x) => { const y = v20.candidatos.find((z) => z.pid === x.pid); return { urna: x.urna, partido: x.partido, votos: x.votos, situacao: x.situacao, foto: x.foto, v20: y ? y.votos : null, sit20: y ? y.situacao : null, ...base(x) }; }),
  cidade: { elmano: elmano.votos / gov.totais.validos, ciro: ciro.votos / gov.totais.validos, fotoElmano: elmano.foto, fotoCiro: ciro.foto },
};
fs.writeFileSync(new URL("./dados-vereadores.json", import.meta.url), JSON.stringify(out, null, 1));
console.log(out.cadeiras, out.candidatos24, out.qe24, out.partidos, "renovados", out.renovados, out.cidade);
out.eleitos.forEach((e) => console.log(e.urna.padEnd(22), e.partido, String(e.votos).padStart(5), String(e.v20 ?? "—").padStart(5), (e.sit20 || "").padEnd(16), "Elmano na base", (e.elmano * 100).toFixed(1), "| reduto", e.reduto.nome, e.reduto.votos, (e.reduto.elmano26 * 100).toFixed(1)));
