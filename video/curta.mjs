// Série curta (30–45 s) para redes — Parte 1 "Os números da Câmara": só dados públicos do TSE, tom neutro,
// sem grupos, sem partidos e sem "quem manda" (período de eleição da Mesa da Câmara).
// Uso: node video/curta.mjs ce/<cidade>   → video/curta-<cidade>.json e a fala em narracao.json (chave curta1-<cidade>)
import fs from "fs";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const ID = process.argv[2] || "ce/varjota", SLUG = ID.split("/")[1];
const ARQ = SLUG === "varjota" ? "dados-vereadores-detalhe.json" : `dados-vereadores-${SLUG}.json`;
const V = JSON.parse(fs.readFileSync(new URL("./" + ARQ, import.meta.url)));
const H = JSON.parse(fs.readFileSync(new URL(`./historico-${SLUG}.json`, import.meta.url)));
const CID = V.municipio, n = V.eleitos.length;

// ---------- números por extenso (mesmas regras dos outros roteiros)
const U = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"];
const DZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"];
const CT = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"];
const ate999 = (k) => { if (k < 20) return U[k]; if (k < 100) return DZ[Math.floor(k / 10)] + (k % 10 ? " e " + U[k % 10] : ""); if (k === 100) return "cem"; return CT[Math.floor(k / 100)] + (k % 100 ? " e " + ate999(k % 100) : ""); };
const ext = (k) => { k = Math.round(k); if (k < 1000) return ate999(k); const m = Math.floor(k / 1000), r = k % 1000; const mil = m === 1 ? "mil" : ate999(m) + " mil"; if (!r) return mil; return mil + (r < 100 || r % 100 === 0 ? " e " : " ") + ate999(r); };
const anoExt = (a) => "dois mil e " + ate999(+a - 2000);
const Cap = (s) => s[0].toUpperCase() + s.slice(1);

// ---------- quem disputou as duas eleições: renovação e maior crescimento
const reeleitos = V.eleitos.filter((e) => e.eleito20), novos = n - reeleitos.length;
const top = V.eleitos.reduce((a, b) => (b.votos > a.votos ? b : a));
const comV20 = V.eleitos.filter((e) => e.v20 && e !== top).sort((a, b) => b.votos / b.v20 - a.votos / a.v20);
const cresceu = comV20[0] && comV20[0].votos > comV20[0].v20 ? comV20[0] : null;
const r20 = (H.renov || []).find((r) => r.ano === "2024");

// presidente da Câmara: só se estiver nos relatórios com fonte "confirmado" (sem datas de mandato no vídeo)
global.window = {}; try { require(`../data/${ID}.relatorios.js`); } catch (er) {}
const REL = ((window.PLENARIA_RELATORIOS || {})[ID] || {}).pessoas || Object.values((window.PLENARIA_RELATORIOS || {})[ID] || {}).find(Array.isArray) || [];
const pres = REL.find((r) => /^Presidente da Câmara/i.test(r.papel || "") && (r.destaques || []).some((d) => d.selo === "confirmado" && /Presidente da Câmara/i.test(d.titulo)));
const presE = pres && V.eleitos.find((e) => pres.nomes.includes(e.urna));
const out = {
  video: "curta1", S: [0, 4.5, 10, 15.5, 21, 28, 34], municipio: CID, cd_ibge: V.cd_ibge || H.cd_ibge, cadeiras: n, candidatos: V.candidatos, validos: V.validos, qe: V.qe,
  eleitos: [...V.eleitos].sort((a, b) => b.votos - a.votos).map((e) => ({ urna: e.urna, foto: e.foto, votos: e.votos, eleito20: !!e.eleito20, v20: e.v20 })),
  reeleitos: reeleitos.length, novos, eleitos20: r20 ? r20.cadeiras : n,
  presidente: presE ? { urna: presE.urna, foto: presE.foto } : null,
  top: { urna: top.urna, foto: top.foto, votos: top.votos },
  cresceu: cresceu && { urna: cresceu.urna, foto: cresceu.foto, votos: cresceu.votos, v20: cresceu.v20, mult: cresceu.votos / cresceu.v20 },
};
const multFala = (m) => (m >= 2 ? "mais que dobrou" : m >= 1.9 ? "quase dobrou" : `cresceu ${ext(Math.round((m - 1) * 100))} por cento`);
out.fala = [
  `${Cap(ext(V.candidatos))} candidatos, ${ext(n)} cadeiras. Quanto vale uma vaga na Câmara de ${CID}?`,
  `${Cap(ext(V.qe))} votos por cadeira. É o quociente eleitoral.`,
  `Esses são os ${ext(n)} eleitos de ${anoExt(2024)}.`,
  `${Cap(ext(novos))} não tinham sido eleitos em ${anoExt(2020)}.`,
  `Maior votação: ${top.urna}.` + (cresceu ? ` E ${cresceu.urna} ${multFala(out.cresceu.mult)} de voto.` : ""),
  presE ? `Hoje, quem preside a Câmara é ${presE.urna}. E o próximo presidente, quem será? Comenta aqui.` : `Qual vereador você quer ver no próximo vídeo? Comenta aqui.`,
];
fs.writeFileSync(new URL(`./curta-${SLUG}.json`, import.meta.url), JSON.stringify(out, null, 1));
const nf = new URL("./narracao.json", import.meta.url), N = JSON.parse(fs.readFileSync(nf)); N.videos[`curta1-${SLUG}`] = out.fala; fs.writeFileSync(nf, JSON.stringify(N, null, 2) + "\n");
out.fala.forEach((f, i) => console.log(i, f));
// trilha de efeitos (tempos da animação de cena-curta.html; o mixador estica cada cena para caber a fala)
const S = out.S;
fs.writeFileSync(new URL(`./trilha-curta1-${SLUG}.json`, import.meta.url), JSON.stringify({
  video: `curta1-${SLUG}`, S, tempo: 1.12, boom: [0.15, S[5] + 0.2], impactos: [2.3, S[1] + 1.4, S[3] + 1.2], riser: null, radar: null,
  ticks: [[0.1, 1.2], [S[1] + 1.4, S[1] + 3.0], [S[2] + 1.2, S[2] + 3.0]], bips: [S[3] + 1.8, S[3] + 2.05, S[3] + 2.3], urna: [S[5] + 1.2],
  pops: [S[4] + 0.4, S[4] + 3.5], swells: [[S[4] + 0.6, 196], [S[5] + 0.4, 220]],
  intensidade: [[0, 0.6], [S[1], 0.55], [S[2], 0.7], [S[3], 0.75], [S[4], 0.8], [S[5], 0.6]],
}, null, 1));
