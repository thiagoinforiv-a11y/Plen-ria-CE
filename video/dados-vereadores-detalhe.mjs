// Números do vídeo "Os vereadores, um por um" de qualquer cidade (TSE 2020 e 2024, votação por local).
// Uso: node video/dados-vereadores-detalhe.mjs ce/<cidade>   (sem argumento = Varjota, arquivo dados-vereadores-detalhe.json)
import { createRequire } from "module";
import fs from "fs";
const require = createRequire(import.meta.url);
global.window = {};
const ID = process.argv[2] || "ce/varjota", SLUG = ID.split("/")[1];
require(`../data/${ID}.js`);
const D = window.PLENARIA_DATA[ID], CID = D.meta.municipio || D.meta.nome;
const ARQ = SLUG === "varjota" ? "dados-vereadores-detalhe.json" : `dados-vereadores-${SLUG}.json`, CHAVE = SLUG === "varjota" ? "vereadores-detalhe" : `vereadores-${SLUG}`;
// --- nomes: acentos que o TSE às vezes omite, partidos por extenso, escola sem sigla
const ACENTOS = { Joao: "João", Sao: "São", Jose: "José", Placido: "Plácido", Gracas: "Graças", Araujo: "Araújo", Anastacio: "Anastácio", Cesario: "Cesário", Flavio: "Flávio", Feijao: "Feijão", Medio: "Médio", Patrocinio: "Patrocínio", Marcio: "Márcio", Liduina: "Liduína", Vinicius: "Vinícius", Junior: "Júnior", Mororo: "Mororó", Conceicao: "Conceição", Sebastiao: "Sebastião", Fatima: "Fátima", Antonio: "Antônio", Candido: "Cândido", Inacia: "Inácia", Tiburcio: "Tibúrcio", Lucia: "Lúcia", Vitoria: "Vitória", Gloria: "Glória", Quiteria: "Quitéria", Mons: "Monsenhor" };
const acento = (t) => String(t || "").replace(/\bMons\./g, "Monsenhor").replace(/\b[A-Za-z]+\b/g, (w) => ACENTOS[w] || w);
const PARTIDO = { "UNIÃO": "União", REPUBLICANOS: "Republicanos", CIDADANIA: "Cidadania", PODE: "Podemos", AVANTE: "Avante", SOLIDARIEDADE: "Solidariedade", NOVO: "Novo", PATRIOTA: "Patriota", AGIR: "Agir", MOBILIZA: "Mobiliza", PCdoB: "PC do B" };
const partido = (p) => PARTIDO[p] || p;
const SIGLA = /^(escola|municipal|estadual|de|do|da|ensino|fundamental|m[eé]dio|infantil|e|eief|emeb|eeief|eeef|emef|emeif|eem|eef|eeem|eeefm|e\.?)$/i;
const escola = (n) => { let w = acento(n).split(/\s+-\s+|-(?=[A-Z])/)[0].trim().split(/\s+/), i = 0;
  while (i < w.length - 1 && (SIGLA.test(w[i]) || /^([A-Za-z]\.){1,5}[A-Za-z]?\.?$/.test(w[i]) || /^E[eifmtbpa]{1,5}$/i.test(w[i]))) i++;
  const r = w.slice(i).join(" "); return r || n; };
const localFala = (n) => { const r = escola(n); return /^(centro|liceu|col[eé]gio|n[uú]cleo|instituto|grupo)\b/i.test(r) ? (/^col/i.test(r) ? "no " : /^n[uú]cleo|^instituto|^grupo|^centro|^liceu/i.test(r) ? "no " : "na ") + r : "na escola " + r; };
const ondeBairro = (b) => { b = acento(b).replace(/^N\.\s?s\.\s?/i, "Nossa Senhora ").replace(/\bDe\b/g, "de"); if (/^(distrito|sede|zona rural|rural|interior)$/i.test(b)) return ""; if (b === "Centro") return "no Centro"; if (b === "Acampamento Dnocs") return "no Acampamento do Dnocs";
  if (/^(distrito|assentamento|s[ií]tio|vila|povoado|conjunto|bairro)\b/i.test(b)) return "no " + b[0].toLowerCase() + b.slice(1); return "em " + b; };
const ok = (x) => /^eleit/i.test(x.situacao || "");
const e24 = D.eleicoes["2024"], v24 = e24.cargos.vereador, v20 = D.eleicoes["2020"].cargos.vereador;
const eleitos = v24.candidatos.filter(ok), eleitos20 = v20.candidatos.filter(ok);
const L = e24.locais, lids = Object.keys(L).filter((l) => Object.values(e24.secoes).some((x) => x.local === l));
const porLocal = (x) => { const o = {}; for (const [s, v] of Object.entries(x.secoes || {})) { const l = e24.secoes[s] && e24.secoes[s].local; if (l) o[l] = (o[l] || 0) + v; } return o; };
const PL = new Map(v24.candidatos.map((x) => [x.sq, porLocal(x)]));
// em cada local, qual vereador (entre todos os candidatos) foi o mais votado
const lider = {}; for (const l of lids) { let best = null, bv = -1; for (const x of v24.candidatos) { const v = PL.get(x.sq)[l] || 0; if (v > bv) { bv = v; best = x.sq; } } lider[l] = best; }
const NC = eleitos.length, QE = Math.round(v24.totais.validos / NC);
const ranking = v24.candidatos.map((x) => x.sq);
const out = {
  municipio: CID, cd_ibge: D.meta.cd_ibge, cadeiras: NC, validos: v24.totais.validos, qe: QE, nlocais: lids.length, candidatos: v24.candidatos.length,
  locais: lids.map((l) => ({ id: l, nome: L[l].nome, curto: escola(L[l].nome), bairro: L[l].bairro, lat: L[l].lat, lon: L[l].lon })).filter((l) => l.lat != null),
  eleitos: eleitos.map((x) => {
    const pl = PL.get(x.sq), lista = Object.entries(pl).sort((a, b) => b[1] - a[1]);
    const y0 = v20.candidatos.find((z) => z.pid === x.pid), y = y0 && (y0.votos >= 50 || ok(y0)) ? y0 : null, y20 = y0;
    return {
      urna: acento(x.urna), partido: partido(x.partido), foto: x.foto, votos: x.votos, pos: ranking.indexOf(x.sq) + 1, pct: x.votos / v24.totais.validos,
      situacao: x.situacao, qp: /qp/.test(x.situacao || ""),
      v20: y ? y.votos : null, eleito20: y ? ok(y) : false, disputou20: !!y20,
      locais: lista.map(([l, v]) => [l, v]), top: lista.slice(0, 3).map(([l, v]) => ({ nome: L[l].nome, curto: escola(L[l].nome), bairro: L[l].bairro, votos: v })),
      conc: lista.length ? lista[0][1] / x.votos : 0, top3: lista.slice(0, 3).reduce((t, [, v]) => t + v, 0) / x.votos,
      venceu: lids.filter((l) => lider[l] === x.sq).length, presente: lista.filter(([, v]) => v > 0).length,
    };
  }),
};
fs.writeFileSync(new URL("./" + ARQ, import.meta.url), JSON.stringify(out, null, 1));
console.log("QE", QE, "locais", lids.length, "candidatos", out.candidatos);
out.eleitos.forEach((e) => console.log(String(e.pos).padStart(2), e.urna.padEnd(20), e.partido.padEnd(4), String(e.votos).padStart(5), (e.pct * 100).toFixed(1) + "%", "20:", String(e.v20 ?? "—").padStart(5), e.eleito20 ? "reeleito" : e.v20 ? "voltou/subiu" : "estreia", e.qp ? "QP" : "média", "| top", e.top[0].nome, e.top[0].votos, "(" + (e.conc * 100).toFixed(0) + "%) top3", (e.top3 * 100).toFixed(0) + "%", "| lidera", e.venceu, "locais | presente", e.presente));
const U = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"];
const DZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"];
const CT = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"];
const ate999 = (n) => { if (n < 20) return U[n]; if (n < 100) return DZ[Math.floor(n / 10)] + (n % 10 ? " e " + U[n % 10] : ""); if (n === 100) return "cem"; return CT[Math.floor(n / 100)] + (n % 100 ? " e " + ate999(n % 100) : ""); };
const extF = (n) => ext(n).replace(/(^| )um$/, "$1uma").replace(/(^| )dois$/, "$1duas").replace(/duzentos/g, "duzentas").replace(/trezentos/g, "trezentas");
const ext = (n) => { n = Math.round(n); if (n < 1000) return ate999(n); const m = Math.floor(n / 1000), r = n % 1000; const mil = m === 1 ? "mil" : ate999(m) + " mil"; if (!r) return mil; return mil + (r < 100 || r % 100 === 0 ? " e " : " ") + ate999(r); };
const anoExt = (a) => "dois mil e " + ate999(+a - 2000);
const ORD = ["", "primeiro", "segundo", "terceiro", "quarto", "quinto", "sexto", "sétimo", "oitavo", "nono", "décimo", "décimo primeiro", "décimo segundo", "décimo terceiro", "décimo quarto", "décimo quinto", "décimo sexto", "décimo sétimo", "décimo oitavo"];
try { require(`../data/${ID}.ficha.js`); } catch (er) {}
const OBS = ((window.PLENARIA_FICHAS || {})[ID] || {}).vereadoresObs || {};
out.eleitos.forEach((e) => { if (OBS[e.urna]) e.obs = OBS[e.urna].curto; });
const QE28 = JSON.parse(fs.readFileSync(new URL(`./historico-${SLUG}.json`, import.meta.url))).qe2028;
out.qe2028 = QE28;
const n = out.eleitos.length, novos = out.eleitos.filter((e) => !e.eleito20).length;
const ps = {}; out.eleitos.forEach((e) => (ps[e.partido] = (ps[e.partido] || 0) + 1));
const fala = [
  `${CID}. Os ${ext(n)} vereadores eleitos em ${anoExt(2024)}, um por um: quantos votos, de onde vieram e o que mudou desde ${anoExt(2020)}.`,
  `Foram ${ext(out.candidatos)} candidatos para ${ext(n)} cadeiras. ${ext(novos)[0].toUpperCase() + ext(novos).slice(1)} são caras novas. ${Object.entries(ps).sort((a, b) => b[1] - a[1]).map(([p, k]) => `${p}, ${ext(k)}`).join("; ")}. E o quociente: ${ext(out.qe)} votos.`,
  ...out.eleitos.map((e) => {
    const s = [`${e.urna}, do ${e.partido}. ${ext(e.votos)} votos${e.pos > n ? "" : ": " + (e.pos === 1 ? "a maior votação da cidade" : ORD[e.pos] + " lugar")}.`];
    if (e.eleito20) { const d = e.votos - e.v20; s.push(`Em ${anoExt(2020)}, tinha feito ${ext(e.v20)}: ${d >= 0 ? "ganhou " + ext(d) : "perdeu " + ext(-d)} votos e renovou o mandato.`); }
    else if (e.v20) s.push(`Em ${anoExt(2020)}, teve ${ext(e.v20)} votos e ficou sem a vaga. Desta vez, chegou lá.`);
    else if (e.disputou20) s.push(`Em ${anoExt(2020)}, não chegou à Câmara.`);
    else s.push(`Não disputou a Câmara em ${anoExt(2020)}.`);
    const t = e.top[0]; s.push(`O maior reduto é ${localFala(t.nome)}${t.bairro && ondeBairro(t.bairro) ? ", " + ondeBairro(t.bairro) : ""}: ${ext(t.votos)} votos.`);
    if (e.conc >= 0.4) s.push(`Mais da metade dos votos veio desse único local.`.replace("Mais da metade", e.conc >= 0.5 ? "Mais da metade" : "Quase metade"));
    else if (e.venceu >= 3) s.push(`Liderou a votação em ${ext(e.venceu)} dos ${ext(out.nlocais)} locais.`);
    else if (out.nlocais >= 12 && e.top3 >= 0.44 && e.top3 < 0.56) s.push(`Três locais somam quase metade dos votos.`);
    else if (out.nlocais >= 12 && e.top3 >= 0.56) s.push(`Três locais somam ${ext(Math.round(e.top3 * 100))} por cento dos votos.`);
    else if (e.presente === out.nlocais && out.nlocais >= 12) s.push(`Voto espalhado: teve eleitor nos ${ext(out.nlocais)} locais.`);
    if (e.pos > n) s.push(`Ficou em ${ORD[e.pos]} lugar, mas a vaga é do partido: com a soma do ${e.partido}, entrou.`);
    else if (!e.qp) s.push(`Entrou pela média, na distribuição das sobras.`);
    const ob = OBS[e.urna]; if (ob) s.push(ob.fala);
    return s.join(" ");
  }),
  (() => { const so = out.eleitos.filter((e) => e.votos >= out.qe).map((e) => e.urna); return so.length === 0 ? `Nenhum eleito passou do quociente com os próprios votos: todos dependeram da soma do partido.` : `${so.length === 1 ? "Só " + so[0] + " passou" : so.slice(0, -1).join(", ") + " e " + so[so.length - 1] + " passaram"} do quociente com os próprios votos. ${so.length === n - 1 ? "Só um dependeu" : "Os outros " + ext(n - so.length) + " dependeram"} da soma do partido.`; })(),
  `Em ${anoExt(2028)}, na tendência, cada cadeira vai pedir perto de ${ext(Math.round(QE28 / 50) * 50)} votos. Plenária CE. Inteligência eleitoral de ${CID}.`,
];
const cap = (x) => x.replace(/(^|[.?] )([a-zà-ú])/g, (m, a, b) => a + b.toUpperCase());
fala.forEach((f, i) => (fala[i] = cap(f)));
out.fala = fala;
fs.writeFileSync(new URL("./" + ARQ, import.meta.url), JSON.stringify(out, null, 1));
const nf = new URL("./narracao.json", import.meta.url), N = JSON.parse(fs.readFileSync(nf)); N.videos[CHAVE] = fala; fs.writeFileSync(nf, JSON.stringify(N, null, 2));
fala.forEach((f, i) => console.log(i, f));
