// Um vídeo por vereador (collab, 20–30 s): só dados públicos do TSE, tom neutro, sem partido nem grupo.
// Uso: node video/vereador.mjs ce/<cidade>  → pautas em video/noticias/ver-<cidade>-<nome>.json + falas em narracao.json
//      depois: narração (Action) e node video/noticia.mjs video/noticias/ver-<cidade>-<nome>.json
import fs from "fs";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
global.window = {};
const ID = process.argv[2] || "ce/varjota", SLUG = ID.split("/")[1];
require(`../data/${ID}.js`);
const D = window.PLENARIA_DATA[ID], CID = D.meta.municipio || D.meta.nome;
const v24 = D.eleicoes["2024"].cargos.vereador;

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


const eleito = (x) => /^eleit/i.test(x.situacao || ""), supl = (x) => /^suplente/i.test(x.situacao || "");
const ORD = ["", "primeira", "segunda", "terceira", "quarta", "quinta", "sexta", "sétima", "oitava", "nona", "décima", "décima primeira", "décima segunda", "décima terceira", "décima quarta", "décima quinta"];
const ORDM = ["", "primeiro", "segundo", "terceiro", "quarto", "quinto", "sexto", "sétimo", "oitavo", "nono", "décimo"];
const ANOS = ["2000", "2004", "2008", "2012", "2016", "2020"];
const anoExt = (a) => "dois mil" + (+a % 100 ? " e " + ext(+a % 100) : "");
const pct = (p) => { const [i, d] = p.toFixed(1).split("."); return { txt: `${i},${d}%`, fala: `${ext(+i)}${d !== "0" ? " vírgula " + ext(+d) : ""} por cento` }; };
const ord = [...v24.candidatos].sort((a, b) => b.votos - a.votos), VAL = v24.totais.validos;
const slug = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

const ids = [];
for (const x of v24.candidatos.filter(eleito).sort((a, b) => b.votos - a.votos)) {
  const N = nome(x), f = fem(x), ver = f ? "vereadora" : "vereador", pos = ord.indexOf(x) + 1, p = pct((100 * x.votos) / VAL);
  const hist = ANOS.map((a) => { const c = D.eleicoes[a]?.cargos?.vereador?.candidatos.find((z) => z.pid === x.pid); return c && { a, c }; }).filter(Boolean);
  const mand = hist.filter((h) => eleito(h.c)).length + 1;
  const cenas = [
    { midia: x.foto, credito: "Foto: TSE", tarja: `${N}, ${ver} de ${CID}`,
      fala: `${N}, ${ver} de ${CID}. Os números da eleição, direto do TSE.` },
    { grande: `${fmt(x.votos)} VOTOS`, sub: pos === 1 ? "A MAIOR VOTAÇÃO" : pos < ORD.length ? `${pos}ª MAIOR VOTAÇÃO` : "VAGA PELA SOMA DO PARTIDO", tarja: `${fmt(x.votos)} votos em 2024`,
      fala: pos < ORD.length ? `Em dois mil e vinte e quatro, teve ${ext(x.votos)} votos: ${pos === 1 ? "a maior votação" : `a ${ORD[pos]} maior votação`} entre ${ext(ord.length)} candidatos.`
        : `Em dois mil e vinte e quatro, teve ${ext(x.votos)} votos e ficou com a vaga pela soma dos votos do partido.` },
    { grande: p.txt, sub: "DOS VOTOS VÁLIDOS", tarja: `${p.txt} dos votos válidos para vereador`,
      fala: `Isso dá ${p.fala} dos votos válidos para vereador na cidade.` },
  ];
  if (hist.length) {
    const u = hist[hist.length - 1], st = eleito(u.c) ? (f ? "foi eleita" : "foi eleito") : supl(u.c) ? "ficou como suplente" : (f ? "não foi eleita" : "não foi eleito");
    const dif = x.votos - u.c.votos;
    cenas.push({ grande: u.a, sub: `${fmt(u.c.votos)} VOTOS`, tarja: `Em ${u.a}: ${fmt(u.c.votos)} votos`,
      fala: `Na disputa anterior, em ${anoExt(u.a)}, ${st} com ${ext(u.c.votos)} votos.` + (dif ? ` Agora, ${ext(Math.abs(dif))} ${Math.abs(dif) === 1 ? "voto" : "votos"} a ${dif > 0 ? "mais" : "menos"}.` : "") });
  } else cenas.push({ grande: "1ª VEZ", sub: "NA DISPUTA", tarja: "Primeira candidatura a vereador na cidade (desde 2000)",
    fala: `Foi a primeira vez como candidat${f ? "a" : "o"} a vereador em ${CID}, nos dados do TSE desde dois mil.` });
  cenas.push({ grande: "2025–2028", sub: mand > 1 && mand <= 10 ? `${ORDM[mand].toUpperCase()} MANDATO` : "MANDATO", tarja: "Siga @plenariace: todos os vereadores, um por um",
    fala: (mand > 1 && mand <= 10 ? `Cumpre o ${ORDM[mand]} mandato, até dois mil e vinte e oito.` : `Mandato até dois mil e vinte e oito.`) + " Siga para conhecer todos os vereadores." });
  const id = `ver-${SLUG}-${slug(N)}`;
  fs.writeFileSync(new URL(`./noticias/${id}.json`, import.meta.url), JSON.stringify({ id, tempo: 1.35, fontes: "Fonte: TSE, eleições 2000 a 2024", cenas }, null, 1) + "\n");
  const nf = new URL("./narracao.json", import.meta.url), NN = JSON.parse(fs.readFileSync(nf)); NN.videos[id] = cenas.map((c) => c.fala); fs.writeFileSync(nf, JSON.stringify(NN, null, 2) + "\n");
  ids.push(id); console.log("\n" + id); cenas.forEach((c) => console.log(" -", c.fala));
}
