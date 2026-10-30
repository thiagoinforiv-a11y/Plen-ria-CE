#!/usr/bin/env node
// Conferência automática dos dados da Plenária CE.
// Roda antes de cada commit (.githooks/pre-commit), a cada push (GitHub Actions) e ao fim do importador.
// ERRO = dado contradiz um fato conhecido ou a própria soma não fecha → bloqueia a publicação.
// AVISO = falta algo (ex.: eleição ainda não carregada) → não bloqueia, mas aparece.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ctx = { window: {} };
vm.createContext(ctx);
const carregar = (rel, obrigatorio = true) => {
  const p = path.join(RAIZ, rel);
  if (!fs.existsSync(p)) { if (obrigatorio) throw new Error(`arquivo ausente: ${rel}`); return false; }
  vm.runInContext(fs.readFileSync(p, "utf8"), ctx, { filename: rel });
  return true;
};
const norm = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
const mesmoNome = (x, ref) => [x.urna, x.nome].some((n) => norm(n) === norm(ref));
const SELOS = new Set(["confirmado", "declaracao", "uma-fonte", "pesquisa", "a-conferir", "local"]);
const erros = [], avisos = [];

carregar("data/cidades.js");
carregar("assets/js/quociente.js");
const Q = ctx.window.PlenariaQuociente;
for (const c of ctx.window.PLENARIA_CIDADES || []) {
  const tag = c.nome;
  carregar(c.arquivo);
  carregar(c.arquivo.replace(/\.js$/, ".ficha.js"), false);
  carregar(c.arquivo.replace(/\.js$/, ".relatorios.js"), false);
  const d = ctx.window.PLENARIA_DATA[c.id];
  const ficha = (ctx.window.PLENARIA_FICHAS || {})[c.id] || {};
  const rel = (ctx.window.PLENARIA_RELATORIOS || {})[c.id] || {};
  const ref = ficha.referencias || {};
  if (!d) { erros.push(`${tag}: dados não carregaram (${c.arquivo})`); continue; }

  // 1) é mesmo o município certo?
  if (ref.municipio) {
    if (String(d.meta.cd_ibge) !== String(ref.municipio.ibge)) erros.push(`${tag}: código IBGE ${d.meta.cd_ibge} ≠ esperado ${ref.municipio.ibge} (dados de outro município?)`);
    if (String(d.meta.cd_tse) !== String(ref.municipio.tse)) erros.push(`${tag}: código TSE ${d.meta.cd_tse} ≠ esperado ${ref.municipio.tse}`);
  } else avisos.push(`${tag}: ficha sem referencias.municipio — não dá para confirmar o código do município`);

  // 2) prefeito eleito em cada ano bate com o conhecido
  for (const [ano, nome] of Object.entries(ref.prefeitos || {})) {
    const c2 = d.eleicoes[ano]?.cargos?.prefeito;
    if (!c2) { avisos.push(`${tag}: ${ano} sem resultado de prefeito carregado — referência "${nome}" não conferida`); continue; }
    const eleito = c2.candidatos.find((x) => (x.situacao || "").startsWith("eleito")) || c2.candidatos[0];
    if (!mesmoNome(eleito, nome)) erros.push(`${tag}: prefeito eleito em ${ano} nos dados é "${eleito.urna}", mas o conhecido é "${nome}"`);
  }
  // 3) vereadores mais votados batem com o conhecido
  for (const [ano, nomes] of Object.entries(ref.vereadoresMaisVotados || {})) {
    const c2 = d.eleicoes[ano]?.cargos?.vereador;
    if (!c2) { avisos.push(`${tag}: ${ano} sem resultado de vereador carregado — mais votados (${nomes.join(", ")}) não conferidos`); continue; }
    nomes.forEach((n, i) => { const x = c2.candidatos[i]; if (!x || !mesmoNome(x, n)) erros.push(`${tag}: ${i + 1}º vereador mais votado em ${ano} nos dados é "${x ? x.urna : "—"}", mas o conhecido é "${n}"`); });
  }
  // 3b) votos por candidato conhecidos de outra fonte têm de bater
  for (const r of ref.votosConhecidos || []) {
    const cg = d.eleicoes[r.ano]?.cargos?.[r.cargo];
    if (!cg) continue;
    const x = cg.candidatos.find((y) => mesmoNome(y, r.nome));
    if (!x) erros.push(`${tag}: ${r.ano} ${r.cargo}: ${r.nome} não está nos dados (fonte: ${r.fonte})`);
    else if (x.votos !== r.votos) erros.push(`${tag}: ${r.ano} ${r.cargo}: ${r.nome} tem ${x.votos} nos dados, mas ${r.fonte} diz ${r.votos}`);
  }
  for (const [ano, cargo, nome] of ref.maisVotados || []) {
    const cg = d.eleicoes[ano]?.cargos?.[cargo];
    if (cg && !mesmoNome(cg.candidatos[0], nome)) erros.push(`${tag}: ${ano} ${cargo}: mais votado nos dados é ${cg.candidatos[0].urna}, a fonte diz ${nome}`);
  }
  // 4) somas e duplicidades
  for (const [ano, e] of Object.entries(d.eleicoes)) for (const [k, cg] of Object.entries(e.cargos)) {
    const soma = cg.candidatos.reduce((t, x) => t + x.votos, 0);
    if (cg.parcial && cg.totais && cg.totais.validos != null && soma > cg.totais.validos) erros.push(`${tag}: ${ano} ${k} (parcial): candidatos somam ${soma}, acima dos válidos ${cg.totais.validos}`);
    if (cg.totais && cg.totais.nominais != null && soma !== cg.totais.nominais) erros.push(`${tag}: ${ano} ${k}: soma dos candidatos ${soma} ≠ nominais oficiais ${cg.totais.nominais}`);
    const sqs = new Set();
    for (const x of cg.candidatos) {
      if (sqs.has(x.sq)) erros.push(`${tag}: ${ano} ${k}: candidato repetido ${x.urna}`);
      sqs.add(x.sq);
      if (x.secoes) { const s2 = Object.values(x.secoes).reduce((t, v) => t + v, 0); if (s2 !== x.votos) erros.push(`${tag}: ${ano} ${k}: ${x.urna} soma por seção ${s2} ≠ total ${x.votos}`); }
    }
    // quociente: votos por partido fecham com os válidos e, sem coligações, a distribuição recalculada bate com os eleitos oficiais
    if (cg.partidos) {
      const tot = Object.values(cg.partidos).reduce((t, p) => t + p.total, 0);
      if (cg.totais && tot !== cg.totais.validos) erros.push(`${tag}: ${ano} ${k}: votos por partido ${tot} ≠ válidos ${cg.totais.validos}`);
      const q = Q.quociente(cg, ano);
      if (q && q.simulado) for (const p of q.partidos) {
        const reais = cg.candidatos.filter((x) => x.partido === p.sigla && (x.situacao || "").startsWith("eleito")).map((x) => x.urna).sort().join(", ");
        const sim = p.eleitos.map((x) => x.urna).sort().join(", ");
        if (reais !== sim) erros.push(`${tag}: ${ano} ${k}: recálculo das cadeiras do ${p.sigla} dá [${sim}], oficial é [${reais}]`);
      }
    }
    for (let i = 1; i < cg.candidatos.length; i++) if (cg.candidatos[i].votos > cg.candidatos[i - 1].votos) { erros.push(`${tag}: ${ano} ${k}: ranking fora de ordem`); break; }
  }
  // 5) cobertura: a eleição mais recente está carregada?
  const anos = (f) => Object.entries(d.eleicoes).filter(([, e]) => Object.keys(e.cargos).some(f)).map(([a]) => +a);
  const ult = ref.ultimasEleicoes || {};
  const munMax = Math.max(0, ...anos((k) => k === "prefeito" || k === "vereador"));
  const gerMax = Math.max(0, ...anos((k) => k.startsWith("deputado") || k === "senador" || k === "governador"));
  if (ult.municipal && munMax < ult.municipal) avisos.push(`${tag}: eleição municipal mais recente carregada é ${munMax || "nenhuma"}; falta ${ult.municipal} (a página avisa o usuário)`);
  if (ult.geral && gerMax < ult.geral) avisos.push(`${tag}: eleição geral mais recente carregada é ${gerMax || "nenhuma"}; falta ${ult.geral}`);
  // 6) ficha e relatórios: selos, links e datas
  const itens = [...(ficha.poder || []), ...(ficha.fatos || []), ...(ficha.acompanhar || []), ...((rel.pessoas || []).flatMap((p) => [...(p.destaques || []), ...(p.redes || [])]))];
  for (const it of itens) {
    if (it.selo && !SELOS.has(it.selo)) erros.push(`${tag}: selo inválido "${it.selo}" em "${it.titulo || it.nome || it.rede}"`);
    for (const f of it.fontes || []) if (!/^https:\/\//.test(f.url || "")) erros.push(`${tag}: link sem https em "${it.titulo || it.nome}": ${f.url}`);
    if (it.data && !/^\d{4}(-\d{2}(-\d{2})?)?$/.test(it.data)) erros.push(`${tag}: data inválida "${it.data}" em "${it.titulo}"`);
  }
}

for (const a of avisos) console.log("AVISO  " + a);
for (const e of erros) console.log("ERRO   " + e);
console.log(erros.length ? `\n✘ ${erros.length} erro(s). Corrija antes de publicar.` : `\n✔ Dados conferidos (${avisos.length} aviso(s)).`);
process.exit(erros.length ? 1 : 0);
