// Série curta — Parte 2 "As surpresas": só dados públicos do TSE (2020 e 2024), tom neutro, sem partidos nem grupos.
// Gera a pauta do vídeo-notícia (video/noticias/curta2-<cidade>.json) e a fala em narracao.json (mesma chave).
// Uso: node video/curta2.mjs ce/<cidade>   → depois: narração (Action) e node video/noticia.mjs video/noticias/curta2-<cidade>.json
import fs from "fs";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
global.window = {};
const ID = process.argv[2] || "ce/varjota", SLUG = ID.split("/")[1];
require(`../data/${ID}.js`);
const D = window.PLENARIA_DATA[ID], CID = D.meta.municipio || D.meta.nome;
const v24 = D.eleicoes["2024"].cargos.vereador, v20 = D.eleicoes["2020"].cargos.vereador;

// ---------- números por extenso (mesmas regras dos outros roteiros)
const U = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"];
const DZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"];
const CT = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"];
const ate999 = (k) => { if (k < 20) return U[k]; if (k < 100) return DZ[Math.floor(k / 10)] + (k % 10 ? " e " + U[k % 10] : ""); if (k === 100) return "cem"; return CT[Math.floor(k / 100)] + (k % 100 ? " e " + ate999(k % 100) : ""); };
const ext = (k) => { k = Math.round(k); if (k < 1000) return ate999(k); const m = Math.floor(k / 1000), r = k % 1000; const mil = m === 1 ? "mil" : ate999(m) + " mil"; if (!r) return mil; return mil + (r < 100 || r % 100 === 0 ? " e " : " ") + ate999(r); };
const Cap = (s) => s[0].toUpperCase() + s.slice(1);
const fmt = (k) => k.toLocaleString("pt-BR");
const ACENTOS = { Joao: "João", Junior: "Júnior", Anastacio: "Anastácio", Conceicao: "Conceição", Araujo: "Araújo", Flavio: "Flávio", Debora: "Débora" };
const nome = (x) => x.urna.replace(/\b[A-Za-z]+\b/g, (w) => ACENTOS[w] || w);
const fem = (x) => x.genero === "feminino";

// ---------- os fatos (só "suplente" conta como "ficou de fora": "não eleito" pode ter candidatura com pendência)
const eleito = (x) => /^eleit/i.test(x.situacao || ""), supl = (x) => /^suplente/i.test(x.situacao || "");
const E = v24.candidatos.filter(eleito), n = E.length;
const ultimo = E.reduce((a, b) => (b.votos < a.votos ? b : a));
const S = v24.candidatos.filter(supl).sort((a, b) => b.votos - a.votos), topS = S[0];
const acima = S.filter((x) => x.votos > ultimo.votos);
// sem suplente acima do último eleito: o suplente mais perto da vaga do próprio partido
const quase = S.map((s) => { const m = E.filter((e) => e.partido === s.partido); if (!m.length) return null; const u = m.reduce((a, b) => (b.votos < a.votos ? b : a)); return { s, u, dif: u.votos - s.votos }; })
  .filter(Boolean).sort((a, b) => a.dif - b.dif)[0];
const E20 = v20.candidatos.filter(eleito), tent = E20.map((x) => v24.candidatos.find((z) => z.pid === x.pid)).filter(Boolean), perd = tent.filter((x) => !eleito(x));
const novos = E.filter((x) => !E20.some((z) => z.pid === x.pid)).sort((a, b) => b.votos - a.votos), nv = novos[0];
const top = E.reduce((a, b) => (b.votos > a.votos ? b : a));
for (const x of [topS, ultimo, nv, quase && quase.s, quase && quase.u].filter(Boolean)) if (!fs.existsSync(new URL("../" + x.foto, import.meta.url))) throw new Error("sem foto: " + x.urna);

const cenas = [];
if (acima.length) {
  cenas.push({ grande: `${fmt(topS.votos)} VOTOS`, sub: "E FICOU DE FORA", tarja: `Parte 2: as surpresas da eleição em ${CID}`,
    fala: `${Cap(ext(topS.votos))} votos, e ficou de fora da Câmara de ${CID}. As surpresas da eleição de vereador.` });
  cenas.push({ midia: topS.foto, credito: "Foto: TSE", tarja: `${nome(topS)}: ${fmt(topS.votos)} votos, suplente`,
    fala: `${nome(topS)} teve ${ext(topS.votos)} votos e ficou como suplente.` });
  cenas.push({ midia: ultimo.foto, credito: "Foto: TSE", tarja: `${nome(ultimo)}: ${fem(ultimo) ? "eleita" : "eleito"} com ${fmt(ultimo.votos)} votos`,
    fala: `${nome(ultimo)} se elegeu com ${ext(ultimo.votos)}.` + (acima.length > 1 ? ` Ao todo, ${ext(acima.length)} suplentes tiveram mais votos que ${fem(ultimo) ? "ela" : "ele"}.` : "") });
} else {
  const { s, u, dif } = quase;
  cenas.push({ grande: `${fmt(dif)} ${dif === 1 ? "VOTO" : "VOTOS"}`, sub: "SEPAROU A VAGA", tarja: `Parte 2: as surpresas da eleição em ${CID}`,
    fala: `${Cap(ext(dif))} ${dif === 1 ? "voto" : "votos"}. Foi o que separou uma vaga na Câmara de ${CID}. As surpresas da eleição de vereador.` });
  cenas.push({ midia: s.foto, credito: "Foto: TSE", tarja: `${nome(s)}: ${fmt(s.votos)} votos, suplente`,
    fala: `${nome(s)} teve ${ext(s.votos)} votos e ficou como suplente.` });
  cenas.push({ midia: u.foto, credito: "Foto: TSE", tarja: `${nome(u)}: ${fem(u) ? "eleita" : "eleito"} com ${fmt(u.votos)} votos`,
    fala: `${nome(u)}, do mesmo partido, ficou com a vaga: ${ext(u.votos)} votos.` });
}
cenas.push({ grande: "PARTIDO", sub: "PRIMEIRO A SOMA DOS VOTOS", tarja: "Vagas vão primeiro aos partidos, depois aos mais votados de cada um",
  fala: "Por quê? As vagas vão primeiro para os partidos, pela soma dos votos. Depois, para os mais votados de cada um." });
if (perd.length) cenas.push({ grande: `${perd.length} DE ${tent.length}`, sub: perd.length === 1 ? "NÃO VOLTOU" : "NÃO VOLTARAM", tarja: `${Cap(ext(perd.length))} ${perd.length === 1 ? "vereador não voltou" : "vereadores não voltaram"} à Câmara`,
  fala: `Dos ${ext(E20.length)} eleitos em dois mil e vinte, ${ext(tent.length)} tentaram de novo. ${Cap(ext(perd.length))} não ${perd.length === 1 ? "voltou" : "voltaram"}.` });
if (nv) cenas.push({ midia: nv.foto, credito: "Foto: TSE", tarja: `${nome(nv)}: ${fmt(nv.votos)} votos${nv === top ? `, ${fem(nv) ? "a mais votada" : "o mais votado"}` : ""}`,
  fala: `Entre os ${ext(novos.length)} que chegaram agora, ${fem(nv) ? "a mais votada" : "o mais votado"} foi ${nome(nv)}: ${ext(nv.votos)} votos` + (nv === top ? `, a maior votação da cidade.` : ".") });
cenas.push({ grande: "?", sub: "QUAL VOCÊ NÃO ESPERAVA", tarja: "Qual dessas surpresas você não esperava? Comenta aqui",
  fala: "Qual você não esperava? Comenta aqui." });

const id = `curta2-${SLUG}`, pauta = { id, tempo: 1.35, fontes: "Fonte: TSE, eleições 2020 e 2024", cenas };
fs.mkdirSync(new URL("./noticias/", import.meta.url), { recursive: true });
fs.writeFileSync(new URL(`./noticias/${id}.json`, import.meta.url), JSON.stringify(pauta, null, 1) + "\n");
const nf = new URL("./narracao.json", import.meta.url), N = JSON.parse(fs.readFileSync(nf)); N.videos[id] = cenas.map((c) => c.fala); fs.writeFileSync(nf, JSON.stringify(N, null, 2) + "\n");
console.log(id); cenas.forEach((c, i) => console.log(i, c.fala));
