// Histórico municipal (prefeito e Câmara) das três últimas eleições + o que os números dizem de 2028.
// Padrão para qualquer cidade: node video/historico.mjs ce/varjota
// Gera video/historico-<cidade>.json (números + roteiro da narração). Projeções são só tendência, e vêm marcadas.
import { createRequire } from "module";
import fs from "fs";
const require = createRequire(import.meta.url);
const id = process.argv[2] || "ce/varjota";
global.window = {};
require(`../data/${id}.js`);
const D = window.PLENARIA_DATA[id], M = D.meta;
try { require(`../data/${id}.ficha.js`); } catch (e) {}
const FICHA = (window.PLENARIA_FICHAS || {})[id] || {}, INTER = (FICHA.referencias || {}).interrupcoes || [];
const interrupcao = (ano, nome) => INTER.find((x) => String(x.eleicao) === String(ano) && (!nome || x.nome === nome));
const anos = Object.keys(D.eleicoes).filter((a) => D.eleicoes[a].cargos.prefeito && D.eleicoes[a].cargos.vereador).sort().slice(-3);
const PARTIDO = { PMDB: "MDB", PFL: "DEM", PPS: "Cidadania", PR: "PL", PRB: "Republicanos", PSL: "União", DEM: "União", "UNIÃO": "União", CIDADANIA: "Cidadania", REPUBLICANOS: "Republicanos", PATRIOTA: "Patriota", PATRI: "Patriota", AVANTE: "Avante", PODE: "Podemos", SOLIDARIEDADE: "Solidariedade", NOVO: "Novo", PHS: "PHS", PROS: "PROS", PCdoB: "PC do B", AGIR: "Agir", MOBILIZA: "Mobiliza", PRD: "PRD" };
const part = (p) => PARTIDO[p] || p;
const ok = (x) => /^eleit/i.test(x.situacao || "");
const fotoDe = (pid) => { let f = null; for (const a of Object.keys(D.eleicoes).sort()) for (const c of Object.values(D.eleicoes[a].cargos)) for (const x of c.candidatos) if (x.pid === pid && x.foto && !/^https?:/.test(x.foto)) f = x.foto; return f; };
const ctx = (a) => (D.contexto || []).find((c) => String(c.ano) === a && c.cargo === "prefeito") || {};

// ---------- números
const prefeito = anos.map((a) => { const c = D.eleicoes[a].cargos.prefeito, v = c.totais.validos, [p1, p2] = c.candidatos;
  return { ano: a, venc: { nome: p1.urna, partido: part(p1.partido), votos: p1.votos, pct: p1.votos / v, pid: p1.pid, foto: fotoDe(p1.pid) }, seg: p2 && { nome: p2.urna, partido: part(p2.partido), votos: p2.votos, pct: p2.votos / v, pid: p2.pid, foto: fotoDe(p2.pid) }, margem: p1.votos - (p2 ? p2.votos : 0) }; });
const eleitorado = anos.map((a) => ({ ano: a, aptos: ctx(a).aptos, comparecimento: ctx(a).comparecimento, abstencoes: ctx(a).abstencoes }));
const eleitosDe = (a) => D.eleicoes[a].cargos.vereador.candidatos.filter(ok);
const camara = anos.map((a) => { const e = eleitosDe(a), p = {}; e.forEach((x) => (p[part(x.partido)] = (p[part(x.partido)] || 0) + 1)); const c = D.eleicoes[a].cargos.vereador, top = c.candidatos[0];
  return { ano: a, cadeiras: e.length, candidatos: c.candidatos.length, validos: c.totais.validos, qe: Math.round(c.totais.validos / e.length), partidos: Object.entries(p).sort((x, y) => y[1] - x[1]), top: { nome: top.urna, votos: top.votos, partido: part(top.partido), foto: fotoDe(top.pid) } }; });
// renovação em cada eleição (comparando com a anterior, mesmo antes da janela)
const todos = Object.keys(D.eleicoes).filter((a) => D.eleicoes[a].cargos.vereador).sort();
const renov = anos.map((a) => { const ant = todos[todos.indexOf(a) - 1]; if (!ant) return null; const A = eleitosDe(ant), B = eleitosDe(a); const re = B.filter((x) => A.some((y) => y.pid === x.pid)); return { ano: a, de: ant, cadeiras: B.length, reeleitos: re.length, novos: B.length - re.length, nomes: re.map((x) => x.urna) }; }).filter(Boolean);
// 2028
const ult = prefeito[prefeito.length - 1], pen = prefeito[prefeito.length - 2];
const todosPref = Object.keys(D.eleicoes).filter((a) => D.eleicoes[a].cargos.prefeito).sort().map((a) => ({ ano: a, p: D.eleicoes[a].cargos.prefeito.candidatos[0] }));
const bisado = (i) => i > 0 && todosPref[i].p.pid === todosPref[i - 1].p.pid;
const semReeleicao = bisado(todosPref.length - 1);
// mandato atual interrompido (cassação seguida de eleição suplementar): quem governa hoje é outro
const atualInt = INTER.find((x) => String(x.eleicao) === String(todosPref[todosPref.length - 1].ano) && x.atual) || null;
// prefeitura aberta: o prefeito no cargo não estava na disputa (fim do segundo mandato ou não concorreu)
const aberturas = [];
for (let i = 1; i < todosPref.length; i++) {
  const a = todosPref[i].ano, sai = todosPref[i - 1].p, cands = D.eleicoes[a].cargos.prefeito.candidatos, entra = todosPref[i].p;
  if (cands.some((x) => x.pid === sai.pid)) continue;
  const it = interrupcao(todosPref[i - 1].ano, sai.urna);
  aberturas.push({ ano: a, saiu: sai.urna, interrompido: it ? it.curto : null, motivo: it ? it.motivo : bisado(i - 1) ? "fim do segundo mandato" : "não disputou", partidoSaiu: part(sai.partido), venceu: entra.urna, partidoVenceu: part(entra.partido), mesmoPartido: part(sai.partido) === part(entra.partido) });
}
const precedentes = aberturas.filter((x) => anos.includes(x.ano)), precedente = precedentes[precedentes.length - 1] || null;
const tend = (xs) => Math.round(xs[xs.length - 1] + (xs[xs.length - 1] - xs[xs.length - 2]));
const qe2028 = tend(camara.map((c) => c.qe));
const novosMedia = Math.round(renov.reduce((s, r) => s + r.novos, 0) / renov.length);
const abst = eleitorado.map((e) => e.abstencoes);

// ---------- números por extenso (a voz lê melhor)
const U = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"];
const DZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"];
const CT = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"];
const ate999 = (n) => { if (n < 20) return U[n]; if (n < 100) return DZ[Math.floor(n / 10)] + (n % 10 ? " e " + U[n % 10] : ""); if (n === 100) return "cem"; return CT[Math.floor(n / 100)] + (n % 100 ? " e " + ate999(n % 100) : ""); };
const extF = (n) => ext(n).replace(/(^| )um$/, "$1uma").replace(/(^| )dois$/, "$1duas").replace(/duzentos/g, "duzentas").replace(/trezentos/g, "trezentas");
const ext = (n) => { n = Math.round(n); if (n < 1000) return ate999(n); const m = Math.floor(n / 1000), r = n % 1000; const mil = m === 1 ? "mil" : ate999(m) + " mil"; if (!r) return mil; return mil + (r < 100 || r % 100 === 0 ? " e " : " ") + ate999(r); };
const anoExt = (a) => "dois mil e " + ate999(+a - 2000);
const pct = (x) => Math.round(x * 100);
const fem = (nome) => /a$/i.test(nome.split(" ")[0]) || /^(Rosa|Célia|Loura|Djinha|Fransquinha)/.test(nome);

// ---------- roteiro (uma fala por cena)
const seqVenc = () => { const g = []; prefeito.forEach((p) => { const u = g[g.length - 1]; if (u && u.pid === p.venc.pid) u.n++; else g.push({ pid: p.venc.pid, nome: p.venc.nome, n: 1 }); });
  const vezes = ["", "", "duas vezes", "três vezes"]; return "Em três eleições: " + g.map((x, i) => (i ? "depois " : "") + x.nome + (x.n > 1 ? ", " + vezes[x.n] : "")).join("; "); };
const fraseAberturas = () => { if (!precedentes.length) return "";
  const qtd = ["", "uma vez", "duas vezes", "três vezes"][precedentes.length] || precedentes.length + " vezes";
  return `Isso já aconteceu ${qtd}. ` + precedentes.map((x) => `Em ${anoExt(x.ano)}, ${x.interrompido ? `com ${x.saiu} ${x.interrompido} e fora da disputa` : `sem ${x.saiu} na disputa`}, ${x.mesmoPartido ? `o ${x.partidoSaiu} manteve a prefeitura com ${x.venceu}` : `${x.venceu} venceu, pelo ${x.partidoVenceu}`}.`).join(" ") + " "; };
const frasePartidos = () => {
  const lid = camara.map((c) => { const n = c.partidos[0][1]; return { ano: c.ano, ps: c.partidos.filter((x) => x[1] === n).map((x) => x[0]), n }; });
  const igual = (x, y) => x.n === y.n && x.ps.join() === y.ps.join();
  const lista = (ps) => ps.map((p) => "o " + p).join(", ").replace(/, ([^,]*)$/, " e $1");
  const partes = []; let i = 0;
  while (i < lid.length) { let j = i; while (j + 1 < lid.length && igual(lid[j + 1], lid[i])) j++;
    const L = lid[i], anosTxt = lid.slice(i, j + 1).map((x) => anoExt(x.ano)).join(" e em "), cada = L.ps.length > 1 ? " cada" : "";
    if (!i) partes.push(`${lista(L.ps)} ${L.ps.length > 1 ? "fizeram" : "fez"} ${extF(L.n)} cadeiras${cada} em ${anosTxt}`);
    else if (L.ps.join() === lid[i - 1].ps.join()) partes.push(`em ${anosTxt}, o ${L.ps.join(" e o ")} ${L.ps.length > 1 ? "seguiram" : "seguiu"} na frente, com ${extF(L.n)} cadeiras`);
    else partes.push(L.ps.length > 1 ? `em ${anosTxt}, ${lista(L.ps)} empataram na frente, com ${extF(L.n)} cadeiras cada` : `em ${anosTxt}, o ${L.ps[0]} passou a liderar com ${extF(L.n)} cadeiras`);
    i = j + 1; }
  const ult = camara[camara.length - 1].partidos, fimL = lid[lid.length - 1].ps;
  const saiu = lid[0].ps.filter((p) => !fimL.includes(p)), zerou = saiu.filter((p) => !ult.some((x) => x[0] === p));
  const quedas = saiu.filter((p) => !zerou.includes(p)).map((p) => `o ${p} caiu para ${extF(ult.find((x) => x[0] === p)[1])}`);
  if (zerou.length) quedas.push(`${lista(zerou)} ${zerou.length > 1 ? "ficaram" : "ficou"} sem cadeira`);
  return partes.join(". E ") + (quedas.length ? ", e " + quedas.join(", e ") : ""); };
const [a0, a1, a2] = anos, C = M.municipio;
const cartoes2028 = (FICHA.fatos || []).filter((f) => f.cartao2028).map((f) => f.cartao2028);
const fala = [
  `${C}. De ${anoExt(a0)} a ${anoExt(a2)}: a prefeitura e a Câmara, eleição por eleição. E o que isso diz de ${anoExt(2028)}.`,
  `O eleitorado foi de ${ext(eleitorado[0].aptos)} para ${ext(eleitorado[2].aptos)}. E a abstenção ${abst[2] < abst[0] ? "caiu" : "subiu"}: de ${ext(abst[0])} para ${ext(abst[2])} eleitores.`,
  ...prefeito.map((p) => { const it = interrupcao(p.ano, p.venc.nome); return `Em ${anoExt(p.ano)}, ${p.venc.nome} venceu com ${ext(pct(p.venc.pct))} por cento. ${p.seg ? `${p.seg.nome} ficou com ${ext(pct(p.seg.pct))}. Diferença de ${ext(p.margem)} votos.` : ""}${it ? ` Depois, foi ${it.motivo}.${it.depois ? " " + it.depois : ""}` : ""}`; }),
  `${seqVenc()}. ${atualInt ? `Hoje, a prefeitura está com ${atualInt.atual}, eleito na eleição suplementar.` : semReeleicao ? `Em ${anoExt(2028)}, ${ult.venc.nome} não pode concorrer de novo: a cadeira de prefeito fica aberta.` : `Em ${anoExt(2028)}, ${ult.venc.nome} pode tentar a reeleição.`}`,
  `Na Câmara, ${frasePartidos()}.`,
  `A renovação é alta. Caras novas em cada eleição: ${renov.map((r) => ext(r.novos)).join(", ").replace(/, ([^,]*)$/, " e $1")}, de ${extF(renov[0].cadeiras)} cadeiras.`,
  `Para se eleger, o preço subiu. O quociente foi de ${ext(camara[0].qe)} para ${ext(camara[2].qe)} votos por cadeira. Na tendência, ${anoExt(2028)} pede perto de ${ext(Math.round(qe2028 / 50) * 50)}.`,
  `Então, como será ${anoExt(2028)}? ${atualInt ? "A prefeitura mudou de mãos no meio do mandato. " : semReeleicao ? "Prefeitura aberta. " : ""}${fraseAberturas()}${cartoes2028.length && !atualInt ? "E os grupos mudaram desde então. " : ""}Se a renovação seguir a média, cerca de ${ext(novosMedia)} vereadores novos.`,
  `Plenária CE. Inteligência eleitoral de ${C}. A história de cada eleição, para decidir a próxima.`,
];
const interrupcoes = INTER;
const out = { atual: atualInt && { nome: atualInt.atual, quando: atualInt.quando }, cartoes2028, interrupcoes, id, municipio: C, cd_ibge: M.cd_ibge, anos, eleitorado, prefeito, camara, renov, semReeleicao, precedente, precedentes, qe2028, novosMedia, fala };
const slug = id.split("/")[1];
// nomes de urna vêm sem acento do TSE em alguns anos
const ACENTOS = [[/\bJoao\b/g, "João"], [/\bSebastiao\b/g, "Sebastião"], [/\bConceicao\b/g, "Conceição"], [/\bSergio\b/g, "Sérgio"], [/\bTomas\b/g, "Tomás"], [/\bRoberio\b/g, "Robério"], [/\bDra\.? /g, "Dra. "], [/\bDr\.? /g, "Dr. "], [/\bJose\b/g, "José"], [/\bMaria Jose\b/g, "Maria José"]];
const acentuar = (t) => ACENTOS.reduce((x, [r, v]) => x.replace(r, v), t);
for (const k of Object.keys(out)) if (k !== "fala") out[k] = JSON.parse(acentuar(JSON.stringify(out[k])));
fala.forEach((f, i) => { fala[i] = acentuar(f).replace(/\bDra\. /g, "Doutora ").replace(/\bDr\. /g, "Doutor "); });
fs.writeFileSync(new URL(`./historico-${slug}.json`, import.meta.url), JSON.stringify(out, null, 1));
// roteiro também vai para a narração
const nf = new URL("./narracao.json", import.meta.url), N = JSON.parse(fs.readFileSync(nf, "utf8"));
N.videos[`historico-${slug}`] = fala; fs.writeFileSync(nf, JSON.stringify(N, null, 2));
console.log(JSON.stringify({ ...out, fala: undefined }, null, 0).slice(0, 1500)); fala.forEach((f, i) => console.log(i, f));
