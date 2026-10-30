/* Plenária CE — painel de análise eleitoral por município.
 * Os dados vêm de data/<uf>/<cidade>.js, gerados por scripts/plenaria.py a partir do TSE.
 * Futuro login: a verificação de acesso entra antes de App.loadCity(). */
(function () {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const NF = new Intl.NumberFormat("pt-BR");
  const fmt = (n) => (n == null || isNaN(n) ? "—" : NF.format(Math.round(n)));
  const pct = (x, d = 1) => (x == null || !isFinite(x) ? "—" : (x * 100).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }) + "%");
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : "");
  const initials = (n) => (n || "?").split(/\s+/).filter((p) => p.length > 2 || /^[A-Z]/.test(p)).slice(0, 2).map((p) => p[0]).join("").toUpperCase();
  const store = {
    get(k, d) { try { const v = localStorage.getItem("plenaria." + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("plenaria." + k, JSON.stringify(v)); } catch (e) { /* modo privado */ } },
  };

  const SLOTS = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)"];
  const CARGO_ORDEM = ["deputado_estadual", "deputado_federal", "vereador", "prefeito", "governador", "senador", "presidente"];
  const CARGO_CURTO = { deputado_estadual: "Dep. Estadual", deputado_federal: "Dep. Federal", vereador: "Vereador", prefeito: "Prefeito", governador: "Governador", senador: "Senador", presidente: "Presidente" };
  const cargoCurto = (k) => (CARGO_CURTO[k.replace(/_2t$/, "")] || k) + (k.endsWith("_2t") ? " (2º t.)" : "");

  const S = {
    city: null, cityId: null, ano: null, cargo: null,
    limiar: store.get("limiar", 1), rankAll: false, busca: "",
    cmp: [], secSel: [], secBairro: "", secCand: "", secSort: "validos",
    map: { ano: null, cargo: null, bairro: null, local: null, secao: null, foco: [] }, cmpBy: "bairro", cmpMode: "votos",
    dep: { pid: "", ano: null },
    traj: { tipo: "vereador", sel: [], modo: "pct", init: false },
    cruz: { depEl: "", dep: "", verEl: "", aliados: [], nivel: "bairro" },
  };
  const cache = new Map();

  // ------------------------------------------------------------------ dados
  function loadScript(src) {
    return new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = src; s.onload = res; s.onerror = () => rej(new Error("Falha ao carregar " + src));
      document.head.appendChild(s);
    });
  }
  async function loadCity(id) {
    const reg = (window.PLENARIA_CIDADES || []).find((c) => c.id === id) || (window.PLENARIA_CIDADES || [])[0];
    if (!reg) throw new Error("Nenhuma cidade em data/cidades.js");
    window.PLENARIA_DATA = window.PLENARIA_DATA || {};
    if (!window.PLENARIA_DATA[reg.id]) {
      await loadScript(reg.arquivo);
      // ficha editável à mão (fatos, quem manda); opcional
      await loadScript(reg.arquivo.replace(/\.js$/, ".ficha.js")).catch(() => null);
      // conhecimento local e leituras: só no computador do usuário (fora do git)
      await loadScript(reg.arquivo.replace(/\.js$/, ".local.js")).catch(() => null);
      await loadScript(reg.arquivo.replace(/\.js$/, ".relatorios.js")).catch(() => null);
    }
    S.city = window.PLENARIA_DATA[reg.id];
    S.ficha = (window.PLENARIA_FICHAS || {})[reg.id] || null;
    S.local = (window.PLENARIA_LOCAL || {})[reg.id] || null;
    S.rel = (window.PLENARIA_RELATORIOS || {})[reg.id] || null;
    resolverFotos();
    S.cityId = reg.id;
    store.set("cidade", reg.id);
    const anos = Object.keys(S.city.eleicoes).sort().reverse();
    // prioriza a eleição mais recente com detalhe por seção
    S.ano = anos.find((a) => S.city.eleicoes[a].nivel === "secao") || anos[0];
    S.cargo = cargosDe(S.ano)[0];
    cache.clear();
  }
  // Fotos: 1) arquivo local (importador do TSE ou enviado por você); 2) foto oficial do DivulgaCand,
  // carregada direto pelo navegador de quem abre a página (some sozinha se o TSE não tiver a foto).
  const DIVULGA = { 2012: "1699", 2014: "680", 2016: "2", 2018: "2022802018", 2020: "2030402020", 2022: "2040602022", 2024: "2045202024" };
  const MUNICIPAIS = new Set(["prefeito", "vereador", "vice-prefeito"]);
  function divulgaUE(ano, cargo) { return MUNICIPAIS.has(cargo.replace(/_2t$/, "")) ? S.city.meta.cd_tse : S.city.meta.uf; }
  function divulgaLink(ano, cargo, sq) {
    const el = DIVULGA[ano];
    return el && /^\d{9,}$/.test(sq || "") ? `https://divulgacandcontas.tse.jus.br/divulga/#/candidato/${ano}/${el}/${divulgaUE(ano, cargo)}/${sq}` : null;
  }
  function resolverFotos() {
    const manual = (S.local && S.local.fotos) || {};
    const porNome = Object.fromEntries(Object.entries(manual).map(([k, v]) => [k.toLowerCase(), v]));
    for (const [ano, e] of Object.entries(S.city.eleicoes))
      for (const [k, c] of Object.entries(e.cargos))
        for (const x of c.candidatos) {
          const m = manual[x.pid] || porNome[(x.urna || "").toLowerCase()] || porNome[(x.nome || "").toLowerCase()];
          if (m) { x.foto = m; continue; }
          const el = DIVULGA[ano];
          if (!x.foto && el && /^\d{9,}$/.test(x.sq || "")) x.foto = `https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/${el}/${x.sq}/${divulgaUE(ano, k)}`;
        }
  }
  const E = () => S.city.eleicoes[S.ano];
  const C = () => E().cargos[S.cargo];
  const porSecao = () => E().nivel === "secao";
  function cargosDe(ano) {
    const ks = Object.keys(S.city.eleicoes[ano].cargos);
    const rank = (k) => { const i = CARGO_ORDEM.indexOf(k.replace(/_2t$/, "")); return (i < 0 ? 99 : i) + (k.endsWith("_2t") ? 0.5 : 0); };
    return ks.sort((a, b) => rank(a) - rank(b));
  }
  function contextoDo(ano, cargo) {
    const ctx = S.city.contexto || [];
    const base = cargo ? cargo.replace(/_2t$/, "") : null;
    const turno = cargo && cargo.endsWith("_2t") ? 2 : 1;
    return ctx.find((c) => c.ano == ano && c.turno === turno && c.cargo === base) || ctx.find((c) => c.ano == ano && c.turno === 1) || null;
  }

  /** agregados de um cargo/ano (padrão: o selecionado): por seção, por local, por bairro */
  function agg(ano = S.ano, cargo = S.cargo) {
    const key = S.cityId + ano + cargo;
    if (cache.has(key)) return cache.get(key);
    const e = S.city.eleicoes[ano], c = e.cargos[cargo];
    const cands = c.candidatos;
    const validos = c.totais ? c.totais.validos : cands.reduce((s, x) => s + x.votos, 0);
    const r = { cands, validos, secoes: {}, locais: {}, bairros: {}, bySq: {} };
    cands.forEach((x, i) => { r.bySq[x.sq] = x; x._pos = i + 1; });
    if (e.nivel === "secao") {
      const legendas = Object.values(c.legendas || {});
      for (const [sid, s] of Object.entries(e.secoes)) {
        const L = e.locais[s.local] || { nome: "?", bairro: "Não informado" };
        const sec = (r.secoes[sid] = { id: sid, ...s, localNome: L.nome, bairro: L.bairro, validos: 0, cand: {} });
        legendas.forEach((l) => (sec.validos += l.secoes[sid] || 0));
        const lo = (r.locais[s.local] ||= { id: s.local, ...L, aptos: 0, validos: 0, cand: {}, secoes: [] });
        lo.secoes.push(sid); lo.aptos += s.aptos || 0;
        const b = (r.bairros[L.bairro] ||= { nome: L.bairro, aptos: 0, validos: 0, cand: {}, secoes: [], locais: new Set() });
        b.secoes.push(sid); b.aptos += s.aptos || 0; b.locais.add(s.local);
      }
      for (const x of cands) {
        for (const [sid, v] of Object.entries(x.secoes || {})) {
          const sec = r.secoes[sid]; if (!sec) continue;
          sec.cand[x.sq] = v; sec.validos += v;
          const lo = r.locais[sec.local]; lo.cand[x.sq] = (lo.cand[x.sq] || 0) + v;
          const b = r.bairros[sec.bairro]; b.cand[x.sq] = (b.cand[x.sq] || 0) + v;
        }
      }
      for (const sec of Object.values(r.secoes)) { r.locais[sec.local].validos += sec.validos; r.bairros[sec.bairro].validos += sec.validos; }
      const top = (o) => Object.entries(o.cand).sort((a, b) => b[1] - a[1]);
      [...Object.values(r.secoes), ...Object.values(r.locais), ...Object.values(r.bairros)].forEach((o) => (o.rank = top(o)));
    }
    cache.set(key, r);
    return r;
  }
  const relevantes = (a) => a.cands.filter((x) => x.votos >= (S.limiar / 100) * a.validos);

  // ------------------------------------------------------------------ peças
  const avatar = (x, cls = "av") =>
    `<span class="${cls}" style="position:relative"${!x.foto && x.wiki ? ` data-wiki="${esc(x.wiki)}"` : ""}>${esc(initials(x.urna))}${x.foto ? `<img src="${esc(x.foto)}" alt="" loading="lazy" style="position:absolute;inset:0" referrerpolicy="no-referrer" onerror="this.remove()">` : ""}</span>`;
  const situTxt = (s) => (s || "").toLowerCase().replace("eleito por qp", "eleito (QP)").replace("eleito por média", "eleito (média)");
  const situ = (x) => {
    const s = situTxt(x.situacao);
    return s ? `<span class="tag ${s.startsWith("eleito") ? "ok" : ""}">${esc(s)}</span>` : "";
  };
  const tip = (html) => `data-tip="${esc(html)}"`;
  const slotOf = (sq) => { const i = S.cmp.indexOf(sq); return i < 0 ? null : SLOTS[i]; };
  const naoSecao = (o) => `<div class="notice"><b>Detalhe por ${o} indisponível para ${S.ano}.</b> Esta eleição está carregada só com os totais do município (fonte: ${esc(E().fonte)}). Para abrir por bairro e seção, importe os arquivos oficiais do TSE:<br><code>python3 scripts/plenaria.py tse --municipio ${esc(S.city.meta.municipio)} --ano ${esc(S.ano)} --baixar</code></div>`;

  // ------------------------------------------------------------------ render
  function renderControls() {
    const cs = window.PLENARIA_CIDADES || [];
    $("#sel-city").innerHTML = cs.map((c) => `<option value="${esc(c.id)}" ${c.id === S.cityId ? "selected" : ""}>${esc(c.nome)} · ${esc(c.uf)}</option>`).join("") + `<option disabled>Outras cidades do CE — em breve</option>`;
    const anos = Object.keys(S.city.eleicoes).sort().reverse();
    $("#sel-year").innerHTML = anos.map((a) => `<option value="${a}" ${a === S.ano ? "selected" : ""}>${a}${S.city.eleicoes[a].nivel === "secao" ? " · por seção" : ""}</option>`).join("");
    $("#seg-cargo").innerHTML = cargosDe(S.ano).map((k) => `<button type="button" data-cargo="${k}" aria-pressed="${k === S.cargo}">${esc(cargoCurto(k))}</button>`).join("");
  }

  function avisoCobertura() {
    const ref = (S.ficha && S.ficha.referencias) || {};
    const ult = ref.ultimasEleicoes || {};
    const municipal = ["prefeito", "vereador"].includes(S.cargo.replace(/_2t$/, ""));
    const esperado = municipal ? ult.municipal : ult.geral;
    if (!esperado || +S.ano >= esperado) return "";
    const top = municipal && S.cargo === "vereador" && (ref.vereadoresMaisVotados || {})[esperado];
    const pref = municipal && S.cargo === "prefeito" && (ref.prefeitos || {})[esperado];
    return `<div class="aviso-cob"><b>Atenção: você está vendo ${esc(S.ano)}, não a eleição mais recente.</b> O resultado de ${esperado} ainda não foi carregado na página (vem do TSE).
      ${top ? ` Em ${esperado}, os mais votados para vereador foram <b>${top.map(esc).join(", ")}</b>.` : ""}${pref ? ` Em ${esperado}, o prefeito eleito foi <b>${esc(pref)}</b>.` : ""}</div>`;
  }
  function renderHero() {
    const a = agg(), m = S.city.meta, c = C();
    const av = $("#aviso-cob") || (() => { const d = document.createElement("div"); d.id = "aviso-cob"; $("#visao").prepend(d); return d; })();
    av.innerHTML = avisoCobertura() + (C().parcial ? `<div class="aviso-cob">Lista <b>parcial</b>: só os candidatos levantados para ${esc(S.city.meta.municipio)} em ${esc(S.ano)} (${esc(E().fonte)}). Números conferidos com outra fonte quando possível; a lista completa vem do TSE.</div>` : "");
    $("#hero-title").innerHTML = `${esc(cargoCurto(S.cargo))} em <em class="s">${esc(m.municipio)}</em>, ${esc(S.ano)}`;
    const rel = relevantes(a);
    const lider = a.cands[0];
    $("#hero-lead").innerHTML = lider
      ? `${esc(lider.urna)} (${esc(lider.partido || "")}) liderou com <b>${fmt(lider.votos)}</b> votos — ${pct(lider.votos / a.validos)} dos ${fmt(a.validos)} válidos. ${fmt(a.cands.length)} candidatos receberam ao menos um voto; ${fmt(rel.length)} passaram de ${S.limiar.toLocaleString("pt-BR")}% dos válidos.`
      : "Sem votos registrados para este cargo.";
  }

  function renderKPIs() {
    const a = agg(), c = C(), ctx = contextoDo(S.ano, S.cargo);
    const rel = relevantes(a);
    const relSoma = rel.reduce((s, x) => s + x.votos, 0);
    const t = c.totais || {};
    const nb = Object.keys(a.bairros).length, ns = Object.keys(a.secoes).length;
    $("#sec-kpis").innerHTML = `<div class="grid kpis">
      <div class="card kpi"><div class="l">Eleitores aptos</div><div class="v num">${fmt(ctx && ctx.aptos)}</div><div class="d">${ctx && ctx.comparecimento ? `${fmt(ctx.comparecimento)} compareceram (${pct(ctx.comparecimento / ctx.aptos)})` : "—"}</div></div>
      <div class="card kpi"><div class="l">Votos válidos · ${esc(cargoCurto(S.cargo))}</div><div class="v num">${fmt(a.validos)}</div><div class="d">${fmt(t.nominais)} nominais · ${fmt(t.legenda)} na legenda<br>${fmt(t.brancos)} brancos · ${fmt(t.nulos)} nulos</div></div>
      <div class="card kpi"><div class="l">Candidatos com voto</div><div class="v num">${fmt(a.cands.length)}</div><div class="d">${porSecao() ? `${fmt(ns)} seções · ${fmt(Object.keys(a.locais).length)} locais · ${fmt(nb)} bairros` : "totais do município"}</div></div>
      <div class="card kpi accent"><div class="l">Votação relevante</div><div class="v num">${fmt(rel.length)}</div>
        <div class="d">candidatos com ≥ <b id="lim-v">${S.limiar.toLocaleString("pt-BR")}%</b> dos válidos (≥ ${fmt(Math.ceil((S.limiar / 100) * a.validos))} votos) — somam ${pct(relSoma / a.validos)}</div>
        <div class="range"><span>0,25%</span><input id="lim" type="range" min="0.25" max="5" step="0.25" value="${S.limiar}" aria-label="Limiar de relevância"><span>5%</span></div></div>
    </div>`;
  }


  // ------------------------------------------------------------------ quociente eleitoral, partidário e "puxados"
  function quocienteHTML() {
    const c = C();
    if (!window.PlenariaQuociente || !c.partidos || !c.vagas) return "";
    const q = PlenariaQuociente.quociente(c, S.ano), pz = PlenariaQuociente.puxados(c);
    const eleitos = (sigla) => c.candidatos.filter((x) => x.partido === sigla && (x.situacao || "").startsWith("eleito"));
    const confere = q.simulado && q.partidos.every((p) => p.eleitos.length === eleitos(p.sigla).length && p.eleitos.every((x) => eleitos(p.sigla).includes(x)));
    const mx = q.partidos[0] ? q.partidos[0].total : 1;
    const linhas = q.partidos.filter((p) => p.total > 0).map((p) => { const el = eleitos(p.sigla); const top = p.lista[0];
      return `<div class="qrow"><div class="qp"><b>${esc(p.sigla)}</b><span class="muted">${fmt(p.nominais)} nominais + ${fmt(p.legenda)} legenda</span></div>
        <div class="hbar" style="grid-template-columns:1fr 92px;padding:0"><div class="t"><i style="width:${(p.total / mx) * 100}%"></i></div><div class="x num">${fmt(p.total)}</div></div>
        <div class="qq num" ${tip(`${fmt(p.total)} ÷ QE ${fmt(q.QE)} = ${p.qp.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}`)}>${p.qp.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        <div class="qc">${el.length ? `<b class="num">${el.length}</b>${q.simulado ? ` <span class="muted">(${p.qpCad} QP + ${p.medCad} média)</span>` : ""}` : `<span class="muted">0</span>`}</div>
        <div class="qe">${el.map((x) => `<span class="cpick" data-sq="${x.sq}">${esc(x.urna)} <span class="muted num">${fmt(x.votos)}</span></span>`).join("") || `<span class="muted" style="font-size:12.5px">${top ? `mais votado: ${esc(top.urna)} (${fmt(top.votos)})` : ""}</span>`}</div></div>`; }).join("");
    const pux = pz.map((z) => `<div class="pux"><b>${esc(z.x.urna)}</b> <span class="muted">(${esc(z.x.partido)})</span> foi eleito com <b class="num">${fmt(z.x.votos)}</b> votos, enquanto ${z.acima.slice(0, 3).map((y) => `<b>${esc(y.urna)}</b> <span class="muted">(${esc(y.partido)}, ${fmt(y.votos)})</span>`).join(", ")} ${z.acima.length > 1 ? "ficaram" : "ficou"} de fora. Puxado pelo voto ${q.coligacoes ? "da coligação" : "do partido"}${z.puxador && z.puxador.sq !== z.x.sq ? ` — puxador: <b>${esc(z.puxador.urna)}</b> (${fmt(z.puxador.votos)})` : ""}.</div>`).join("");
    return `<div class="card quoc"><div class="qhead"><div><div class="k">Quociente eleitoral · ${esc(S.ano)}</div>
        <div class="qbig"><b class="num">${fmt(q.QE)}</b><span>votos por cadeira</span></div>
        <div class="muted" style="font-size:13px">${fmt(q.validos)} válidos ÷ ${q.vagas} vagas${q.simulado ? ` · cada eleito precisa de ao menos ${fmt(Math.ceil((+S.ano >= 2022 ? 0.1 : 0.1) * q.QE))} votos (10% do QE)` : ""}</div></div>
        ${q.simulado ? `<span class="qok ${confere ? "" : "bad"}">${confere ? "✔ Recalculado: bate com o resultado oficial" : "✘ Recalculado: não bate — conferir"}</span>` : `<span class="qok neutro">Em ${esc(S.ano)} havia coligações: as cadeiras saíram por coligação</span>`}</div>
      <div class="qtab"><div class="qrow qh"><div>Partido</div><div>Votos (nominal + legenda)</div><div>QP${q.coligacoes ? "*" : ""}</div><div>Cadeiras</div><div>Eleitos</div></div>${linhas}</div>
      ${pux ? `<div class="k" style="margin-top:18px">Quem foi puxado</div>${pux}` : `<p class="muted" style="font-size:13px;margin-top:14px">Nenhum eleito teve menos votos do que alguém que ficou de fora.</p>`}
      <p class="muted" style="font-size:12px;margin-top:12px">QP = votos do partido ÷ QE; a parte inteira dá as cadeiras diretas, as demais saem pelas maiores médias (sobras).${q.coligacoes ? " *Com coligações, o QP valia para a coligação inteira; aqui aparece o que o partido teria sozinho." : ""}</p></div>`;
  }
  function renderRanking() {
    const a = agg();
    const rel = new Set(relevantes(a).map((x) => x.sq));
    let lista = a.cands;
    if (S.busca) { const q = S.busca.toLowerCase(); lista = lista.filter((x) => (x.urna + " " + x.nome + " " + x.partido + " " + x.nr).toLowerCase().includes(q)); }
    const total = lista.length;
    if (!S.rankAll && !S.busca) lista = lista.slice(0, Math.max(15, rel.size));
    const max = a.cands[0] ? a.cands[0].votos : 1;
    const puxSet = new Set(window.PlenariaQuociente && C().partidos ? PlenariaQuociente.puxados(C()).map((z) => z.x.sq) : []);
    $("#ranking").innerHTML = `<div class="blk-h"><div><h2>Os mais <em class="s">votados</em></h2><p class="lead">Clique em um nome para abrir o perfil: foto, desempenho por bairro e histórico na cidade. Use ◯ para separar até 4 candidatos para comparar.</p></div>
      <div class="tools"><input class="search" id="busca" type="search" placeholder="Buscar nome, partido ou número" value="${esc(S.busca)}"></div></div>
      ${quocienteHTML()}
      <div class="rank">${lista.map((x) => {
        const sl = slotOf(x.sq);
        return `<div class="rrow ${rel.has(x.sq) ? "" : "dim"}" data-sq="${x.sq}" role="button" tabindex="0">
          <div class="pos num">${x._pos}º</div>${avatar(x)}
          <div><div class="nm">${esc(x.urna)}</div><div class="meta">${esc(x.partido || "")} · ${esc(x.nr || "")}${situ(x)}${puxSet.has(x.sq) ? `<span class="tag" style="border-color:rgba(224,164,42,.6);color:#ffd780">puxado</span>` : ""}</div></div>
          <div class="bar" ${tip(`<b>${esc(x.urna)}</b><br>${fmt(x.votos)} votos · ${pct(x.votos / a.validos, 2)} dos válidos`)}><i style="width:${(x.votos / max) * 100}%"></i></div>
          <div class="vv num">${fmt(x.votos)}</div><div class="pp num">${pct(x.votos / a.validos)}</div>
          <button class="chk" type="button" data-cmp="${x.sq}" aria-pressed="${!!sl}" title="Comparar" style="${sl ? `background:${sl}` : ""}">${sl ? "✓" : "◯"}</button>
        </div>`;
      }).join("")}</div>
      ${!S.busca && total > lista.length ? `<button class="btn more" id="rank-all" type="button">Ver todos os ${fmt(total)} candidatos</button>` : ""}
      ${S.rankAll && !S.busca ? `<button class="btn more" id="rank-less" type="button">Mostrar só os principais</button>` : ""}`;
  }

  function renderBairros() {
    const el = $("#bairros");
    const head = `<div class="blk-h"><div><h2>Quem venceu em cada <em class="s">bairro</em></h2><p class="lead">Bairro conforme o cadastro do local de votação no TSE. Percentuais sobre os votos válidos do bairro para ${esc(cargoCurto(S.cargo))}.</p></div></div>`;
    if (!porSecao()) { el.innerHTML = head + naoSecao("bairro"); return; }
    const a = agg();
    const bairros = Object.values(a.bairros).sort((x, y) => y.validos - x.validos);
    const vit = {};
    bairros.forEach((b) => b.rank[0] && (vit[b.rank[0][0]] = (vit[b.rank[0][0]] || 0) + 1));
    const lideres = Object.entries(vit).sort((x, y) => y[1] - x[1]);
    const rel = relevantes(a).slice(0, 12);
    const maxShare = Math.max(...rel.flatMap((x) => bairros.map((b) => (b.cand[x.sq] || 0) / (b.validos || 1))), 0.0001);
    el.innerHTML = head + `
      <h4 class="muted" style="margin:0 0 10px;font-weight:600;font-size:13px;letter-spacing:.12em;text-transform:uppercase">Bairros vencidos</h4>
      <div class="grid leader">${lideres.map(([sq, n]) => { const x = a.bySq[sq]; return `<div class="card lchip" data-sq="${sq}" role="button" tabindex="0"><div class="n num">${n}</div>${avatar(x)}<div><div style="font-weight:800">${esc(x.urna)}</div><div class="muted" style="font-size:12.5px">${esc(x.partido || "")} · de ${bairros.length} bairros</div></div></div>`; }).join("")}</div>
      <div class="grid bairros">${bairros.map((b) => {
        const [w, ...rest] = b.rank;
        const x = w && a.bySq[w[0]];
        return `<div class="card bcard"><h3>${esc(b.nome)}</h3><div class="sub">${fmt(b.aptos)} aptos · ${b.locais.size} ${b.locais.size > 1 ? "locais" : "local"} · ${b.secoes.length} ${b.secoes.length > 1 ? "seções" : "seção"} · ${fmt(b.validos)} válidos</div>
          ${x ? `<div class="win" data-sq="${x.sq}" role="button" tabindex="0">${avatar(x)}<div><div class="k">1º no bairro</div><div class="nm">${esc(x.urna)} <span class="muted" style="font-weight:500;font-size:13px">${esc(x.partido || "")}</span></div><div class="vv num">${fmt(w[1])} votos · ${pct(w[1] / b.validos)}</div></div></div>` : ""}
          ${rest.slice(0, 4).map(([sq, v], i) => `<div class="mini" data-sq="${sq}"><span>${i + 2}º ${esc(a.bySq[sq].urna)}</span><span class="num">${fmt(v)} · ${pct(v / b.validos)}</span></div>`).join("")}
        </div>`;
      }).join("")}</div>
      <h4 class="muted" style="margin:30px 0 10px;font-weight:600;font-size:13px;letter-spacing:.12em;text-transform:uppercase">Força de cada candidato relevante por bairro (% dos válidos do bairro)</h4>
      <div class="heat"><table><thead><tr><th>Candidato</th>${bairros.map((b) => `<th>${esc(b.nome)}</th>`).join("")}<th>Cidade</th></tr></thead><tbody>
        ${rel.map((x) => `<tr><td><a href="#" data-sq="${x.sq}" style="color:inherit;text-decoration:none;font-weight:700">${esc(x.urna)}</a> <span class="muted">${esc(x.partido || "")}</span></td>${bairros.map((b) => {
          const v = b.cand[x.sq] || 0, s = v / (b.validos || 1);
          const top = b.rank[0] && b.rank[0][0] === x.sq;
          return `<td class="c num ${top ? "top" : ""}" style="background:rgba(57,135,229,${(0.06 + 0.8 * (s / maxShare)).toFixed(3)})" ${tip(`<b>${esc(x.urna)}</b> em ${esc(b.nome)}<br>${fmt(v)} votos · ${pct(s)} dos válidos${top ? "<br>1º colocado no bairro" : ""}`)}>${pct(s)}</td>`;
        }).join("")}<td class="num">${pct(x.votos / a.validos)}</td></tr>`).join("")}
      </tbody></table></div>
      <div class="legend"><span><i style="background:rgba(57,135,229,.86)"></i>mais forte</span><span><i style="background:rgba(57,135,229,.1)"></i>mais fraco</span><span><i style="box-shadow:inset 0 0 0 2px var(--accent)"></i>venceu no bairro</span></div>`;
  }

  // ------------------------------------------------------------------ mapa interativo: cidade › bairro/distrito › local › seção
  const MAP_ORDEM = ["deputado_federal", "deputado_estadual", "vereador", "prefeito", "governador", "senador", "presidente"];
  function mapEleicoes() {
    const out = [];
    for (const [ano, e] of Object.entries(S.city.eleicoes)) {
      if (e.nivel !== "secao") continue;
      for (const k of Object.keys(e.cargos)) if (!k.endsWith("_2t")) out.push({ ano, cargo: k });
    }
    const r = (k) => { const i = MAP_ORDEM.indexOf(k); return i < 0 ? 99 : i; };
    return out.sort((p, q) => q.ano - p.ano || r(p.cargo) - r(q.cargo));
  }
  let LMAP = null, LLAYER = null;
  function centro(locs) {
    const c = locs.filter((l) => l.lat != null && l.lon != null);
    if (!c.length) return null;
    return [c.reduce((s, l) => s + l.lat, 0) / c.length, c.reduce((s, l) => s + l.lon, 0) / c.length];
  }
  function forcas(a, o, n = 3) {
    return (o.rank || []).slice(0, n).map(([sq, v]) => ({ x: a.bySq[sq], v, p: v / (o.validos || 1) }));
  }
  const miniAv = (x, cls = "av") => avatar(x, cls);
  function forcasHTML(a, o, titulo, extra = "") {
    const top = forcas(a, o);
    const foco = S.map.foco.filter((sq) => a.bySq[sq]);
    const linha = (x, v, i) => `<div class="fz" data-sq="${x.sq}">${i != null ? `<span class="fp">${i}º</span>` : ""}${miniAv(x)}<div class="fn"><b>${esc(x.urna)}</b><span>${esc(x.partido || "")}${x.situacao ? " · " + esc(situTxt(x.situacao)) : ""}</span></div><div class="fv"><b class="num">${fmt(v)}</b><span class="num">${pct(v / (o.validos || 1))}</span></div></div>`;
    return `<div class="forcas"><div class="ft">${titulo}</div><div class="fs2">${fmt(o.validos)} votos válidos${o.aptos ? ` · ${fmt(o.aptos)} aptos` : ""}</div>
      ${top.map((t, i) => linha(t.x, t.v, i + 1)).join("") || `<div class="muted">Sem votos.</div>`}
      ${foco.length ? `<div class="fk">Seus escolhidos</div>${foco.map((sq) => { const pos = (o.rank || []).findIndex(([q]) => q === sq); return linha(a.bySq[sq], o.cand[sq] || 0, pos < 0 ? null : pos + 1); }).join("")}` : ""}${extra}</div>`;
  }
  function renderMapa() {
    const el = $("#mapa");
    const opts = mapEleicoes();
    const head = (tools) => `<div class="blk-h"><div><h2>Mapa das <em class="s">forças</em></h2><p class="lead">Toque num balão: bairro ou distrito, depois o local de votação e a seção. Cada balão mostra as três maiores forças ali.</p></div>${tools || ""}</div>`;
    if (!opts.length) {
      el.innerHTML = head() + `<div class="notice"><b>O mapa precisa da votação por seção do TSE</b>, que traz o bairro e as coordenadas de cada local de votação. Assim que o acesso ao TSE for liberado: <code>python3 scripts/plenaria.py tse --municipio ${esc(S.city.meta.municipio)} --ano 2026 --ano 2024 --baixar</code> (2026 = deputados; 2024 = vereadores e prefeito, com fotos).</div>`;
      return;
    }
    if (!opts.some((o) => o.ano === S.map.ano && o.cargo === S.map.cargo)) Object.assign(S.map, opts[0], { bairro: null, local: null, secao: null, zoom: false, foco: [] });
    const a = agg(S.map.ano, S.map.cargo);
    const rel = relevantes(a).slice(0, 40);
    const tools = `<div class="tools"><select class="pill" id="map-el">${opts.map((o) => `<option value="${o.ano}|${o.cargo}" ${o.ano === S.map.ano && o.cargo === S.map.cargo ? "selected" : ""}>${o.ano} · ${esc(cargoCurto(o.cargo))}</option>`).join("")}</select>
      <select class="pill" id="map-rx"><option value="">Cor: quem lidera</option>${rel.map((x) => `<option value="${x.sq}" ${x.sq === S.map.rx ? "selected" : ""}>Raio-X de ${esc(x.urna)}</option>`).join("")}</select>
      ${S.map.foco.length < 3 ? `<select class="pill" id="map-foco"><option value="">+ Escolher candidato</option>${rel.filter((x) => !S.map.foco.includes(x.sq)).map((x) => `<option value="${x.sq}">${esc(x.urna)} (${esc(x.partido || "")})</option>`).join("")}</select>` : ""}</div>`;
    const chips = S.map.foco.length ? `<div class="cmp-pick">${S.map.foco.map((sq) => { const x = a.bySq[sq]; return x ? `<span class="cpick">${avatar(x)}<b>${esc(x.urna)}</b><button type="button" data-unfoco="${sq}" aria-label="Remover">×</button></span>` : ""; }).join("")}</div>` : "";
    const rxLeg = S.map.rx && a.bySq[S.map.rx] ? `<div class="legend" style="margin:0 0 10px">Raio-X de <b style="margin:0 6px">${esc(a.bySq[S.map.rx].urna)}</b>${CLASSES.map(([, n, ic, c]) => `<span><i style="background:${c}"></i>${ic} ${n}</span>`).join("")}</div>` : "";
    el.innerHTML = head(tools) + chips + rxLeg + `<div class="mapx"><div id="lmap" class="lmap" role="application" aria-label="Mapa de ${esc(S.city.meta.municipio)}"></div><aside class="mpanel" id="mpanel"></aside></div>`;
    desenharMapa();
  }
  function desenharMapa() {
    const a = agg(S.map.ano, S.map.cargo), m = S.city.meta;
    const bairros = Object.values(a.bairros).sort((p, q) => q.validos - p.validos);
    // cores fixas: as 3 maiores forças da cidade; demais cinza
    const top3 = forcas(a, { rank: a.cands.map((x) => [x.sq, x.votos]), validos: a.validos }).map((t) => t.x.sq);
    const cor = (sq) => { const i = top3.indexOf(sq); return i < 0 ? "var(--other)" : SLOTS[i]; };
    const box = $("#lmap");
    if (!window.L) { box.innerHTML = `<div class="notice" style="margin:16px">Mapa indisponível (Leaflet não carregou). Use a lista ao lado.</div>`; }
    else {
      if (LMAP) { LMAP.remove(); LMAP = null; }
      LMAP = L.map(box, { zoomControl: true, attributionControl: true, scrollWheelZoom: false });
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 19, subdomains: "abcd", attribution: "© OpenStreetMap · © CARTO" }).addTo(LMAP);
      LLAYER = L.layerGroup().addTo(LMAP);
    }
    const vmax = Math.max(...bairros.map((b) => b.validos), 1);
    const balao = (o, nome, latlng, nivel, id) => {
      const rx = S.map.rx && a.bySq[S.map.rx];
      const w = rx || (o.rank && o.rank[0] ? a.bySq[o.rank[0][0]] : null);
      const sz = Math.round(44 + 30 * Math.sqrt(o.validos / vmax));
      let ring = w ? cor(w.sq) : "var(--other)", rot = esc(nome);
      if (rx) { const base = rx.votos / (a.validos || 1), idx = base ? (((o.cand[rx.sq] || 0) / (o.validos || 1)) / base) * 100 : 0, cl = classe(idx); ring = cl[3]; rot = `${esc(nome)} · ${cl[2]} ${Math.round(idx)}`; }
      const html = `<div class="bal" style="--c:${ring};--s:${sz}px">${w ? avatar(w, "bav") : ""}<span class="bn">${rot}</span></div>`;
      const mk = L.marker(latlng, { icon: L.divIcon({ html, className: "balw", iconSize: [sz, sz], iconAnchor: [sz / 2, sz / 2] }), riseOnHover: true, keyboard: true, title: nome });
      mk.on("click", () => selecionar(nivel, id));
      const drill = nivel === "bairro" ? `<button type="button" class="btn primary fdrill" data-mdrill="${esc(id)}">Ver locais e seções ›</button>` : "";
      mk.bindPopup(() => forcasHTML(a, o, esc(nome), drill), { className: "fpop", maxWidth: 320, minWidth: 260, offset: [0, -sz / 2 + 6], autoPanPadding: [30, 30] });
      return mk;
    };
    const painel = () => {
      const p = $("#mpanel");
      const b = S.map.bairro && a.bairros[S.map.bairro], l = S.map.local && a.locais[S.map.local], sc = S.map.secao && a.secoes[S.map.secao];
      const crumb = `<div class="crumb"><a href="#" data-mnav="cidade">${esc(m.municipio)}</a>${b ? ` › <a href="#" data-mnav="bairro">${esc(b.nome)}</a>` : ""}${l ? ` › <a href="#" data-mnav="local">${esc(l.nome)}</a>` : ""}${sc ? ` › Seção ${sc.secao}` : ""}</div>`;
      let corpo;
      if (sc) corpo = forcasHTML(a, sc, `Seção ${sc.secao} <span class="muted">· ${sc.zona}ª zona</span>`);
      else if (l) corpo = forcasHTML(a, l, esc(l.nome)) + `<div class="fk">Seções deste local</div><div class="lst">${l.secoes.map((sid) => a.secoes[sid]).sort((p, q) => p.secao - q.secao).map((s) => { const w = s.rank[0] && a.bySq[s.rank[0][0]]; return `<button type="button" class="li" data-msec="${s.id}"><span>Seção <b>${s.secao}</b></span><span class="muted">${w ? esc(w.urna) + " · " + pct(s.rank[0][1] / (s.validos || 1)) : ""}</span></button>`; }).join("")}</div>`;
      else if (b) corpo = forcasHTML(a, b, esc(b.nome)) + `<div class="fk">Locais de votação</div><div class="lst">${[...b.locais].map((id) => a.locais[id]).sort((p, q) => q.validos - p.validos).map((lo) => { const w = lo.rank[0] && a.bySq[lo.rank[0][0]]; return `<button type="button" class="li" data-mloc="${esc(lo.id)}"><span>${esc(lo.nome)} <span class="muted">· ${lo.secoes.length} seç.</span></span><span class="muted">${w ? esc(w.urna) : ""}</span></button>`; }).join("")}</div>`;
      else corpo = forcasHTML(a, { rank: a.cands.map((x) => [x.sq, x.votos]), validos: a.validos, cand: Object.fromEntries(a.cands.map((x) => [x.sq, x.votos])) }, `${esc(m.municipio)} inteira`) + `<div class="fk">Bairros e distritos</div><div class="lst">${bairros.map((bb) => { const w = bb.rank[0] && a.bySq[bb.rank[0][0]]; return `<button type="button" class="li" data-mbai="${esc(bb.nome)}"><span>${esc(bb.nome)} <span class="muted">· ${bb.secoes.length} seç.</span></span><span class="muted">${w ? esc(w.urna) + " · " + pct(bb.rank[0][1] / (bb.validos || 1)) : ""}</span></button>`; }).join("")}</div>`;
      p.innerHTML = crumb + corpo;
      if (window.gsap) gsap.from("#mpanel > *", { y: 12, opacity: 0, stagger: 0.04, duration: 0.35 });
    };
    const desenhar = () => {
      painel();
      if (!LMAP) return;
      LLAYER.clearLayers();
      const pts = [];
      if (!S.map.bairro || !S.map.zoom) {
        for (const b of bairros) {
          const c = centro([...b.locais].map((id) => a.locais[id]));
          if (c) { balao(b, b.nome, c, "bairro", b.nome).addTo(LLAYER); pts.push(c); }
        }
      } else {
        const b = a.bairros[S.map.bairro];
        for (const id of b.locais) {
          const lo = a.locais[id];
          if (lo.lat == null) continue;
          balao(lo, lo.nome, [lo.lat, lo.lon], "local", id).addTo(LLAYER); pts.push([lo.lat, lo.lon]);
        }
      }
      desenharMapa.fit = () => {
        if (!LMAP) return;
        LMAP.invalidateSize();
        const pad = box.clientWidth < 500 ? 56 : 90;
        if (pts.length > 1) LMAP.fitBounds(L.latLngBounds(pts), { padding: [pad, pad], maxZoom: 16, animate: true });
        else if (pts.length) LMAP.setView(pts[0], 15);
        else LMAP.setView([-4.19, -40.37], 13);
      };
      desenharMapa.fit();
      setTimeout(() => LMAP && LMAP.invalidateSize(), 50);
    };
    function selecionar(nivel, id) {
      if (nivel === "bairro") Object.assign(S.map, { bairro: id, local: null, secao: null });
      if (nivel === "local") Object.assign(S.map, { local: id, secao: null });
      if (nivel === "secao") S.map.secao = id;
      painel();
    }
    desenharMapa.nav = (alvo, id) => {
      if (alvo === "cidade") Object.assign(S.map, { bairro: null, local: null, secao: null, zoom: false });
      if (alvo === "bairro") Object.assign(S.map, { local: null, secao: null });
      if (alvo === "drill") { Object.assign(S.map, { bairro: id, local: null, secao: null, zoom: true }); if (LMAP) LMAP.closePopup(); }
      if (alvo === "local") S.map.secao = null;
      if (alvo === "bai") { Object.assign(S.map, { bairro: id, local: null, secao: null, zoom: true }); return desenhar(); }
      if (alvo === "loc") { if (!S.map.zoom) { S.map.zoom = true; desenhar(); } selecionar("local", id); if (LLAYER) LLAYER.eachLayer((mk) => { if (mk.options.title === a.locais[id].nome) mk.openPopup(); }); return; }
      if (alvo === "sec") return selecionar("secao", id);
      desenhar();
    };
    desenhar();
  }

  function renderSecoes() {
    const el = $("#secoes");
    const head = (extra = "") => `<div class="blk-h"><div><h2>Seção por <em class="s">seção</em></h2><p class="lead">Selecione até 4 seções para comparar lado a lado. Escolha um candidato para ver onde ele foi mais forte.</p></div>${extra}</div>`;
    if (!porSecao()) { el.innerHTML = head() + naoSecao("seção"); return; }
    const a = agg();
    const bairros = Object.keys(a.bairros).sort((p, q) => p.localeCompare(q, "pt-BR"));
    const rel = relevantes(a);
    const cand = S.secCand && a.bySq[S.secCand];
    const tools = `<div class="tools"><select class="pill" id="sec-bairro"><option value="">Todos os bairros</option>${bairros.map((b) => `<option ${b === S.secBairro ? "selected" : ""}>${esc(b)}</option>`).join("")}</select>
      <select class="pill" id="sec-cand"><option value="">Candidato: nenhum</option>${(cand && !rel.includes(cand) ? [cand, ...rel] : rel).map((x) => `<option value="${x.sq}" ${x.sq === S.secCand ? "selected" : ""}>${esc(x.urna)}</option>`).join("")}</select>
      ${S.secSel.length ? `<button class="btn" id="sec-clear" type="button">Limpar seleção (${S.secSel.length})</button>` : ""}</div>`;
    let secs = Object.values(a.secoes).filter((s) => !S.secBairro || s.bairro === S.secBairro);
    const key = { validos: (s) => -s.validos, secao: (s) => s.zona * 1e5 + s.secao, cand: (s) => -((s.cand[S.secCand] || 0) / (s.validos || 1)), aptos: (s) => -(s.aptos || 0) };
    const sortBy = S.secSort === "cand" && !cand ? "validos" : S.secSort;
    secs.sort((p, q) => key[sortBy](p) - key[sortBy](q));
    const th = (k, t, r) => `<th class="${r ? "r" : ""}" data-sort="${k}">${t}${sortBy === k ? " ↓" : ""}</th>`;
    el.innerHTML = head(tools) + `<div class="tbl-wrap"><table class="tbl"><thead><tr>
      <th></th>${th("secao", "Zona/Seção")}<th>Local</th><th>Bairro</th>${th("aptos", "Aptos", 1)}${th("validos", "Válidos", 1)}<th>1º colocado</th><th class="r">Votos</th>
      ${cand ? th("cand", esc(cand.urna) + " (%)", 1) : ""}</tr></thead><tbody>
      ${secs.map((s) => { const w = s.rank[0]; const on = S.secSel.includes(s.id); const v = cand ? s.cand[cand.sq] || 0 : 0;
        return `<tr class="${on ? "sel" : ""}" data-sec="${s.id}"><td><span class="chk" aria-pressed="${on}" style="${on ? "background:var(--accent);color:#000" : ""}">${on ? "✓" : ""}</span></td>
          <td class="num">${s.zona}ª / <b>${s.secao}</b>${s.agregadas ? ` <span class="muted" title="seções agregadas">+${s.agregadas.join(", ")}</span>` : ""}</td><td>${esc(s.localNome)}</td><td>${esc(s.bairro)}</td>
          <td class="r num">${fmt(s.aptos)}</td><td class="r num">${fmt(s.validos)}</td>
          <td>${w ? esc(a.bySq[w[0]].urna) : "—"}</td><td class="r num">${w ? `${fmt(w[1])} <span class="muted">${pct(w[1] / s.validos)}</span>` : ""}</td>
          ${cand ? `<td class="r num"><b>${fmt(v)}</b> <span class="muted">${pct(v / (s.validos || 1))}</span></td>` : ""}</tr>`; }).join("")}
      </tbody></table></div>
      ${S.secSel.length ? `<div class="grid cmp-secs">${S.secSel.map((id) => { const s = a.secoes[id]; if (!s) return ""; const mx = s.rank[0] ? s.rank[0][1] : 1;
        return `<div class="card"><h4>Seção ${s.secao} <span class="muted" style="font-weight:500">· ${s.zona}ª zona</span></h4><div class="muted" style="font-size:12.5px;margin-bottom:10px">${esc(s.localNome)} · ${esc(s.bairro)} · ${fmt(s.validos)} válidos</div>
          ${s.rank.slice(0, 8).map(([sq, v]) => `<div class="hbar" data-sq="${sq}" style="grid-template-columns:110px 1fr 70px;cursor:pointer"><div class="lb">${esc(a.bySq[sq].urna)}</div><div class="t"><i style="width:${(v / mx) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / s.validos, 0)}</div></div>`).join("")}</div>`; }).join("")}</div>` : ""}`;
  }

  function renderComparar() {
    const el = $("#comparar");
    const a = agg();
    S.cmp = S.cmp.filter((sq) => a.bySq[sq]);
    const opts = a.cands.filter((x) => !S.cmp.includes(x.sq)).slice(0, 80);
    const head = `<div class="blk-h"><div><h2>Comparar <em class="s">candidatos</em></h2><p class="lead">Até 4 nomes. Cada um mantém a mesma cor em todos os gráficos desta seção.</p></div>
      <div class="tools">${S.cmp.length < 4 ? `<select class="pill" id="cmp-add"><option value="">+ Adicionar candidato</option>${opts.map((x) => `<option value="${x.sq}">${esc(x.urna)} (${esc(x.partido || "")})</option>`).join("")}</select>` : ""}
      ${porSecao() ? `<div class="seg" id="cmp-by"><button type="button" data-by="bairro" aria-pressed="${S.cmpBy === "bairro"}">Bairros</button><button type="button" data-by="local" aria-pressed="${S.cmpBy === "local"}">Locais</button></div>
      <div class="seg" id="cmp-mode"><button type="button" data-mode="votos" aria-pressed="${S.cmpMode === "votos"}">Votos</button><button type="button" data-mode="pct" aria-pressed="${S.cmpMode === "pct"}">% válidos</button></div>` : ""}</div></div>`;
    if (!S.cmp.length) { el.innerHTML = head + `<div class="notice">Escolha candidatos no seletor acima ou marque ◯ na lista dos mais votados.</div>`; return; }
    const sel = S.cmp.map((sq) => a.bySq[sq]);
    const chips = `<div class="cmp-pick">${sel.map((x, i) => `<span class="cpick"><i style="background:${SLOTS[i]}"></i>${avatar(x)}<b>${esc(x.urna)}</b><span class="muted num">${fmt(x.votos)}</span><button type="button" data-rm="${x.sq}" aria-label="Remover">×</button></span>`).join("")}</div>`;
    let grupos;
    if (porSecao()) {
      const src = S.cmpBy === "bairro" ? Object.values(a.bairros) : Object.values(a.locais);
      grupos = src.sort((p, q) => q.validos - p.validos).map((g) => ({ nome: g.nome, validos: g.validos, v: sel.map((x) => g.cand[x.sq] || 0) }));
    } else grupos = [{ nome: S.city.meta.municipio + " (total)", validos: a.validos, v: sel.map((x) => x.votos) }];
    const val = (g, i) => (S.cmpMode === "pct" && porSecao() ? g.v[i] / (g.validos || 1) : g.v[i]);
    const mx = Math.max(...grupos.flatMap((g) => g.v.map((_, i) => val(g, i))), 1e-9);
    el.innerHTML = head + chips + `<div class="gbars">${grupos.map((g) => `<div class="g"><div class="lb">${esc(g.nome)}<div class="muted" style="font-size:12px">${fmt(g.validos)} válidos</div></div><div class="bars">${sel.map((x, i) => {
      const v = val(g, i); const txt = S.cmpMode === "pct" && porSecao() ? pct(v) : fmt(v);
      return `<div class="b" ${tip(`<b>${esc(x.urna)}</b> · ${esc(g.nome)}<br>${fmt(g.v[i])} votos · ${pct(g.v[i] / (g.validos || 1))}`)}><i style="width:${(v / mx) * 82}%;background:${SLOTS[i]}"></i><span class="num">${txt}</span></div>`;
    }).join("")}</div></div>`).join("")}</div>`;
  }

  function renderHistorico() {
    const ctx = (S.city.contexto || []).filter((c) => c.turno === 1);
    const anos = [...new Set(ctx.map((c) => c.ano))].sort();
    const linha = anos.map((ano) => ctx.find((c) => c.ano === ano && c.aptos)).filter(Boolean);
    const el = $("#historico");
    if (!linha.length) { el.innerHTML = ""; return; }
    const W = 560, H = 240, P = { l: 16, r: 16, t: 30, b: 30 };
    const bw = (W - P.l - P.r) / linha.length;
    const amax = Math.max(...linha.map((c) => c.aptos));
    const bars = linha.map((c, i) => {
      const h = ((H - P.t - P.b) * c.aptos) / amax, x = P.l + i * bw + bw * 0.2, y = H - P.b - h;
      return `<rect x="${x}" y="${y}" width="${bw * 0.6}" height="${h}" rx="4" fill="${c.ano == S.ano ? "var(--accent)" : "#3987e5"}" ${tip(`<b>${c.ano}</b><br>${fmt(c.aptos)} eleitores aptos`)}/>
        <path d="M${x} ${H - P.b}h${bw * 0.6}" stroke="var(--surface)" stroke-width="0"/>
        <text x="${x + bw * 0.3}" y="${H - 10}" text-anchor="middle">${c.ano}</text>
        <text class="lab" x="${x + bw * 0.3}" y="${y - 8}" text-anchor="middle">${(c.aptos / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mil</text>`;
    }).join("");
    const pts = linha.map((c, i) => [P.l + i * bw + bw / 2, c.comparecimento / c.aptos]);
    const pmin = Math.min(...pts.map((p) => p[1])) - 0.04, pmax = Math.max(...pts.map((p) => p[1])) + 0.03;
    const py = (v) => P.t + (H - P.t - P.b) * (1 - (v - pmin) / (pmax - pmin));
    const line = `<polyline points="${pts.map(([x, v]) => `${x},${py(v)}`).join(" ")}" fill="none" stroke="#3987e5" stroke-width="2"/>` +
      pts.map(([x, v], i) => `<circle cx="${x}" cy="${py(v)}" r="5" fill="${linha[i].ano == S.ano ? "var(--accent)" : "#3987e5"}" stroke="var(--surface)" stroke-width="2" ${tip(`<b>${linha[i].ano}</b><br>${fmt(linha[i].comparecimento)} de ${fmt(linha[i].aptos)} (${pct(v)})<br>${fmt(linha[i].abstencoes)} abstenções`)}/>
        <text class="lab" x="${x}" y="${py(v) - 12}" text-anchor="middle">${pct(v, 1)}</text><text x="${x}" y="${H - 10}" text-anchor="middle">${linha[i].ano}</text>`).join("");
    el.innerHTML = `<div class="blk-h"><div><h2>O eleitorado de <em class="s">${esc(S.city.meta.municipio)}</em> no tempo</h2><p class="lead">1º turno de cada eleição. Fonte: ${esc([...new Set(linha.map((c) => c.fonte))].join("; "))}.</p></div></div>
      <div class="grid hist"><div class="card"><div style="font-weight:800">Eleitores aptos</div><svg class="chart" viewBox="0 0 ${W} ${H}">${bars}</svg></div>
      <div class="card"><div style="font-weight:800">Comparecimento</div><svg class="chart" viewBox="0 0 ${W} ${H}">${line}</svg></div></div>`;
  }

  function renderFooter() {
    const m = S.city.meta;
    $("#foot").innerHTML = `<b>Fontes.</b> ${esc(E().fonte)}. Dados de ${esc(m.municipio)}/${esc(m.uf)} (código TSE ${esc(m.cd_tse || "—")}, IBGE ${esc(m.cd_ibge || "—")}), atualizados em ${esc(m.atualizado || "—")}.
      Votos válidos = nominais + legenda. Bairro e coordenadas vêm do cadastro de locais de votação do TSE.<br>
      Anos disponíveis: ${Object.keys(S.city.eleicoes).sort().reverse().map((a) => `${a} (${S.city.eleicoes[a].nivel === "secao" ? "por seção" : "totais municipais"})`).join(", ")}.`;
  }


  // ------------------------------------------------------------------ ficha da cidade
  const SELOS = {
    "confirmado": ["✔", "Confirmado", "oficial ou 2+ fontes independentes"],
    "declaracao": ["❝", "Declaração", "alguém disse; registrado como fala"],
    "uma-fonte": ["①", "Uma fonte só", "ainda sem segunda fonte"],
    "pesquisa": ["▤", "Pesquisa registrada", "instituto e nº de registro"],
    "a-conferir": ["?", "A conferir", "não verificado"],
    "local": ["◆", "Informação local", "conhecimento seu; fica só no seu computador"],
  };
  const selo = (k) => { const v = SELOS[k] || SELOS["a-conferir"]; return `<span class="selo selo-${esc(k)}" title="${esc(v[2])}"><b>${v[0]}</b> ${esc(v[1])}</span>`; };
  const fontes = (fs) => (fs || []).map((f) => `<a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.nome)} ↗</a>`).join(" · ");
  const dataBR = (d) => { if (!d) return ""; const [y, m, dd] = String(d).split("-"); const mes = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][+m - 1]; return dd ? `${+dd} ${mes} ${y}` : m ? `${mes} ${y}` : y; };


  // ------------------------------------------------------------------ blocos locais: lideranças, placar, governador, 2028
  const COR_GRUPO = { "situação": "var(--s1)", "oposição": "var(--s2)", "terceira via": "var(--s3)", "opinião": "#8d8b82" };
  function blocosLocaisHTML(sub) {
    const L = S.local || {};
    let h = "";
    if ((L.liderancas || []).length) {
      const mx = Math.max(...L.liderancas.map((l) => Math.max(l.fed, l.est)), 1);
      const ordem = ["situação", "oposição", "terceira via", "opinião"];
      h += sub(`Força das lideranças em 2026 <span class="muted" style="font-weight:500;font-size:14px;text-transform:none;letter-spacing:0">· votos em Varjota dos deputados que cada uma apoiou</span>`) +
        `<div class="card lid">${ordem.map((g) => { const ls = L.liderancas.filter((l) => l.grupo === g); if (!ls.length) return ""; const tf = ls.reduce((t, l) => t + l.fed, 0), te = ls.reduce((t, l) => t + l.est, 0);
          return `<div class="lg"><div class="lgh"><span class="dot" style="background:${COR_GRUPO[g]}"></span><b>${esc(cap(g))}</b><span class="muted num">federal ${fmt(tf)} · estadual ${fmt(te)}</span></div>
            ${ls.map((l) => `<div class="lr"><div class="ln"><b>${esc(l.nome)}</b><span class="muted">${esc(l.deps)}</span></div>
              <div class="lb2"><div class="hbar" style="grid-template-columns:1fr 64px;padding:2px 0" ${tip(`<b>${esc(l.nome)}</b> · federal<br>${fmt(l.fed)} votos`)}><div class="t"><i style="width:${(l.fed / mx) * 100}%;background:${COR_GRUPO[g]}"></i></div><div class="x num">${l.fed ? fmt(l.fed) : "—"}</div></div>
              <div class="hbar" style="grid-template-columns:1fr 64px;padding:2px 0" ${tip(`<b>${esc(l.nome)}</b> · estadual<br>${fmt(l.est)} votos`)}><div class="t"><i style="width:${(l.est / mx) * 100}%;background:${COR_GRUPO[g]};opacity:.55"></i></div><div class="x num">${l.est ? fmt(l.est) : "—"}</div></div></div></div>`).join("")}</div>`; }).join("")}
          <div class="legend"><span><i style="background:var(--ink-2)"></i>barra cheia = federal</span><span><i style="background:var(--ink-2);opacity:.55"></i>barra clara = estadual</span><span>◆ informação local · fonte dos votos: Band (apuração por município)</span></div></div>`;
    }
    if (L.placar) {
      const P = L.placar, cores = ["var(--s1)", "var(--s2)", "#8d8b82", "var(--s3)", "#5d5c57", "#3a3936", "#2c2b29"];
      const barra = (i) => `<div class="stk">${P.linhas.map((l, j) => `<i style="width:${(l[i] / P.total) * 100}%;background:${cores[j]}" ${tip(`<b>${esc(l[0])}</b><br>${fmt(l[i])} votos · ${pct(l[i] / P.total)}`)}></i>`).join("")}</div>`;
      h += sub(`Placar de 2026 <span class="muted" style="font-weight:500;font-size:14px;text-transform:none;letter-spacing:0">· sobre ${fmt(P.total)} votos (${fmt(P.abstencoes)} faltaram)</span>`) +
        `<div class="card placar"><div class="pl"><b>Federal</b>${barra(1)}</div><div class="pl"><b>Estadual</b>${barra(2)}</div>
        <div class="legend">${P.linhas.map((l, j) => `<span><i style="background:${cores[j]}"></i>${esc(l[0])} <b class="num" style="margin-left:4px">${pct(l[1] / P.total)}</b> / <b class="num">${pct(l[2] / P.total)}</b></span>`).join("")}</div></div>`;
    }
    if (L.governador) {
      const G = L.governador, tot = G.ciro + G.elmano;
      h += sub("Governador em Varjota: o recado das urnas") + `<div class="grid gov"><div class="card"><div class="gv"><div><span class="muted">Ciro Gomes</span><b class="num">${fmt(G.ciro)}</b><span class="num">${pct(G.ciro / tot)}</span></div><div><span class="muted">Elmano de Freitas</span><b class="num">${fmt(G.elmano)}</b><span class="num">${pct(G.elmano / tot)}</span></div></div>
        <div class="stk" style="margin-top:14px"><i style="width:${(G.ciro / tot) * 100}%;background:var(--s2)"></i><i style="width:${(G.elmano / tot) * 100}%;background:var(--s1)"></i></div>
        <div class="gvd"><div><b class="num">+${fmt(G.margem2024)}</b><span>vitória do Elmo em 2024</span></div><div class="arrow">→</div><div><b class="num">−${fmt(G.ciro - G.elmano)}</b><span>Elmano em 2026</span></div><div><b class="num">≈ ${fmt(G.margem2024 + G.ciro - G.elmano)}</b><span>votos de virada</span></div></div></div>
        <div class="card"><div class="k" style="font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin-bottom:8px">Leitura</div>${G.leitura.map((t) => `<div class="pux">${esc(t)}</div>`).join("")}</div></div>`;
    }
    if ((L.cenario2028 || []).length) h += sub("Cenário de 2028") + `<div class="grid analise">${L.cenario2028.map((a, i) => `<div class="card acard"><div class="n">${String(i + 1).padStart(2, "0")}</div><div><div class="tt">${esc(a.titulo)}</div><p>${esc(a.texto)}</p></div></div>`).join("")}</div>`;
    if ((L.raony || []).length) h += sub("Estratégia: Raony") + `<div class="card">${L.raony.map((t) => `<div class="pux">${esc(t)}</div>`).join("")}</div>`;
    if ((L.divergencias || []).length) h += sub("Divergências a resolver") + `<div class="card diverg">${L.divergencias.map((t) => `<div class="pux">⚠ ${esc(t)}</div>`).join("")}</div>`;
    if ((L.pendencias || []).length) h += sub("Pendências") + `<div class="card">${L.pendencias.map((t) => `<div class="pux">☐ ${esc(t)}</div>`).join("")}</div>`;
    return h;
  }
  const POSICAO = { situacao: ["Situação", "ok"], oposicao: ["Oposição", "op"], rompido: ["Rompido", "rp"], independente: ["Independente", ""] };
  function renderFicha() {
    const el = $("#ficha"), f = S.ficha, L = S.local || {}, m = S.city.meta;
    const head = `<div class="blk-h"><div><h2>Ficha de <em class="s">${esc(m.municipio)}</em></h2><p class="lead">Quem manda, com quem, que força tem e o que aconteceu. Cada item mostra a fonte e o grau de confiança.</p></div>
      <div class="selos-leg">${Object.keys(SELOS).map(selo).join("")}</div></div>`;
    if (!f && !S.local) { el.innerHTML = head + `<div class="notice">Ainda não há ficha para ${esc(m.municipio)}. Ela fica em <code>data/${esc(m.uf.toLowerCase())}/${esc(m.slug)}.ficha.js</code>.</div>`; return; }
    const F = f || {};
    const fatos = [...(F.fatos || []), ...(L.fatos || []).map((x) => ({ selo: "local", ...x }))].sort((a, b) => String(b.data).localeCompare(String(a.data)));
    const sub = (t) => `<h3 class="fh">${t}</h3>`;
    const grupos = L.grupos || F.grupos || [];
    const ligado = (d) => `<div class="lig"><div><b data-rel="${esc(d.nome)}" role="button" tabindex="0" class="relk">${esc(d.nome)}</b> <span class="muted">${esc([d.cargo, d.partido].filter(Boolean).join(" · "))}</span></div>
      <div class="r">${esc(d.resultado || "")}${d.votosCidade != null ? ` · <b class="num">${fmt(d.votosCidade)}</b> em ${esc(m.municipio)}` : d.votosCidadeTxt ? ` · ${esc(d.votosCidadeTxt)} em ${esc(m.municipio)}` : ""}</div>
      ${d.selo ? `<div class="f">${selo(d.selo)} ${fontes(d.fontes)}</div>` : ""}</div>`;
    el.innerHTML = head +
      `<div class="grid poder">${(F.poder || []).map((p) => `<div class="card pcard"><div class="l">${esc(p.papel)}</div><div class="v"${acharRelatorio([p.nome]) ? ` data-rel="${esc(p.nome)}" role="button" tabindex="0" style="cursor:pointer"` : ""}>${esc(p.nome)}</div>${p.detalhe ? `<div class="d">${esc(p.detalhe)}</div>` : ""}<div class="f">${selo(p.selo)} ${fontes(p.fontes)}</div></div>`).join("")}</div>` +
      ((F.quocientes || []).length ? sub("Quocientes da eleição geral · Ceará") + `<div class="grid qgeral">${F.quocientes.map((q) => `<div class="card"><div class="k" style="font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted)">${esc(q.titulo)}</div>
        <div class="qbig" style="margin:8px 0 6px">${q.qe ? `<b class="num">${fmt(q.qe)}</b><span>votos por cadeira (quociente eleitoral)</span>` : `<b style="font-size:24px;color:var(--ink-2)">a confirmar</b>`}</div>
        ${q.itens.map((it) => `<div class="pux">${esc(it.texto)} ${selo(it.selo)}<div class="fs" style="margin-top:4px;font-size:12px">${fontes(it.fontes)}</div></div>`).join("")}</div>`).join("")}</div>` : "") +
      ((S.rel && S.rel.pessoas.length) ? sub("Relatórios por pessoa") + `<div class="relchips">${S.rel.pessoas.map((r) => { const c = acharCandidato(r.nomes); return `<button type="button" class="cpick" data-rel="${esc(r.nomes[0])}">${avatar({ urna: r.nomes[0], foto: c && c.x.foto, wiki: r.wiki })}<b>${esc(r.nomes[0])}</b><span class="muted">${esc(r.partido || "")}</span></button>`; }).join("")}</div>` : "") +
      (grupos.length ? sub("Grupos políticos") + `<div class="grid grupos">${grupos.map((g, i) => { const [pl, pc] = POSICAO[g.posicao] || [g.posicao || "", ""]; return `<div class="card gcard" style="--g:${SLOTS[i] || "var(--other)"}">
        <div class="gh"><div><div class="l">${esc(g.nome)}</div><div class="v"${acharRelatorio([g.lider]) ? ` data-rel="${esc(g.lider)}" role="button" tabindex="0" class="relk"` : ""}>${esc(g.lider || "")}</div></div>${pl ? `<span class="pos ${pc}">${esc(pl)}</span>` : ""}</div>
        ${g.resumo ? `<p class="d">${esc(g.resumo)}</p>` : ""}
        ${(g.ligados || []).length ? `<div class="k">Deputados e lideranças ligados</div>${g.ligados.map(ligado).join("")}` : ""}
        ${g.vereadores ? `<div class="k">Câmara</div><p class="d">${esc(g.vereadores)}</p>` : ""}
        ${g.forca ? `<div class="forca"><span>Força nas urnas 2026</span><b>${esc(g.forca)}</b></div>` : ""}</div>`; }).join("")}</div>` : "") +
      blocosLocaisHTML(sub) +
      ((L.analise || []).length ? sub(`Leitura <span class="muted" style="font-weight:500;font-size:14px">· análise, não é fato</span>`) + `<div class="grid analise">${L.analise.map((a, i) => `<div class="card acard"><div class="n">${String(i + 1).padStart(2, "0")}</div><div><div class="tt">${esc(a.titulo)}</div><p>${esc(a.texto)}</p></div></div>`).join("")}</div>` : "") +
      ((F.acompanhar || []).length ? sub("Acompanhar") + `<div class="grid acomp">${F.acompanhar.map((a) => `<div class="card wcard"><div class="st">${esc(a.status || "")}</div><div class="tt">${esc(a.titulo)}</div><p>${esc(a.porque || "")}</p><div class="f">${fontes(a.fontes)}</div></div>`).join("")}</div>` : "") +
      sub("Linha do tempo") +
      `<div class="fatos">${fatos.map((x) => `<article class="fato"><div class="dt">${esc(dataBR(x.data))}</div><div><div class="tt">${esc(x.titulo)} ${selo(x.selo)}</div>${x.resumo ? `<p>${esc(x.resumo)}</p>` : ""}${x.nota ? `<p class="nota">${esc(x.nota)}</p>` : ""}<div class="fs">${fontes(x.fontes)}</div></div></article>`).join("")}</div>
      ${F.observacao ? `<p class="muted" style="font-size:12.5px;margin-top:14px">${esc(F.observacao)}${F.atualizado ? ` Atualizado em ${esc(dataBR(F.atualizado))}.` : ""}</p>` : ""}
      ${S.local ? `<p class="muted" style="font-size:12.5px">◆ Itens de informação local e a leitura vêm de <code>${esc(m.slug)}.local.js</code>, que não vai para o GitHub.</p>` : ""}`;
  }

  // ------------------------------------------------------------------ deputado × cidade
  function deputados() {
    const m = new Map();
    for (const [ano, e] of Object.entries(S.city.eleicoes))
      for (const [k, c] of Object.entries(e.cargos)) {
        if (!k.startsWith("deputado") || k.endsWith("_2t")) continue;
        c.candidatos.forEach((x) => { const d = m.get(x.pid) || { pid: x.pid, ent: [] }; d.ent.push({ ano, cargo: k, x }); m.set(x.pid, d); });
      }
    const lista = [...m.values()];
    lista.forEach((d) => d.ent.sort((p, q) => q.ano - p.ano));
    return lista.sort((p, q) => q.ent[0].ano - p.ent[0].ano || q.ent[0].x.votos - p.ent[0].x.votos);
  }
  function statusEleito(sit) {
    const s = (sit || "").toLowerCase();
    if (!s) return ["—", ""];
    if (s.startsWith("eleito")) return ["Eleito", "ok"];
    if (s.includes("suplente")) return ["Suplente · não eleito", "no"];
    return ["Não eleito", "no"];
  }
  function renderDeputado() {
    const el = $("#deputado"), m = S.city.meta;
    const cs = window.PLENARIA_CIDADES || [];
    const lista = deputados();
    const head = (tools) => `<div class="blk-h"><div><h2>Deputado na <em class="s">cidade</em></h2><p class="lead">Escolha a cidade e o deputado: votos na cidade e no estado, locais e bairros mais fortes e o histórico dele na cidade.</p></div>${tools}</div>`;
    const selCity = `<select class="pill" id="dep-city">${cs.map((c) => `<option value="${esc(c.id)}" ${c.id === S.cityId ? "selected" : ""}>${esc(c.nome)} · ${esc(c.uf)}</option>`).join("")}</select>`;
    if (!lista.length) {
      el.innerHTML = head(`<div class="tools">${selCity}</div>`) + `<div class="notice"><b>Ainda não há votação de deputados carregada para ${esc(m.municipio)}.</b> Ela vem dos arquivos oficiais do TSE (por seção, com bairro e local). Assim que o acesso ao TSE for liberado: <code>python3 scripts/plenaria.py tse --municipio ${esc(m.municipio)} --ano 2026 --ano 2022 --ano 2018 --baixar</code></div>`;
      return;
    }
    if (!lista.some((d) => d.pid === S.dep.pid)) S.dep = { pid: lista[0].pid, ano: null };
    const d = lista.find((z) => z.pid === S.dep.pid);
    const ent = d.ent.find((z) => z.ano === S.dep.ano) || d.ent[0];
    const anos = [...new Set(lista.flatMap((z) => z.ent.map((e) => e.ano)))].sort().reverse();
    const opts = anos.map((ano) => `<optgroup label="${ano}">${lista.filter((z) => z.ent[0].ano === ano).map((z) => { const x = z.ent[0].x; return `<option value="${esc(z.pid)}" ${z.pid === d.pid ? "selected" : ""}>${esc(x.urna)} (${esc(x.partido || "")}) — ${fmt(x.votos)} votos</option>`; }).join("")}</optgroup>`).join("");
    const tools = `<div class="tools">${selCity}<select class="pill" id="dep-sel" aria-label="Deputado">${opts}</select>${d.ent.length > 1 ? `<select class="pill" id="dep-ano">${d.ent.map((e) => `<option value="${e.ano}" ${e === ent ? "selected" : ""}>${e.ano} · ${esc(cargoCurto(e.cargo))}</option>`).join("")}</select>` : ""}</div>`;
    const a = agg(ent.ano, ent.cargo), x = a.bySq[ent.x.sq], e = S.city.eleicoes[ent.ano];
    S.dep.cur = { ano: ent.ano, cargo: ent.cargo };
    const u = x.uf || {};
    const [st, stc] = statusEleito(x.situacao);
    const hist = historico(x.pid);
    const porSec = e.nivel === "secao";
    const locais = porSec ? Object.values(a.locais).map((l) => ({ l, v: l.cand[x.sq] || 0 })).filter((r) => r.v).sort((p, q) => q.v - p.v).slice(0, 5) : [];
    const bairros = porSec ? Object.values(a.bairros).map((b) => ({ b, v: b.cand[x.sq] || 0 })).sort((p, q) => q.v - p.v) : [];
    const lmax = locais[0] ? locais[0].v : 1, bmax = bairros[0] && bairros[0].v ? bairros[0].v : 1;
    const hmax = Math.max(...hist.map((h) => h.x.votos), 1);
    el.innerHTML = head(tools) + `<div class="dep-card card">
      <div class="dep-id">
        <div class="pf-photo">${esc(initials(x.urna))}${x.foto ? `<img src="${esc(x.foto)}" alt="Foto de ${esc(x.urna)}" referrerpolicy="no-referrer" onerror="this.remove()" style="position:absolute;inset:0">` : ""}</div>
        <div class="k">${esc(cargoCurto(ent.cargo))} · ${esc(ent.ano)}</div>
        <h3>${esc(x.urna)}</h3><div class="full">${esc(x.nome)}</div>
        <div class="badges"><span>${esc(x.partido || "")} ${esc(x.nr || "")}</span></div>
        <div class="status ${stc}">${esc(st)}</div>
        <div class="city">em <b>${esc(m.municipio)}</b> · ${esc(m.uf)}</div>
      </div>
      <div class="dep-body">
        <div class="grid dep-k">
          <div><div class="v num">${fmt(x.votos)}</div><div class="l">votos em ${esc(m.municipio)}</div></div>
          <div><div class="v num">${x._pos}º</div><div class="l">na cidade · ${pct(x.votos / a.validos)} dos válidos</div></div>
          <div><div class="v num">${u.total != null ? fmt(u.total) : "—"}</div><div class="l">votos no ${esc(m.uf)} (total geral)${u.rank ? ` · ${u.rank}º do estado` : ""}</div></div>
          <div><div class="v num">${u.total ? pct(x.votos / u.total) : "—"}</div><div class="l">da votação dele veio de ${esc(m.municipio)}${u.posMun ? ` · ${u.posMun}º município dele` : ""}</div></div>
          <div><div class="v num">${hist.length}</div><div class="l">${hist.length === 1 ? "eleição" : "eleições"} com voto em ${esc(m.municipio)} (anos carregados)</div></div>
        </div>
        ${porSec ? `<div class="grid dep-cols">
          <div><h4>Top 5 locais de votação</h4>${locais.map(({ l, v }, i) => `<div class="hbar"><div class="lb">${i + 1}. ${esc(l.nome)}<div class="muted" style="font-size:11.5px">${esc(l.bairro)}</div></div><div class="t"><i style="width:${(v / lmax) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / (l.validos || 1))}</div></div>`).join("")}</div>
          <div><h4>Votos por bairro</h4>${bairros.map(({ b, v }) => `<div class="hbar" ${tip(`${esc(b.nome)}: ${fmt(v)} votos · ${pct(v / (b.validos || 1))} dos válidos do bairro`)}><div class="lb">${esc(b.nome)}</div><div class="t"><i style="width:${(v / bmax) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / (b.validos || 1))}</div></div>`).join("")}</div>
        </div>${raioXHTML(a, x.sq)}` : `<div class="notice" style="margin-top:16px">Locais e bairros não disponíveis para ${esc(ent.ano)} (só totais do município).</div>`}
        <h4>Histórico em ${esc(m.municipio)}</h4>
        <div class="timeline">${hist.map((h) => { const [hs] = statusEleito(h.x.situacao); return `<div class="tl ${h.ano == ent.ano && h.cargo === ent.cargo ? "cur" : ""}"><div class="y">${h.ano} <span class="muted" style="font-weight:500;font-size:14px">· ${esc(cargoCurto(h.cargo))} · ${esc(h.x.partido || "")}</span></div>
          <div class="c">${fmt(h.x.votos)} votos na cidade · ${pct(h.share)} dos válidos · ${h.pos}º de ${h.n}${h.x.uf && h.x.uf.total ? ` · ${fmt(h.x.uf.total)} no estado` : ""} · ${esc(hs)}</div><div class="t"><i style="width:${(h.x.votos / hmax) * 100}%"></i></div></div>`; }).join("")}</div>
      </div></div>`;
  }


  // ------------------------------------------------------------------ trajetória e comparação (todas as eleições carregadas)
  const TIPOS = { vereador: ["Vereadores", (k) => k === "vereador"], prefeito: ["Prefeitos", (k) => k === "prefeito"], deputado: ["Deputados", (k) => k.startsWith("deputado")] };
  function pessoasIdx() {
    const m = new Map();
    for (const [ano, e] of Object.entries(S.city.eleicoes))
      for (const [k, c] of Object.entries(e.cargos)) {
        if (k.endsWith("_2t")) continue;
        const val = c.totais ? c.totais.validos : c.candidatos.reduce((t, y) => t + y.votos, 0);
        c.candidatos.forEach((x, i) => {
          const d = m.get(x.pid) || { pid: x.pid, ent: [] };
          d.ent.push({ ano: +ano, cargo: k, x, pos: i + 1, n: c.candidatos.length, share: x.votos / (val || 1) });
          m.set(x.pid, d);
        });
      }
    for (const d of m.values()) {
      d.ent.sort((p, q) => p.ano - q.ano);
      const ult = d.ent[d.ent.length - 1].x;
      d.urna = ult.urna; d.nome = ult.nome;
      d.foto = [...d.ent].reverse().map((e) => e.x.foto).find(Boolean) || null;
      d.eleito = d.ent.filter((e) => (e.x.situacao || "").startsWith("eleito")).length;
    }
    return m;
  }
  function tendencia(ent) {
    if (ent.length < 2) return ["Uma candidatura", ""];
    const a = ent[ent.length - 2], b = ent[ent.length - 1];
    if (a.cargo !== b.cargo) return ["Mudou de cargo", ""];
    const d = (b.share - a.share) * 100;
    const txt = `${d > 0 ? "+" : ""}${d.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} p.p. · ${b.x.votos - a.x.votos > 0 ? "+" : ""}${fmt(b.x.votos - a.x.votos)} votos vs ${a.ano}`;
    if (d >= 0.5) return ["▲ Em crescimento", "up", txt];
    if (d <= -0.5) return ["▼ Em declínio", "down", txt];
    return ["■ Estável", "", txt];
  }
  const _renderCruzamento = renderCruzamento;
  renderCruzamento = function () { _renderCruzamento(); $("#estrategia").insertAdjacentHTML("beforeend", divisaoHTML()); };
  function renderTrajetoria() {
    const el = $("#trajetoria"), m = S.city.meta;
    const idx = pessoasIdx();
    const T = S.traj;
    const okTipo = (d) => d.ent.some((e) => TIPOS[T.tipo][1](e.cargo));
    const lista = [...idx.values()].filter(okTipo);
    if (!T.init || !T.sel.every((p) => idx.has(p))) {
      T.init = true;
      // padrão: os dois mais votados da eleição mais recente desse tipo
      const ult = Math.max(...lista.flatMap((d) => d.ent.filter((e) => TIPOS[T.tipo][1](e.cargo)).map((e) => e.ano)));
      const v = (d) => (d.ent.find((e) => e.ano === ult && TIPOS[T.tipo][1](e.cargo)) || { x: { votos: -1 } }).x.votos;
      T.sel = [...lista].sort((p, q) => v(q) - v(p)).slice(0, 2).map((d) => d.pid);
    }
    const sel = T.sel.map((p) => idx.get(p)).filter(Boolean);
    const anos = Object.keys(S.city.eleicoes).map(Number).sort();
    const tem = Object.keys(TIPOS).filter((k) => [...idx.values()].some((d) => d.ent.some((e) => TIPOS[k][1](e.cargo))));
    const opts = lista.filter((d) => !T.sel.includes(d.pid)).sort((p, q) => p.urna.localeCompare(q.urna, "pt-BR"));
    const head = `<div class="blk-h"><div><h2>Trajetória e <em class="s">comparação</em></h2><p class="lead">A evolução de cada nome em ${esc(m.municipio)}, eleição a eleição: partido, votos, posição e resultado. Escolha até 4 para comparar. Dados de ${anos[0]} a ${anos[anos.length - 1]}.</p></div>
      <div class="tools"><div class="seg" role="group" aria-label="Tipo">${tem.map((k) => `<button type="button" data-ttipo="${k}" aria-pressed="${k === T.tipo}">${TIPOS[k][0]}</button>`).join("")}</div>
      <div class="seg" role="group" aria-label="Medida"><button type="button" data-tmodo="pct" aria-pressed="${T.modo === "pct"}">% dos válidos</button><button type="button" data-tmodo="votos" aria-pressed="${T.modo === "votos"}">Votos</button></div>
      ${sel.length < 4 ? `<input class="search" id="traj-add" list="traj-dl" placeholder="+ Adicionar nome para comparar" autocomplete="off"><datalist id="traj-dl">${opts.map((d) => `<option value="${esc(d.urna)} — ${esc(d.nome)} (${d.ent.map((e) => e.ano).join(", ")})"></option>`).join("")}</datalist>` : ""}</div></div>`;
    el._opts = opts;
    if (!sel.length) { el.innerHTML = head + `<div class="notice">Escolha um nome no campo acima.</div>`; return; }
    // gráfico: um eixo só (% dos válidos ou votos), uma linha por pessoa
    // eixo X: todas as eleições do tipo escolhido (mantém o espaçamento real entre os anos)
    const xs = [...new Set([...Object.entries(S.city.eleicoes).filter(([, e]) => Object.keys(e.cargos).some((k) => TIPOS[T.tipo][1](k))).map(([a]) => +a), ...sel.flatMap((d) => d.ent.map((e) => e.ano))])].sort((p, q) => p - q);
    const W = 900, H = 340, P = { l: 56, r: 30, t: 40, b: 40 };
    const val = (e) => (T.modo === "pct" ? e.share : e.x.votos);
    const bruto = Math.max(...sel.flatMap((d) => d.ent.map(val)), 1e-9);
    const passo = (() => { const r = bruto / 4, k = Math.pow(10, Math.floor(Math.log10(r))); return [1, 2, 2.5, 5, 10].map((f) => f * k).find((v) => v >= r); })();
    const vmax = Math.ceil((bruto * 1.12) / passo) * passo;
    const xp = (ano) => P.l + (xs.length === 1 ? (W - P.l - P.r) / 2 : ((xs.indexOf(ano)) * (W - P.l - P.r)) / (xs.length - 1));
    const yp = (v) => H - P.b - (v / vmax) * (H - P.t - P.b);
    const ticks = Array.from({ length: Math.round(vmax / passo) + 1 }, (_, i) => i * passo);
    const fy = (v) => (T.modo === "pct" ? pct(v, passo * 100 < 1 ? 1 : 0) : fmt(v));
    let svg = ticks.map((v) => `<line x1="${P.l}" x2="${W - P.r}" y1="${yp(v)}" y2="${yp(v)}" stroke="var(--line)"/><text x="${P.l - 8}" y="${yp(v) + 4}" text-anchor="end">${fy(v)}</text>`).join("");
    svg += xs.map((a) => `<text x="${xp(a)}" y="${H - 14}" text-anchor="middle">${a}</text>`).join("");
    sel.forEach((d, i) => {
      const c = SLOTS[i];
      for (let j = 1; j < d.ent.length; j++) {
        const a = d.ent[j - 1], b = d.ent[j];
        const gap = b.ano - a.ano > 4 || a.cargo !== b.cargo;
        svg += `<line x1="${xp(a.ano)}" y1="${yp(val(a))}" x2="${xp(b.ano)}" y2="${yp(val(b))}" stroke="${c}" stroke-width="2" ${gap ? 'stroke-dasharray="5 5"' : ""}/>`;
      }
      d.ent.forEach((e) => {
        const ok = (e.x.situacao || "").startsWith("eleito");
        const t = `<b>${esc(d.urna)}</b> · ${e.ano}<br>${esc(cargoCurto(e.cargo))} · ${esc(e.x.partido || "")}<br>${fmt(e.x.votos)} votos · ${pct(e.share)} dos válidos<br>${e.pos}º de ${e.n} · ${esc(situTxt(e.x.situacao) || "—")}`;
        svg += `<circle cx="${xp(e.ano)}" cy="${yp(val(e))}" r="6" fill="${ok ? c : "var(--surface)"}" stroke="${c}" stroke-width="2.5" ${tip(t)}/>`;
        if (sel.length <= 2) svg += `<text class="lab" x="${xp(e.ano)}" y="${yp(val(e)) + (i ? 22 : -12)}" text-anchor="middle">${esc(e.x.partido || "")}</text>`;
      });
      const u = d.ent[d.ent.length - 1];
      if (sel.length > 2) svg += `<text class="lab" x="${Math.min(xp(u.ano) + 10, W - 4)}" y="${yp(val(u)) + 4}" style="fill:var(--ink-2)">${esc(d.urna.split(" ")[0])}</text>`;
    });
    const cards = sel.map((d, i) => {
      const [tl, tc, tx] = tendencia(d.ent);
      const best = [...d.ent].sort((p, q) => q.share - p.share)[0];
      const ult = d.ent[d.ent.length - 1];
      const partidos = d.ent.map((e) => e.x.partido).filter((p, j, a) => p && p !== a[j - 1]);
      const fake = { urna: d.urna, foto: d.foto };
      return `<div class="card tcard" style="--c:${SLOTS[i]}"><div class="th">${avatar(fake, "av tav")}<div style="min-width:0"><div class="nm" data-sq="${ult.x.sq}" data-pano="${ult.ano}" data-pcargo="${ult.cargo}">${esc(d.urna)}</div><div class="muted" style="font-size:12.5px">${esc(d.nome)}</div></div><button type="button" class="chk" data-trm="${d.pid}" aria-label="Remover">×</button></div>
        <div class="tend ${tc}">${esc(tl)}</div>${tx ? `<div class="muted" style="font-size:12.5px">${esc(tx)}</div>` : ""}
        <div class="grid tk"><div><b>${d.ent.length}</b><span>candidaturas</span></div><div><b>${d.eleito}</b><span>vezes eleito</span></div><div><b>${fmt(best.x.votos)}</b><span>melhor: ${best.ano}</span></div></div>
        <div class="k">Partidos</div><div class="parts">${partidos.map((p, j) => `${j ? '<span class="arr">→</span>' : ""}<span class="pt">${esc(p)}</span>`).join("")}</div></div>`;
    }).join("");
    const linhas = xs.map((a) => `<tr><td><b>${a}</b></td>${sel.map((d) => { const e = d.ent.find((z) => z.ano === a); return `<td>${e ? `<b class="num">${fmt(e.x.votos)}</b> <span class="muted num">${pct(e.share)}</span><div class="muted" style="font-size:12px">${esc(e.x.partido || "")} · ${e.pos}º de ${e.n} · ${esc(situTxt(e.x.situacao) || "")}${TIPOS.vereador[1](e.cargo) ? "" : " · " + esc(cargoCurto(e.cargo))}</div>` : `<span class="muted">—</span>`}</td>`; }).join("")}</tr>`).reverse().join("");
    el.innerHTML = head + `<div class="grid tcards">${cards}</div>
      <div class="card" style="margin-top:14px"><div class="legend" style="margin:0 0 6px">${sel.map((d, i) => `<span><i style="background:${SLOTS[i]}"></i>${esc(d.urna)}</span>`).join("")}<span><i style="background:transparent;box-shadow:inset 0 0 0 2px var(--ink-2)"></i>vazado = não eleito</span><span>tracejado = pulou eleição ou mudou de cargo</span></div>
      <svg class="chart" viewBox="0 0 ${W} ${H}" style="height:auto" role="img" aria-label="Evolução eleitoral">${svg}</svg></div>
      <div class="tbl-wrap" style="margin-top:14px;max-height:none"><table class="tbl"><thead><tr><th>Eleição</th>${sel.map((d, i) => `<th><i style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${SLOTS[i]};margin-right:6px"></i>${esc(d.urna)}</th>`).join("")}</tr></thead><tbody>${linhas}</tbody></table></div>
      <p class="muted" style="font-size:12.5px;margin-top:10px">A mesma pessoa é ligada entre eleições pelo identificador do candidato (Base dos Dados/TSE). % dos válidos permite comparar anos com eleitorados diferentes.</p>`;
  }


  // ------------------------------------------------------------------ onde ir: cruza a base local (vereadores) com um deputado
  const QUAD = {
    ir: ["Ir primeiro", "Base local forte, deputado fraco: voto do grupo que não foi para ele", "var(--s1)", 1],
    adv: ["Território adversário", "Os dois fracos num lugar grande: alguém de fora manda ali", "var(--s2)", 2],
    proprio: ["Voto próprio do deputado", "Deputado forte sem a base local: reforçar com lideranças", "var(--s3)", 3],
    ok: ["Consolidado", "Os dois fortes: manter, sem gastar energia", "#8d8b82", 4],
    nao: ["Não compensa", "Os dois fracos num lugar pequeno", "#5d5c57", 5],
  };
  function cruzamento() {
    const C = S.cruz;
    const [da, dc] = C.depEl.split("|"), [va, vc] = C.verEl.split("|");
    const aD = agg(da, dc), aV = agg(va, vc);
    const dep = aD.bySq[C.dep];
    const aliados = C.aliados.map((sq) => aV.bySq[sq]).filter(Boolean);
    if (!dep || !aliados.length) return null;
    const chave = (z) => (C.nivel === "bairro" ? z.nome : normNome(z.nome));
    const mapa = new Map();
    const fonte = (o, lado) => Object.values(o).forEach((z) => { const k = chave(z); const r = mapa.get(k) || { nome: z.nome, bairro: z.bairro || z.nome }; r[lado] = z; mapa.set(k, r); });
    fonte(C.nivel === "bairro" ? aD.bairros : aD.locais, "d");
    fonte(C.nivel === "bairro" ? aV.bairros : aV.locais, "v");
    const baseD = dep.votos / (aD.validos || 1);
    const votosAl = aliados.reduce((t, x) => t + x.votos, 0), baseV = votosAl / (aV.validos || 1);
    const totVal = [...mapa.values()].reduce((t, r) => t + ((r.d && r.d.validos) || 0), 0) || 1;
    const linhas = [...mapa.values()].filter((r) => r.d && r.v).map((r) => {
      const vd = r.d.cand[dep.sq] || 0, valD = r.d.validos || 0;
      const vv = aliados.reduce((t, x) => t + (r.v.cand[x.sq] || 0), 0), valV = r.v.validos || 0;
      const idxD = baseD ? ((vd / (valD || 1)) / baseD) * 100 : 0, idxV = baseV ? ((vv / (valV || 1)) / baseV) * 100 : 0;
      const peso = valD / totVal;
      let q;
      if (idxV >= 100 && idxD < 100) q = "ir";
      else if (idxV >= 100) q = "ok";
      else if (idxD >= 100) q = "proprio";
      else q = peso >= 0.1 ? "adv" : "nao";
      const gap = Math.max(0, Math.round(baseD * valD - vd));
      const liderV = r.v.rank && r.v.rank[0] ? aV.bySq[r.v.rank[0][0]] : null;
      const liderD = r.d.rank && r.d.rank[0] ? aD.bySq[r.d.rank[0][0]] : null;
      return { nome: r.nome, bairro: r.bairro, vd, valD, vv, valV, idxD, idxV, peso, q, gap, liderV, liderD, aptos: r.d.aptos || r.v.aptos || 0 };
    });
    linhas.sort((p, q) => QUAD[p.q][3] - QUAD[q.q][3] || q.gap - p.gap);
    return { dep, aliados, baseD, baseV, linhas, aD, aV, da, dc, va, vc };
  }

  // ------------------------------------------------------------------ divisão da base: cada vereador com seu deputado
  // Os pares vêm de S.local.apoios (conhecimento local). Com votos por seção, mede se cada vereador entregou.
  function pearson(xs, ys) {
    const n = xs.length; if (n < 3) return null;
    const mx = xs.reduce((a, b) => a + b, 0) / n, my = ys.reduce((a, b) => a + b, 0) / n;
    let sxy = 0, sxx = 0, syy = 0;
    for (let i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; syy += (ys[i] - my) ** 2; }
    return sxx && syy ? sxy / Math.sqrt(sxx * syy) : null;
  }
  function divisaoBase() {
    const apoios = (S.local && S.local.apoios) || [];
    if (!apoios.length) return { apoios };
    const ops = mapEleicoes();
    const ver = ops.find((o) => o.cargo === "vereador");
    const deps = ops.filter((o) => o.cargo.startsWith("deputado"));
    const achar = (a, nome) => a && a.cands.find((x) => normNome(x.urna) === normNome(nome) || normNome(x.nome) === normNome(nome));
    const aV = ver ? agg(ver.ano, ver.cargo) : null;
    const pares = [];
    for (const ap of apoios) for (const dn of ap.deputados || []) {
      const p = { vereador: ap.vereador, deputado: dn, grupo: ap.grupo || "", obs: ap.obs || "", tipo: ap.tipo || "vereador" };
      const xv = achar(aV, ap.vereador);
      let dep = null, aD = null;
      for (const o of deps) { const a = agg(o.ano, o.cargo); const x = achar(a, dn); if (x) { dep = x; aD = a; p.cargoDep = o.cargo; p.anoDep = o.ano; break; } }
      if (xv && dep) {
        p.vVer = xv.votos; p.vDep = dep.votos; p.transf = dep.votos / (xv.votos || 1);
        const nomes = Object.keys(aV.bairros).filter((b) => aD.bairros[b]);
        p.corr = pearson(nomes.map((b) => (aV.bairros[b].cand[xv.sq] || 0) / (aV.bairros[b].validos || 1)), nomes.map((b) => (aD.bairros[b].cand[dep.sq] || 0) / (aD.bairros[b].validos || 1)));
        const redutos = Object.values(aV.locais).map((l) => ({ l, v: l.cand[xv.sq] || 0 })).sort((a, b) => b.v - a.v).slice(0, 3);
        p.redutos = redutos.map(({ l, v }) => {
          const ld = Object.values(aD.locais).find((z) => normNome(z.nome) === normNome(l.nome));
          const lider = ld && ld.rank[0] ? aD.bySq[ld.rank[0][0]] : null;
          return { nome: l.nome, vVer: v, vDep: ld ? ld.cand[dep.sq] || 0 : null, lider, ok: lider && lider.sq === dep.sq };
        });
      } else if (ap.tipo === "liderança" || ap.tipo === "prefeito") p.falta = (ap.tipo === "prefeito" ? "apoio do próprio prefeito" : "liderança local sem votação própria") + " — com o TSE, mede-se onde o deputado foi forte";
      else p.falta = !xv ? (aV ? "vereador não encontrado na votação de " + ver.ano : "falta a votação por seção dos vereadores") : "falta a votação por seção dos deputados";
      pares.push(p);
    }
    return { apoios, pares };
  }
  function divisaoHTML() {
    const D = divisaoBase();
    const head = `<h3 class="fh" style="margin-top:46px">Divisão da base: cada vereador com seu deputado</h3>`;
    if (!D.apoios.length) return head + `<div class="notice">Registre no arquivo local quem trabalhou para quem (campo <code>apoios</code>, ex.: <code>{ vereador: "Eudes Mesquita", deputados: ["Lia Gomes"] }</code>). Com isso a página mede, para cada par, quanto do voto do vereador virou voto do deputado e se o deputado ganhou nos redutos do vereador.</div>`;
    const comDados = D.pares.filter((p) => p.vDep != null);
    const linha = (p) => `<tr><td><b>${esc(p.vereador)}</b>${p.grupo ? `<div class="muted" style="font-size:12px">${esc(p.grupo)}</div>` : ""}${p.obs ? `<div style="font-size:12px;color:#ffd780">${esc(p.obs)}</div>` : ""}</td><td>${esc(p.deputado)}${p.cargoDep ? `<div class="muted" style="font-size:12px">${esc(cargoCurto(p.cargoDep))} ${esc(p.anoDep)}</div>` : ""}</td>
      ${p.vDep != null ? `<td class="r num">${fmt(p.vVer)}</td><td class="r num">${fmt(p.vDep)}</td><td class="r num"><b>${pct(p.transf, 0)}</b></td>
        <td class="r num">${p.corr == null ? "—" : `<span class="qtag" style="--c:${p.corr >= 0.5 ? "var(--s1)" : p.corr >= 0.2 ? "#8d8b82" : "var(--s2)"}">${p.corr.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}</span>`}</td>
        <td>${p.redutos.map((r) => `<div style="font-size:12.5px">${esc(r.nome)}: ${r.ok ? "✔ deputado venceu" : r.lider ? `✘ venceu ${esc(r.lider.urna)}` : "—"}${r.vDep != null ? ` <span class="muted">(${fmt(r.vDep)} p/ ele)</span>` : ""}</div>`).join("")}</td>`
        : `<td colspan="5" class="muted" style="font-size:12.5px">Aguardando dados: ${esc(p.falta)}</td>`}</tr>`;
    // quem trabalhou para quem (não depende do TSE)
    const info = (S.local && S.local.deputadosInfo) || {};
    const porDep = new Map();
    D.pares.forEach((p) => { const r = porDep.get(p.deputado) || { nome: p.deputado, vers: [] }; r.vers.push(p); porDep.set(p.deputado, r); });
    const ordem = [...porDep.values()].sort((a, b) => (a.vers[0].grupo === "oposição") - (b.vers[0].grupo === "oposição") || b.vers.length - a.vers.length);
    const mapa = `<div class="grid apo">${ordem.map((d) => { const i = info[d.nome] || {}; const op = d.vers.some((v) => v.grupo === "oposição"), tv = d.vers.some((v) => v.grupo === "terceira via"); const eleito = /^eleit/i.test(i.resultado || "");
      const rr = acharRelatorio([d.nome]), cc = acharCandidato(rr ? rr.nomes : [d.nome]);
      return `<div class="card apcard ${op ? "op" : tv ? "tv" : ""}"><div class="ah">${avatar({ urna: d.nome, foto: cc && cc.x.foto, wiki: rr && rr.wiki }, "av apav")}<div style="flex:1;min-width:0"><div class="l">${esc([i.cargo, i.partido].filter(Boolean).join(" · ") || "Deputado")}</div><div class="v relk" data-rel="${esc(d.nome)}" role="button" tabindex="0">${esc(d.nome)}</div></div><span class="pos ${eleito ? "ok" : ""}">${eleito ? "Eleito" : esc((i.resultado || "?").split(" · ")[0])}</span></div>
        <div class="d">${esc(i.resultado || "")}${i.url ? ` · <a href="${esc(i.url)}" target="_blank" rel="noopener">fonte ↗</a>` : ""}${cc && !i.resultado ? `${esc([cc.x.partido, cc.x.situacao].filter(Boolean).join(" · "))}` : ""}${cc ? ` · <b class="num">${fmt(cc.x.votos)}</b> em ${esc(S.city.meta.municipio)} (${cc.ano})` : ""}</div>
        <div class="k">Quem trabalhou em Varjota</div><div class="vers">${d.vers.map((v) => `<span class="cpick" ${v.obs ? `title="${esc(v.obs)}"` : ""}><b>${esc(v.vereador)}</b>${v.tipo === "liderança" ? `<span class="tagx" style="color:var(--ink-2)">liderança</span>` : v.tipo === "prefeito" ? `<span class="tagx" style="color:var(--accent)">prefeito</span>` : ""}${v.obs && /especula/i.test(v.obs) ? `<span class="tagx">especulação</span>` : ""}</span>`).join("")}</div></div>`; }).join("")}</div>`;
    return head + `<p class="muted" style="font-size:13px;margin:-6px 0 12px">Mapa de apoios (informação local ◆). Abaixo, a medição de cada par com os votos por seção.</p>` + mapa + `<p class="muted" style="font-size:13px;margin:22px 0 12px">Transferência = votos do deputado na cidade ÷ votos do vereador. Sintonia = se o deputado foi bem justamente onde o vereador é forte (de −1 a 1; acima de 0,5 o vereador entregou no território dele).</p>
      <div class="tbl-wrap" style="max-height:none"><table class="tbl"><thead><tr><th>Vereador</th><th>Deputado apoiado</th><th class="r">Votos vereador</th><th class="r">Votos deputado</th><th class="r">Transferência</th><th class="r">Sintonia</th><th>Nos 3 redutos do vereador</th></tr></thead><tbody>${D.pares.map(linha).join("")}</tbody></table></div>
      ${comDados.length ? "" : `<p class="muted" style="font-size:12.5px;margin-top:8px">Os pares estão registrados; os números aparecem quando a votação por seção de vereadores e deputados for importada do TSE.</p>`}`;
  }
  function renderCruzamento() {
    const el = $("#estrategia"), m = S.city.meta;
    const opts = mapEleicoes();
    const deps = opts.filter((o) => !["vereador", "prefeito"].includes(o.cargo));
    const vers = opts.filter((o) => ["vereador", "prefeito"].includes(o.cargo));
    const head = (tools) => `<div class="blk-h"><div><h2>Onde <em class="s">ir</em></h2><p class="lead">Cruza a força dos vereadores do grupo (a base local) com a do deputado, bairro a bairro: onde o voto do grupo não chegou nele, onde é território adversário e onde não compensa ir.</p></div>${tools || ""}</div>`;
    if (!deps.length || !vers.length) {
      el.innerHTML = head() + `<div class="notice"><b>Precisa da votação por seção de uma eleição de vereador e de uma de deputado.</b> Assim que o TSE for liberado: <code>python3 scripts/plenaria.py tse --municipio ${esc(m.municipio)} --ano 2026 --ano 2024 --baixar</code></div>`;
      return;
    }
    const C = S.cruz;
    if (!deps.some((o) => `${o.ano}|${o.cargo}` === C.depEl)) { C.depEl = `${deps[0].ano}|${deps[0].cargo}`; C.dep = ""; }
    if (!vers.some((o) => `${o.ano}|${o.cargo}` === C.verEl)) { C.verEl = `${vers.find((o) => o.cargo === "vereador")?.ano || vers[0].ano}|${vers.find((o) => o.cargo === "vereador") ? "vereador" : vers[0].cargo}`; C.aliados = []; }
    const aD = agg(...C.depEl.split("|")), aV = agg(...C.verEl.split("|"));
    if (!aD.bySq[C.dep]) C.dep = aD.cands[0] ? aD.cands[0].sq : "";
    C.aliados = C.aliados.filter((sq) => aV.bySq[sq]);
    const tools = `<div class="tools">
      <select class="pill" id="cz-depel">${deps.map((o) => `<option value="${o.ano}|${o.cargo}" ${`${o.ano}|${o.cargo}` === C.depEl ? "selected" : ""}>${o.ano} · ${esc(cargoCurto(o.cargo))}</option>`).join("")}</select>
      <select class="pill" id="cz-dep">${relevantes(aD).concat(aD.cands.filter((x) => !relevantes(aD).includes(x)).slice(0, 60)).map((x) => `<option value="${x.sq}" ${x.sq === C.dep ? "selected" : ""}>${esc(x.urna)} (${esc(x.partido || "")})</option>`).join("")}</select>
      <div class="seg"><button type="button" data-cznivel="bairro" aria-pressed="${C.nivel === "bairro"}">Bairros</button><button type="button" data-cznivel="local" aria-pressed="${C.nivel === "local"}">Locais</button></div></div>`;
    const base = `<div class="cz-base"><div class="k">Base local <span class="muted" style="text-transform:none;letter-spacing:0">· ${esc(C.verEl.split("|")[0])} · escolha os vereadores do grupo</span></div>
      <div class="cmp-pick">${C.aliados.map((sq) => { const x = aV.bySq[sq]; return `<span class="cpick">${avatar(x)}<b>${esc(x.urna)}</b><span class="muted num">${fmt(x.votos)}</span><button type="button" data-czrm="${sq}" aria-label="Remover">×</button></span>`; }).join("")}
      <select class="pill" id="cz-add"><option value="">+ Adicionar vereador do grupo</option>${aV.cands.filter((x) => !C.aliados.includes(x.sq)).map((x) => `<option value="${x.sq}">${esc(x.urna)} (${esc(x.partido || "")}) · ${fmt(x.votos)}</option>`).join("")}</select>
      ${vers.length > 1 ? `<select class="pill" id="cz-verel">${vers.map((o) => `<option value="${o.ano}|${o.cargo}" ${`${o.ano}|${o.cargo}` === C.verEl ? "selected" : ""}>${o.ano} · ${esc(cargoCurto(o.cargo))}</option>`).join("")}</select>` : ""}</div></div>`;
    const R = cruzamento();
    if (!R) { el.innerHTML = head(tools) + base + `<div class="notice">Escolha o deputado e pelo menos um vereador do grupo para ver o cruzamento.</div>`; return; }
    // gráfico de quadrantes: x = força da base local, y = força do deputado (100 = média de cada um)
    const W = 760, H = 460, P = { l: 56, r: 24, t: 24, b: 48 };
    const mx = Math.max(160, ...R.linhas.map((l) => Math.max(l.idxD, l.idxV))) * 1.1;
    const X = (v) => P.l + (Math.min(v, mx) / mx) * (W - P.l - P.r), Y = (v) => H - P.b - (Math.min(v, mx) / mx) * (H - P.t - P.b);
    const vmax = Math.max(...R.linhas.map((l) => l.valD), 1);
    let svg = `<rect x="${X(100)}" y="${Y(mx)}" width="${X(mx) - X(100)}" height="${Y(100) - Y(mx)}" fill="#8d8b82" opacity=".06"/>`;
    svg += `<line x1="${X(100)}" x2="${X(100)}" y1="${Y(0)}" y2="${Y(mx)}" stroke="var(--ink-2)" stroke-dasharray="4 4"/><line x1="${X(0)}" x2="${X(mx)}" y1="${Y(100)}" y2="${Y(100)}" stroke="var(--ink-2)" stroke-dasharray="4 4"/>`;
    svg += `<text x="${X(100) + 8}" y="${Y(0) - 8}" style="fill:var(--s1)">IR PRIMEIRO ↘</text><text x="${X(100) + 8}" y="${Y(mx) + 16}">CONSOLIDADO</text><text x="${X(0) + 8}" y="${Y(mx) + 16}">VOTO PRÓPRIO DO DEPUTADO</text><text x="${X(0) + 8}" y="${Y(0) - 8}">ADVERSÁRIO / NÃO COMPENSA</text>`;
    svg += `<text x="${(W + P.l) / 2}" y="${H - 10}" text-anchor="middle">força da base local (vereadores) →  100 = média do grupo</text><text x="16" y="${(H - P.b) / 2}" transform="rotate(-90 16 ${(H - P.b) / 2})" text-anchor="middle">força do deputado →</text>`;
    svg += R.linhas.map((l) => { const r = 7 + 18 * Math.sqrt(l.valD / vmax); const t = `<b>${esc(l.nome)}</b>${C.nivel === "local" ? ` · ${esc(l.bairro)}` : ""}<br>${QUAD[l.q][0]}<br>${esc(R.dep.urna)}: ${fmt(l.vd)} votos (índice ${Math.round(l.idxD)})<br>Grupo: ${fmt(l.vv)} votos (índice ${Math.round(l.idxV)})<br>${fmt(l.valD)} válidos${l.gap ? ` · faltam ~${fmt(l.gap)} p/ a média dele` : ""}`;
      return `<circle cx="${X(l.idxV)}" cy="${Y(l.idxD)}" r="${r.toFixed(1)}" fill="${QUAD[l.q][2]}" fill-opacity=".85" stroke="var(--surface)" stroke-width="2" ${tip(t)}/><text class="lab" x="${X(l.idxV)}" y="${Y(l.idxD) - r - 4}" text-anchor="middle">${esc(l.nome.length > 18 ? l.nome.slice(0, 17) + "…" : l.nome)}</text>`; }).join("");
    const resumo = Object.entries(QUAD).map(([k, q]) => { const ls = R.linhas.filter((l) => l.q === k); return `<div class="card cz-q" style="--c:${q[2]}"><div class="n">${ls.length}</div><div><b>${q[0]}</b><span class="muted">${q[1]}</span><span class="num">${fmt(ls.reduce((t, l) => t + l.valD, 0))} válidos${k === "ir" ? ` · ~${fmt(ls.reduce((t, l) => t + l.gap, 0))} votos a buscar` : ""}</span></div></div>`; }).join("");
    const tabela = `<div class="tbl-wrap" style="max-height:none"><table class="tbl"><thead><tr><th>${C.nivel === "bairro" ? "Bairro / distrito" : "Local de votação"}</th><th>Leitura</th><th class="r">${esc(R.dep.urna)}</th><th class="r">Grupo</th><th class="r">A buscar</th><th>Quem manda ali (vereador)</th></tr></thead><tbody>
      ${R.linhas.map((l) => `<tr><td><b>${esc(l.nome)}</b>${C.nivel === "local" ? `<div class="muted" style="font-size:12px">${esc(l.bairro)}</div>` : ""}<div class="muted" style="font-size:12px">${fmt(l.valD)} válidos</div></td>
        <td><span class="qtag" style="--c:${QUAD[l.q][2]}">${QUAD[l.q][0]}</span></td>
        <td class="r num">${fmt(l.vd)}<div class="muted">${pct(l.vd / (l.valD || 1))} · ${Math.round(l.idxD)}</div></td>
        <td class="r num">${fmt(l.vv)}<div class="muted">${pct(l.vv / (l.valV || 1))} · ${Math.round(l.idxV)}</div></td>
        <td class="r num">${l.gap ? `~${fmt(l.gap)}` : "—"}</td>
        <td>${l.liderV ? `${esc(l.liderV.urna)} <span class="muted">${esc(l.liderV.partido || "")}${C.aliados.includes(l.liderV.sq) ? " · do grupo" : ""}</span>` : "—"}</td></tr>`).join("")}</tbody></table></div>`;
    el.innerHTML = head(tools) + base + `<div class="grid cz-res">${resumo}</div>
      <div class="card" style="margin-top:14px"><svg class="chart" viewBox="0 0 ${W} ${H}" style="height:auto" role="img" aria-label="Quadrantes de força">${svg}</svg>
      <p class="muted" style="font-size:12.5px;margin:6px 0 0">Cada bolha é um ${C.nivel === "bairro" ? "bairro" : "local"}; tamanho = votos válidos. Índice = % na área ÷ % na cidade × 100. "A buscar" = votos que faltaram para o deputado chegar à média dele ali.</p></div>
      <div style="margin-top:14px">${tabela}</div>`;
  }


  // ------------------------------------------------------------------ quem é quem: rostos por grupo, com ligações aos deputados
  function fotoPorNome(nome) {
    const n = normNome(nome);
    const manual = (S.local && S.local.fotos) || {};
    for (const [k, v] of Object.entries(manual)) if (normNome(k) === n) return { foto: v };
    const cl = acharCandidato([nome]);
    if (cl && cl.x.foto && /^fotos\//.test(cl.x.foto)) return { foto: cl.x.foto };
    const c24 = ((S.city.candidaturas || {})["2024"] || []).find((c) => normNome(c.urna) === n || normNome(c.nome) === n);
    if (c24) return { foto: `https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/2045202024/${c24.sq}/${S.city.meta.cd_tse}`, c24 };
    const c = acharCandidato([nome]);
    const r = acharRelatorio([nome]);
    if (c && c.x.foto && /^fotos\//.test(c.x.foto)) return { foto: c.x.foto };   // foto oficial guardada no projeto
    return { foto: c && c.x.foto && /^https/.test(c.x.foto) ? c.x.foto : null, wiki: r && r.wiki };
  }
  function retrato(nome, sub, extra = {}) {
    const f = fotoPorNome(nome);
    const nm = nome.split(" / ")[0];
    return `<div class="rt ${extra.cls || ""}" data-pessoa="${esc(nome)}" ${extra.dep ? `data-dep="${esc(nome)}"` : ""} role="button" tabindex="0">
      ${avatar({ urna: nm, foto: f.foto, wiki: f.wiki }, "av rta")}
      <div class="rtn">${esc(nome)}</div>${sub ? `<div class="rts">${sub}</div>` : ""}${extra.tag ? `<span class="rtt ${extra.tagc || ""}">${esc(extra.tag)}</span>` : ""}</div>`;
  }
  function renderQuem() {
    const el = $("#quem"); if (!el) return;
    const m = S.city.meta, L = S.local || {}, F = S.ficha || {};
    const e26 = S.city.eleicoes["2026"] || { cargos: {} };
    const votos26 = (nome) => { for (const k of ["deputado_federal", "deputado_estadual"]) { const c = e26.cargos[k]; const x = c && c.candidatos.find((y) => normNome(y.urna) === normNome(nome)); if (x) return { x, cargo: k }; } return null; };
    const pref = (F.poder || []).find((p) => p.papel === "Prefeito"), vice = (F.poder || []).find((p) => p.papel === "Vice-prefeito");
    const c24 = (S.city.candidaturas || {})["2024"] || [];
    const sub24 = (nome) => { const c = c24.find((y) => normNome(y.urna) === normNome(nome)); return c ? `${esc(c.partido)}` : ""; };
    let html = `<div class="blk-h"><div><h2>Quem é quem em <em class="s">${esc(m.municipio)}</em></h2><p class="lead">Os rostos da política da cidade, por grupo. Passe o dedo ou o mouse sobre um vereador ou liderança para ver a quais deputados ele levou voto em 2026.</p></div></div>`;
    html += `<div class="qtopo">${pref ? retrato(pref.nome, "Prefeito · " + (sub24(pref.nome) || ""), { cls: "big", tag: "2º mandato" }) : ""}${vice ? retrato(vice.nome, "Vice-prefeito · Republicanos", { cls: "big", tag: "rompido", tagc: "warn" }) : ""}</div>`;
    const grupos = L.grupos || [];
    const apoios = L.apoios || [];
    if (!grupos.length) { el.innerHTML = html + `<div class="notice">Os grupos e as ligações vêm do seu arquivo local (<code>${esc(m.slug)}.local.js</code>).</div>`; return; }
    const chave = { "Situação": "prefeito", "Oposição": "oposição", "Terceira via": "terceira via" };
    const ordem = ["Situação", "Terceira via", "Oposição"].map((n) => grupos.find((g) => g.nome === n)).filter(Boolean);
    html += `<div class="board" id="board"><svg class="blinks" id="blinks"></svg>${ordem.map((g) => {
      const k = chave[g.nome];
      const doGrupo = apoios.filter((a) => (a.grupo || "") === k && a.vereador !== "Elmo Monte");
      const lideres = g.lider.split(" · ");
      const vers = (g.camara || [...new Set(doGrupo.filter((a) => (a.tipo || "vereador") === "vereador").map((a) => a.vereador))]).filter((v) => !lideres.includes(v));
      const lids0 = [...new Set(doGrupo.filter((a) => a.tipo === "liderança").map((a) => a.vereador))];
      const lids = lids0.filter((v) => !g.lider.split(" · ").includes(v));
      const deps = [...new Set(apoios.filter((a) => (a.grupo || "") === k).flatMap((a) => a.deputados))];
      const cor = k === "prefeito" ? "var(--s1)" : k === "oposição" ? "var(--s2)" : "var(--s3)";
      return `<div class="bcol" style="--c:${cor}"><div class="bh"><span class="dot"></span>${esc(g.nome)}<span class="muted">${esc(g.forca || "")}</span></div>
        <div class="blead">${lideres.map((n) => retrato(n, "liderança do grupo", { cls: "mid" })).join("")}</div>
        ${vers.length ? `<div class="bk">Na Câmara</div><div class="bgrid">${vers.map((v) => retrato(v, sub24(v) || "vereador")).join("")}</div>` : ""}
        ${lids.length ? `<div class="bk">Lideranças</div><div class="bgrid">${lids.map((v) => retrato(v, "liderança")).join("")}</div>` : ""}
        <div class="bk">Deputados com voto em ${esc(m.municipio)} · 2026</div><div class="bgrid deps">${deps.map((d) => { const v = votos26(d); return retrato(d, v ? `<b class="num">${fmt(v.x.votos)}</b> · ${v.cargo === "deputado_federal" ? "federal" : "estadual"}` : "", { dep: true, tag: v && /^eleit/.test(v.x.situacao || "") ? "eleito" : v && v.x.situacao ? v.x.situacao : "", tagc: v && /^eleit/.test(v.x.situacao || "") ? "ok" : "" }); }).join("")}</div></div>`; }).join("")}</div>`;
    el.innerHTML = html;
    // ligações: ao passar sobre alguém, desenha linhas até os deputados que ele apoiou
    const board = $("#board"), svg = $("#blinks");
    const mapa = {}; apoios.forEach((a) => { (mapa[a.vereador] ||= new Set()); a.deputados.forEach((d) => mapa[a.vereador].add(d)); });
    const limpar = () => { svg.innerHTML = ""; board.classList.remove("foco"); $$(".rt.on", board).forEach((x) => x.classList.remove("on")); };
    const ligar = (rt) => {
      const nome = rt.dataset.pessoa, alvo = mapa[nome]; if (!alvo || !alvo.size) return;
      limpar(); board.classList.add("foco"); rt.classList.add("on");
      const B = board.getBoundingClientRect(), a = rt.querySelector(".rta").getBoundingClientRect();
      const x1 = a.left + a.width / 2 - B.left, y1 = a.top + a.height / 2 - B.top;
      svg.setAttribute("viewBox", `0 0 ${B.width} ${B.height}`);
      let paths = "";
      $$(".rt[data-dep]", board).forEach((d) => {
        if (!alvo.has(d.dataset.dep)) return;
        d.classList.add("on");
        const r = d.querySelector(".rta").getBoundingClientRect(), x2 = r.left + r.width / 2 - B.left, y2 = r.top + r.height / 2 - B.top;
        const cy = (y1 + y2) / 2;
        paths += `<path d="M${x1},${y1} C${x1},${cy} ${x2},${cy} ${x2},${y2}" />`;
      });
      svg.innerHTML = paths;
      if (window.gsap) svg.querySelectorAll("path").forEach((p) => { const n = p.getTotalLength(); gsap.fromTo(p, { strokeDasharray: n, strokeDashoffset: n }, { strokeDashoffset: 0, duration: 0.6, ease: "power2.out" }); });
    };
    board.addEventListener("mouseover", (ev) => { const rt = ev.target.closest(".rt:not([data-dep])"); if (rt) ligar(rt); });
    board.addEventListener("mouseleave", limpar);
    board.addEventListener("click", (ev) => { const rt = ev.target.closest(".rt"); if (!rt) return; if (!rt.dataset.dep && mapa[rt.dataset.pessoa]) { ligar(rt); } else openRelatorio(rt.dataset.pessoa.split(" / ")[0]); });
  }
  function renderAll() {
    renderControls(); renderHero(); renderKPIs(); renderQuem(); renderFicha(); renderMapa(); renderCruzamento(); renderTrajetoria(); renderDeputado(); renderRanking(); renderBairros(); renderSecoes(); renderComparar(); renderHistorico(); renderFooter();
    revealOnScroll();
  }

  // ------------------------------------------------------------------ perfil
  function historico(pid) {
    const out = [];
    for (const [ano, e] of Object.entries(S.city.eleicoes)) {
      for (const [k, c] of Object.entries(e.cargos)) {
        const i = c.candidatos.findIndex((x) => x.pid === pid);
        if (i < 0) continue;
        const x = c.candidatos[i];
        const val = c.totais ? c.totais.validos : c.candidatos.reduce((s, y) => s + y.votos, 0);
        out.push({ ano: +ano, cargo: k, x, pos: i + 1, n: c.candidatos.length, share: x.votos / val });
      }
    }
    return out.sort((p, q) => q.ano - p.ano || p.cargo.localeCompare(q.cargo));
  }

  // ------------------------------------------------------------------ relatório por pessoa (rede e notícias)
  const normNome = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
  function acharRelatorio(nomes) {
    const alvo = new Set(nomes.filter(Boolean).map(normNome));
    return ((S.rel && S.rel.pessoas) || []).find((r) => r.nomes.some((n) => alvo.has(normNome(n)))) || null;
  }
  function acharCandidato(nomes) {
    const alvo = new Set(nomes.filter(Boolean).map(normNome));
    let best = null;
    for (const [ano, e] of Object.entries(S.city.eleicoes))
      for (const [k, c] of Object.entries(e.cargos))
        for (const x of c.candidatos)
          if ((alvo.has(normNome(x.urna)) || alvo.has(normNome(x.nome))) && (!best || +ano > +best.ano)) best = { ano, cargo: k, x };
    return best;
  }
  function buscasHTML(nome) {
    const cid = S.city.meta.municipio;
    const q = encodeURIComponent(`"${nome}"`), qc = encodeURIComponent(`"${nome}" ${cid}`);
    const L = [
      ["Google", `https://www.google.com/search?q=${qc}`],
      ["Notícias", `https://news.google.com/search?q=${q}&hl=pt-BR&gl=BR&ceid=BR:pt-419`],
      ["Instagram", `https://www.google.com/search?q=${encodeURIComponent(`site:instagram.com "${nome}"`)}`],
      ["Facebook", `https://www.facebook.com/search/top?q=${encodeURIComponent(nome)}`],
      ["YouTube", `https://www.youtube.com/results?search_query=${qc}`],
      ["X / Twitter", `https://x.com/search?q=${q}&f=live`],
    ];
    return `<div class="buscas">${L.map(([n, u]) => `<a href="${u}" target="_blank" rel="noopener">${n} ↗</a>`).join("")}</div>`;
  }
  function relatorioHTML(nomes) {
    const r = acharRelatorio(nomes);
    const nome = (r && r.nomes[0]) || nomes[0];
    const dest = r ? [...(r.destaques || [])].sort((a, b) => String(b.data).localeCompare(String(a.data))) : [];
    return `<h4>Relatório na rede${S.rel && S.rel.atualizado ? ` <span style="text-transform:none;letter-spacing:0">· atualizado em ${esc(dataBR(S.rel.atualizado))}</span>` : ""}</h4>
      ${r ? `<div class="rel">${r.papel ? `<div class="rp">${esc(r.papel)}${r.partido ? ` · <b>${esc(r.partido)}</b>` : ""}</div>` : ""}${r.resumo ? `<p>${esc(r.resumo)}</p>` : ""}
        <div class="redes">${(r.redes || []).length ? r.redes.map((rd) => `<a href="${esc(rd.url)}" target="_blank" rel="noopener" class="rede"><b>${esc(rd.rede)}</b> ${esc(rd.rotulo || "")} ↗</a>${rd.selo ? selo(rd.selo) : ""}`).join("") : `<span class="muted" style="font-size:13px">Nenhum perfil oficial confirmado nas buscas.</span>`}</div>
        ${dest.length ? `<div class="fatos rfatos">${dest.map((x) => `<article class="fato"><div class="dt">${esc(dataBR(x.data))}</div><div><div class="tt">${esc(x.titulo)} ${selo(x.selo)}</div>${x.resumo ? `<p>${esc(x.resumo)}</p>` : ""}<div class="fs">${fontes(x.fontes)}</div></div></article>`).join("")}</div>` : ""}</div>`
        : `<p class="muted" style="font-size:13.5px">Ainda não há relatório pesquisado para ${esc(nome)}. Use as buscas abaixo ou peça para eu levantar.</p>`}
      <div class="k" style="margin-top:14px">Buscar mais na rede</div>${buscasHTML(nome)}`;
  }
  function openRelatorio(nome) {
    const r = acharRelatorio([nome]);
    const nomes = r ? r.nomes : [nome];
    const c = acharCandidato(nomes);
    if (c) return openProfile(c.x.sq, c.ano, c.cargo);
    const foto = null;
    $("#drawer").innerHTML = `<div class="pf-top"><button class="close" id="pf-close" aria-label="Fechar">✕</button>
      <div class="pf-id"><div class="pf-photo"${r && r.wiki ? ` data-wiki="${esc(r.wiki)}"` : ""}>${esc(initials(nomes[0]))}${foto ? `<img src="${esc(foto)}" alt="" referrerpolicy="no-referrer" onerror="this.remove()" style="position:absolute;inset:0">` : ""}</div>
      <div><div style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;opacity:.7">Relatório</div><h3>${esc(nomes[0])}</h3>${r && r.papel ? `<div class="full">${esc(r.papel)}</div>` : ""}
      ${r && r.partido ? `<div class="badges"><span>${esc(r.partido)}</span></div>` : ""}</div></div></div>
      <div class="pf-body">${relatorioHTML(nomes)}<p class="muted" style="font-size:12.5px;margin-top:16px">Sem votação desta pessoa nas eleições carregadas para ${esc(S.city.meta.municipio)}. Os números por seção entram quando o TSE for liberado.</p></div>`;
    abrirDrawer();
  }


  // ------------------------------------------------------------------ raio-x: onde é forte, onde é fraco
  // Índice de força = % do candidato na área ÷ % dele na cidade × 100 (100 = igual à média dele).
  const CLASSES = [
    [130, "Reduto", "▲▲", "#3987e5"], [110, "Forte", "▲", "#86b6ef"], [90, "Na média", "■", "#8d8b82"],
    [70, "Fraco", "▼", "#e8a07f"], [-1, "Muito fraco", "▼▼", "#d95926"],
  ];
  const classe = (idx) => CLASSES.find(([min]) => idx >= min);
  function raioX(a, sq) {
    const x = a.bySq[sq];
    const base = x.votos / (a.validos || 1);
    const min = Math.max(30, a.validos * 0.02);
    const areas = (o) => Object.values(o).map((z) => {
      const v = z.cand[sq] || 0, share = v / (z.validos || 1);
      const idx = base ? (share / base) * 100 : 0;
      return { z, nome: z.nome, v, val: z.validos, share, idx, cl: classe(idx), gap: Math.max(0, Math.round(base * z.validos - v)), ok: z.validos >= min };
    });
    const bairros = areas(a.bairros), locais = areas(a.locais);
    const porVotos = [...locais].sort((p, q) => q.v - p.v);
    const conc3 = porVotos.slice(0, 3).reduce((t, r) => t + r.v, 0) / (x.votos || 1);
    return { x, base, bairros, locais, conc3, topLocal: porVotos[0] };
  }
  function raioXHTML(a, sq) {
    const r = raioX(a, sq);
    if (!r.x.votos) return "";
    const fortes = r.bairros.filter((b) => b.ok && b.idx >= 110).sort((p, q) => q.idx - p.idx).slice(0, 3);
    const fracos = r.bairros.filter((b) => b.ok && b.idx < 90).sort((p, q) => p.idx - q.idx).slice(0, 3);
    const crescer = [...r.locais].filter((l) => l.ok && l.idx < 100).sort((p, q) => q.gap - p.gap).slice(0, 3);
    const item = (b, extra) => `<div class="rx-i"><span class="rx-b" style="--c:${b.cl[3]}">${b.cl[2]} ${Math.round(b.idx)}</span><div><b>${esc(b.nome)}</b><span class="muted">${fmt(b.v)} votos · ${pct(b.share)} ${extra || ""}</span></div></div>`;
    const lista = [...r.bairros].sort((p, q) => q.idx - p.idx);
    const lim = Math.max(60, ...lista.map((b) => Math.abs(b.idx - 100)));
    const div = lista.map((b) => {
      const d = b.idx - 100, w = (Math.abs(d) / lim) * 50;
      return `<div class="rx-row" ${tip(`<b>${esc(b.nome)}</b><br>${fmt(b.v)} votos · ${pct(b.share)} dos válidos do bairro<br>Índice ${Math.round(b.idx)} · ${b.cl[1]}`)}><div class="lb">${esc(b.nome)}</div><div class="rx-t"><i style="${d >= 0 ? `left:50%;width:${w}%` : `left:${50 - w}%;width:${w}%`};background:${b.cl[3]}"></i><span class="mid"></span></div><div class="x num">${b.cl[2]} ${Math.round(b.idx)}</div></div>`;
    }).join("");
    const conc = r.conc3 >= 0.6 ? "voto concentrado" : r.conc3 >= 0.35 ? "voto médio" : "voto espalhado";
    return `<h4>Raio-X: onde é forte e onde é fraco</h4>
      <p class="muted" style="font-size:12.5px;margin:-4px 0 12px">Índice = % dele na área ÷ % dele na cidade (${pct(r.base)}) × 100. Acima de 100, ele vai melhor ali do que no conjunto da cidade.</p>
      <div class="grid rx3">
        <div class="card"><div class="k">Onde é forte</div>${fortes.map((b) => item(b)).join("") || `<span class="muted">Nenhum bairro acima de 110.</span>`}</div>
        <div class="card"><div class="k">Onde é fraco</div>${fracos.map((b) => item(b)).join("") || `<span class="muted">Nenhum bairro abaixo de 90.</span>`}</div>
        <div class="card"><div class="k">Onde pode crescer</div>${crescer.map((l) => item(l, `· faltam ~${fmt(l.gap)} p/ a média`)).join("") || `<span class="muted">Já está na média ou acima em todos os locais.</span>`}</div>
      </div>
      <div class="rx-conc"><b>${pct(r.conc3, 0)}</b> dos votos dele vêm de 3 locais (${conc})${r.topLocal ? ` · maior reduto em votos: <b>${esc(r.topLocal.nome)}</b> (${fmt(r.topLocal.v)})` : ""}</div>
      <div class="rx-div">${div}</div>
      <div class="legend">${CLASSES.map(([, n, ic, c]) => `<span><i style="background:${c}"></i>${ic} ${n}</span>`).join("")}</div>`;
  }
  function openProfile(sq, ano = S.ano, cargo = S.cargo) {
    const a = agg(ano, cargo), x = a.bySq[sq];
    const porSecao = () => S.city.eleicoes[ano].nivel === "secao";
    if (!x) return;
    const m = S.city.meta;
    const hist = historico(x.pid);
    const hmax = Math.max(...hist.map((h) => h.x.votos), 1);
    const bairros = porSecao() ? Object.values(a.bairros).map((b) => ({ b, v: b.cand[sq] || 0 })).sort((p, q) => q.v - p.v) : [];
    const bmax = bairros[0] ? bairros[0].v : 1;
    const secs = porSecao() ? Object.values(a.secoes).map((s) => ({ s, v: s.cand[sq] || 0 })).filter((r) => r.v).sort((p, q) => q.v - p.v).slice(0, 5) : [];
    const venceuB = bairros.filter(({ b }) => b.rank[0] && b.rank[0][0] === sq).length;
    const u = x.uf;
    const fatos = [["Nome completo", x.nome], ["Número", x.nr], ["Partido", x.partido], ["Federação", x.federacao], ["Situação", x.situacao && cap(situTxt(x.situacao))], ["Ocupação", x.ocupacao && cap(x.ocupacao)], ["Idade", x.idade && x.idade + " anos"], ["Instrução", x.instrucao && cap(x.instrucao)], ["Gênero", x.genero && cap(x.genero)]].filter(([, v]) => v);
    $("#drawer").innerHTML = `<div class="pf-top"><button class="close" id="pf-close" aria-label="Fechar">✕</button>
      <div class="pf-id"><div class="pf-photo">${esc(initials(x.urna))}${x.foto ? `<img src="${esc(x.foto)}" alt="Foto de ${esc(x.urna)}" referrerpolicy="no-referrer" onerror="this.remove()" style="position:absolute;inset:0">` : ""}</div>
      <div><div style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;opacity:.7">${esc(cargoCurto(cargo))} · ${ano}</div><h3>${esc(x.urna)}</h3><div class="full">${esc(x.nome)}</div>
      <div class="badges"><span>${esc(x.partido || "")} ${esc(x.nr || "")}</span>${x.situacao ? `<span>${esc(situTxt(x.situacao))}</span>` : ""}</div></div></div></div>
      <div class="pf-body">
        <h4>Em ${esc(m.municipio)}</h4>
        <div class="grid pf-k">
          <div class="card"><div class="v num">${fmt(x.votos)}</div><div class="l">votos na cidade</div></div>
          <div class="card"><div class="v num">${x._pos}º</div><div class="l">de ${fmt(a.cands.length)} candidatos com voto</div></div>
          <div class="card"><div class="v num">${pct(x.votos / a.validos)}</div><div class="l">dos votos válidos</div></div>
          ${porSecao() ? `<div class="card"><div class="v num">${venceuB}</div><div class="l">de ${bairros.length} bairros vencidos</div></div>` : ""}
          ${u ? `<div class="card"><div class="v num">${fmt(u.total)}</div><div class="l">votos no ${esc(m.uf)}${u.rank ? ` — ${u.rank}º do estado` : ""}</div></div>
          <div class="card"><div class="v num">${pct(x.votos / (u.total || 1))}</div><div class="l">da votação dele veio de ${esc(m.municipio)}${u.posMun ? ` — ${u.posMun}º município dele (de ${u.nMun})` : ""}</div></div>` : ""}
        </div>
        ${porSecao() ? raioXHTML(a, sq) : ""}
        ${bairros.length ? `<h4>Por bairro</h4>${bairros.map(({ b, v }) => `<div class="hbar" ${tip(`${esc(b.nome)}: ${fmt(v)} votos · ${pct(v / (b.validos || 1))} dos válidos do bairro`)}><div class="lb">${esc(b.nome)}</div><div class="t"><i style="width:${(v / bmax) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / (b.validos || 1))}</div></div>`).join("")}` : ""}
        ${secs.length ? `<h4>Melhores seções</h4>${secs.map(({ s, v }) => `<div class="hbar"><div class="lb">Seção ${s.secao}</div><div class="t"><i style="width:${(v / secs[0].v) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / (s.validos || 1))}</div></div><div class="muted" style="font-size:12px;margin:-2px 0 6px">${esc(s.localNome)} · ${esc(s.bairro)}</div>`).join("")}` : ""}
        <h4>Histórico em ${esc(m.municipio)}</h4>
        <div class="timeline">${hist.map((h) => `<div class="tl ${h.ano == ano && h.cargo === cargo ? "cur" : ""}"><div class="y">${h.ano} <span class="muted" style="font-weight:500;font-size:14px">· ${esc(cargoCurto(h.cargo))}</span></div>
          <div class="c">${fmt(h.x.votos)} votos · ${pct(h.share)} dos válidos · ${h.pos}º de ${h.n}${h.x.situacao ? ` · ${esc(situTxt(h.x.situacao))}` : ""} · ${esc(h.x.partido || "")}</div><div class="t"><i style="width:${(h.x.votos / hmax) * 100}%"></i></div></div>`).join("")}</div>
        ${hist.length < 2 ? `<p class="muted" style="font-size:13px">Sem outras candidaturas ligadas a esta pessoa nos anos carregados para ${esc(m.municipio)}.</p>` : ""}
        ${relatorioHTML([x.urna, x.nome])}
        ${fatos.length ? `<h4>Ficha</h4><dl class="facts">${fatos.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl>` : ""}
        ${divulgaLink(ano, cargo, x.sq) ? `<p style="margin-top:14px"><a class="btn" style="text-decoration:none;color:var(--ink)" href="${divulgaLink(ano, cargo, x.sq)}" target="_blank" rel="noopener">Ficha oficial no TSE (DivulgaCand) ↗</a></p>` : ""}
        <div style="margin-top:24px;display:flex;gap:10px;flex-wrap:wrap">
          <button class="btn primary" type="button" data-cmp="${x.sq}">${S.cmp.includes(x.sq) ? "✓ Na comparação" : "+ Comparar"}</button>
          ${porSecao() ? `<button class="btn" type="button" id="pf-secoes" data-sq="${x.sq}">Ver nas seções</button>` : ""}
        </div>
      </div>`;
    abrirDrawer();
  }
  function abrirDrawer() {
    const d = $("#drawer"), sc = $("#scrim");
    d.setAttribute("aria-hidden", "false"); sc.classList.add("on");
    if (window.gsap) { gsap.to(d, { x: 0, xPercent: 0, duration: 0.45, ease: "power3.out" }); gsap.to(sc, { opacity: 1, duration: 0.3 }); gsap.from(".pf-body > *", { y: 16, opacity: 0, stagger: 0.03, duration: 0.4, delay: 0.1 }); }
    else { d.style.transform = "none"; sc.style.opacity = 1; }
    d.scrollTop = 0;
  }
  function closeProfile() {
    const d = $("#drawer"), sc = $("#scrim");
    d.setAttribute("aria-hidden", "true"); sc.classList.remove("on");
    if (window.gsap) { gsap.to(d, { xPercent: 100, duration: 0.35, ease: "power2.in" }); gsap.to(sc, { opacity: 0, duration: 0.3 }); }
    else { d.style.transform = ""; sc.style.opacity = 0; }
  }

  function toggleCmp(sq) {
    const i = S.cmp.indexOf(sq);
    if (i >= 0) S.cmp.splice(i, 1);
    else { if (S.cmp.length >= 4) S.cmp.shift(); S.cmp.push(sq); }
    renderRanking(); renderComparar();
  }

  // ------------------------------------------------------------------ eventos
  function bind() {
    $("#sel-city").addEventListener("change", async (ev) => { await loadCity(ev.target.value); S.cmp = []; S.secSel = []; renderAll(); });
    $("#sel-year").addEventListener("change", (ev) => {
      S.ano = ev.target.value;
      const cs = cargosDe(S.ano);
      if (!cs.includes(S.cargo)) S.cargo = cs[0];
      S.cmp = []; S.secSel = []; S.secCand = "";
      renderAll();
    });
    document.addEventListener("click", (ev) => {
      const t = ev.target;
      const rl = t.closest("[data-rel]");
      if (rl) { ev.preventDefault(); openRelatorio(rl.dataset.rel); return; }
      const cargo = t.closest("[data-cargo]");
      if (cargo) { S.cargo = cargo.dataset.cargo; S.cmp = []; S.secSel = []; S.secCand = ""; renderAll(); return; }
      const cmp = t.closest("[data-cmp]");
      if (cmp) { ev.stopPropagation(); toggleCmp(cmp.dataset.cmp); if (cmp.closest("#drawer")) cmp.textContent = S.cmp.includes(cmp.dataset.cmp) ? "✓ Na comparação" : "+ Comparar"; return; }
      const rm = t.closest("[data-rm]");
      if (rm) { toggleCmp(rm.dataset.rm); return; }
      if (t.closest("#pf-secoes")) { S.secCand = t.closest("#pf-secoes").dataset.sq; S.secSort = "cand"; closeProfile(); renderSecoes(); $("#secoes").scrollIntoView({ behavior: "smooth" }); return; }
      const sq = t.closest("[data-sq]");
      if (sq && !t.closest("#drawer .hbar")) {
        ev.preventDefault();
        if (sq.dataset.pano) openProfile(sq.dataset.sq, sq.dataset.pano, sq.dataset.pcargo);
        else if (t.closest("#mapa, .fpop")) openProfile(sq.dataset.sq, S.map.ano, S.map.cargo);
        else if (t.closest("#deputado") && S.dep.cur) openProfile(sq.dataset.sq, S.dep.cur.ano, S.dep.cur.cargo);
        else openProfile(sq.dataset.sq);
        return;
      }
      if (t.closest("#pf-close") || t.id === "scrim") { closeProfile(); return; }
      const sort = t.closest("[data-sort]");
      if (sort) { S.secSort = sort.dataset.sort; renderSecoes(); return; }
      const sec = t.closest("[data-sec]");
      if (sec) {
        const id = sec.dataset.sec, i = S.secSel.indexOf(id);
        if (i >= 0) S.secSel.splice(i, 1); else { if (S.secSel.length >= 4) S.secSel.shift(); S.secSel.push(id); }
        renderSecoes(); return;
      }
      if (t.id === "sec-clear") { S.secSel = []; renderSecoes(); return; }
      if (t.id === "rank-all") { S.rankAll = true; renderRanking(); return; }
      if (t.id === "rank-less") { S.rankAll = false; renderRanking(); $("#ranking").scrollIntoView(); return; }
      const by = t.closest("[data-by]");
      if (by) { S.cmpBy = by.dataset.by; renderComparar(); return; }
      const mode = t.closest("[data-mode]");
      if (mode) { S.cmpMode = mode.dataset.mode; renderComparar(); return; }
      const mn = t.closest("[data-mnav]");
      if (mn) { ev.preventDefault(); desenharMapa.nav(mn.dataset.mnav); return; }
      const czn = t.closest("[data-cznivel]"); if (czn) { S.cruz.nivel = czn.dataset.cznivel; renderCruzamento(); return; }
      const czr = t.closest("[data-czrm]"); if (czr) { S.cruz.aliados = S.cruz.aliados.filter((q) => q !== czr.dataset.czrm); renderCruzamento(); return; }
      const tt = t.closest("[data-ttipo]"); if (tt) { S.traj.tipo = tt.dataset.ttipo; S.traj.init = false; renderTrajetoria(); return; }
      const tm = t.closest("[data-tmodo]"); if (tm) { S.traj.modo = tm.dataset.tmodo; renderTrajetoria(); return; }
      const tr = t.closest("[data-trm]"); if (tr) { S.traj.sel = S.traj.sel.filter((p) => p !== tr.dataset.trm); if (!S.traj.sel.length) S.traj.sel = []; renderTrajetoria(); return; }
      const md = t.closest("[data-mdrill]"); if (md) { desenharMapa.nav("drill", md.dataset.mdrill); return; }
      const mb = t.closest("[data-mbai]"); if (mb) { desenharMapa.nav("bai", mb.dataset.mbai); return; }
      const ml = t.closest("[data-mloc]"); if (ml) { desenharMapa.nav("loc", ml.dataset.mloc); return; }
      const ms = t.closest("[data-msec]"); if (ms) { desenharMapa.nav("sec", ms.dataset.msec); return; }
      const uf = t.closest("[data-unfoco]"); if (uf) { S.map.foco = S.map.foco.filter((q) => q !== uf.dataset.unfoco); renderMapa(); return; }
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") closeProfile();
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches("[role=button][data-sq]")) { ev.preventDefault(); openProfile(ev.target.dataset.sq); }
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches("[role=button][data-rel]")) { ev.preventDefault(); openRelatorio(ev.target.dataset.rel); }
    });
    document.addEventListener("input", (ev) => {
      const t = ev.target;
      if (t.id === "lim") {
        S.limiar = +t.value; store.set("limiar", S.limiar);
        clearTimeout(bind._lt); bind._lt = setTimeout(() => { renderHero(); renderKPIs(); renderRanking(); renderBairros(); renderMapa(); renderSecoes(); $("#lim").focus(); }, 120);
      }
      if (t.id === "busca") { S.busca = t.value; renderRanking(); const b = $("#busca"); b.focus(); b.setSelectionRange(b.value.length, b.value.length); }
    });
    document.addEventListener("change", (ev) => {
      const t = ev.target;
      if (t.id === "sec-bairro") { S.secBairro = t.value; renderSecoes(); }
      if (t.id === "sec-cand") { S.secCand = t.value; S.secSort = t.value ? "cand" : "validos"; renderSecoes(); }
      if (t.id === "map-el") { const [ano, cargo] = t.value.split("|"); Object.assign(S.map, { ano, cargo, bairro: null, local: null, secao: null, zoom: false, foco: [] }); renderMapa(); }
      if (t.id === "cz-depel") { S.cruz.depEl = t.value; S.cruz.dep = ""; renderCruzamento(); }
      if (t.id === "cz-dep") { S.cruz.dep = t.value; renderCruzamento(); }
      if (t.id === "cz-verel") { S.cruz.verEl = t.value; S.cruz.aliados = []; renderCruzamento(); }
      if (t.id === "cz-add" && t.value) { S.cruz.aliados.push(t.value); renderCruzamento(); }
      if (t.id === "map-rx") { S.map.rx = t.value; renderMapa(); }
      if (t.id === "map-foco" && t.value) { S.map.foco.push(t.value); renderMapa(); }
      if (t.id === "cmp-add" && t.value) toggleCmp(t.value);
      if (t.id === "traj-add" && t.value) { const d = ($("#trajetoria")._opts || []).find((z) => t.value.startsWith(z.urna + " — " + z.nome)); if (d) { S.traj.sel.push(d.pid); renderTrajetoria(); } }
      if (t.id === "dep-sel") { S.dep = { pid: t.value, ano: null }; renderDeputado(); }
      if (t.id === "dep-ano") { S.dep.ano = t.value; renderDeputado(); }
      if (t.id === "dep-city") { const pid = S.dep.pid; loadCity(t.value).then(() => { S.dep.pid = pid; S.cmp = []; S.secSel = []; renderAll(); $("#deputado").scrollIntoView(); }); }
    });
    // tooltip único
    const tipEl = $("#tip");
    document.addEventListener("mousemove", (ev) => {
      const t = ev.target.closest && ev.target.closest("[data-tip]");
      if (!t) { tipEl.style.opacity = 0; return; }
      tipEl.innerHTML = t.getAttribute("data-tip");
      const w = tipEl.offsetWidth, h = tipEl.offsetHeight;
      tipEl.style.left = Math.min(ev.clientX + 14, innerWidth - w - 8) + "px";
      tipEl.style.top = (ev.clientY + 16 + h > innerHeight ? ev.clientY - h - 12 : ev.clientY + 16) + "px";
      tipEl.style.opacity = 1;
    });
    // aba ativa
    const links = $$("nav.tabs a");
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) links.forEach((l) => l.classList.toggle("on", l.getAttribute("href") === "#" + e.target.id)); }), { rootMargin: "-40% 0px -55% 0px" });
    ["visao", "quem", "ficha", "mapa", "estrategia", "trajetoria", "deputado", "ranking", "bairros", "secoes", "comparar", "historico"].forEach((id) => io.observe(document.getElementById(id)));
    if (window.gsap) gsap.set("#drawer", { x: 0, xPercent: 100 });
    addEventListener("resize", () => { clearTimeout(bind._rt); bind._rt = setTimeout(() => desenharMapa.fit && desenharMapa.fit(), 200); });
    $("#btn-intro").addEventListener("click", () => window.Intro && window.Intro.play());
  }

  let revealIO;
  function revealOnScroll() {
    if (!window.gsap || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    revealIO ||= new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { gsap.to(e.target, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }); revealIO.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px" });
    $$("section.blk:not(.seen), #sec-kpis:not(.seen)").forEach((el) => { el.classList.add("reveal", "seen"); revealIO.observe(el); });
  }



  // ------------------------------------------------------------------ fotos via Wikipédia (carregadas pelo navegador de quem abre a página)
  const wikiCache = (() => { try { return JSON.parse(localStorage.getItem("plenaria.wiki") || "{}"); } catch (e) { return {}; } })();
  async function fotoWiki(titulo) {
    if (titulo in wikiCache) return wikiCache[titulo];
    let url = null;
    for (const lang of ["pt", "en"]) {
      try {
        const r = await fetch(`https://${lang}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(titulo)}`);
        if (r.ok) { const j = await r.json(); if (j.thumbnail && j.thumbnail.source) { url = j.thumbnail.source; break; } }
      } catch (e) { /* sem rede */ }
    }
    wikiCache[titulo] = url;
    try { localStorage.setItem("plenaria.wiki", JSON.stringify(wikiCache)); } catch (e) { /* ok */ }
    return url;
  }
  function hidratarFotos(raiz) {
    if (!raiz || !raiz.querySelectorAll) return;
    [...(raiz.matches && raiz.matches("[data-wiki]") ? [raiz] : []), ...raiz.querySelectorAll("[data-wiki]")].forEach(async (el) => {
      if (el.dataset.wok) return; el.dataset.wok = "1";
      const u = await fotoWiki(el.dataset.wiki);
      if (u && !el.querySelector("img")) el.insertAdjacentHTML("beforeend", `<img src="${esc(u)}" alt="" referrerpolicy="no-referrer" onerror="this.remove()" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 20%;border-radius:50%">`);
    });
  }
  if ("MutationObserver" in window) new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && hidratarFotos(n)))).observe(document.body, { childList: true, subtree: true });
  // ------------------------------------------------------------------ movimento: barras crescem do zero, números contam, blocos sobem
  const MOV = !matchMedia("(prefers-reduced-motion: reduce)").matches;
  const SEL_BAR = ".rrow .bar i, .hbar .t i, .tl .t i, .gbars .b i, .rx-t i, .stk i";
  const SEL_NUM = ".kpi .v, .dep-k .v, .pf-k .v, .tk b, .cz-q .n, .rrow .vv, .lchip .n, .acard .n, .qbig b, .gv b, .gvd b, .rts b, .qrow .x, .lr .x";
  const SEL_POP = ".card, .rrow, .fato, .cpick, .li, .lig, .rt, .qrow, .lr, .pux";
  const contar = (el) => {
    const m = el.textContent.trim().match(/^([^\d]*)(\d{1,3}(?:\.\d{3})*|\d+)(,\d+)?(.*)$/);
    if (!m || !window.gsap) return;
    const dec = m[3] ? m[3].length - 1 : 0;
    const alvo = parseFloat(m[2].replace(/\./g, "") + (m[3] ? "." + m[3].slice(1) : ""));
    const o = { v: 0 };
    gsap.to(o, { v: alvo, duration: 1.2, ease: "power2.out", onUpdate: () => { el.textContent = m[1] + o.v.toLocaleString("pt-BR", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + m[4]; } });
  };
  const io = "IntersectionObserver" in window ? new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    const el = e.target; io.unobserve(el);
    if (el.classList.contains("anim-bar")) el.style.transform = "scaleX(1)";
    if (el.classList.contains("anim-pop")) el.classList.add("in");
    if (el.dataset.conta) contar(el);
    if (el.tagName === "svg") desenharSVG(el);
  }), { rootMargin: "0px 0px -6% 0px" }) : null;
  function desenharSVG(svg) {
    if (!window.gsap) return;
    svg.querySelectorAll("polyline, line[stroke-width='2']").forEach((l) => {
      const n = l.getTotalLength ? l.getTotalLength() : 0; if (!n) return;
      const dash = l.getAttribute("stroke-dasharray");
      gsap.fromTo(l, { strokeDasharray: n, strokeDashoffset: n }, { strokeDashoffset: 0, duration: 1.2, ease: "power2.out", onComplete: () => { l.style.strokeDasharray = dash || ""; l.style.strokeDashoffset = ""; } });
    });
    gsap.from(svg.querySelectorAll("circle"), { scale: 0, transformOrigin: "50% 50%", transformBox: "fill-box", duration: 0.5, ease: "back.out(2)", stagger: 0.02, delay: 0.3 });
    gsap.from(svg.querySelectorAll("rect[rx]"), { scaleY: 0, transformOrigin: "50% 100%", transformBox: "fill-box", duration: 0.9, ease: "power3.out", stagger: 0.06 });
    gsap.from(svg.querySelectorAll("text.lab"), { opacity: 0, duration: 0.6, delay: 0.8 });
  }
  function animar(raiz) {
    if (!MOV || !io || !raiz || !raiz.querySelectorAll) return;
    const pega = (sel) => [...(raiz.matches && raiz.matches(sel) ? [raiz] : []), ...raiz.querySelectorAll(sel)].filter((el) => !el.dataset.a && (el.dataset.a = "1"));
    pega(SEL_BAR).forEach((el, i) => {
      el.classList.add("anim-bar");
      const neg = el.closest(".rx-t") && parseFloat(el.style.left) < 50;
      el.style.transformOrigin = neg ? "right center" : "left center";
      el.style.transform = "scaleX(0)";
      el.style.transitionDelay = `${Math.min(i % 14, 12) * 45}ms`;
      io.observe(el);
    });
    pega(SEL_NUM).forEach((el) => { el.dataset.conta = "1"; io.observe(el); });
    pega(SEL_POP).forEach((el, i) => { if (el.closest("#intro, .leaflet-pane")) return; el.classList.add("anim-pop"); el.style.transitionDelay = `${Math.min(i % 12, 10) * 40}ms`; io.observe(el); });
    pega("svg.chart").forEach((el) => io.observe(el));
  }
  if (MOV && "MutationObserver" in window) {
    new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && animar(n)))).observe(document.body, { childList: true, subtree: true });
  }

  // ------------------------------------------------------------------ API p/ a intro
  const ready = (async () => {
    await loadCity(store.get("cidade", null));
    renderAll(); bind();
  })();
  ready.catch((err) => { document.body.innerHTML = `<div class="wrap" style="padding:60px 16px"><h1>Não foi possível carregar os dados</h1><p class="muted">${esc(err.message)}</p></div>`; });

  window.App = {
    ready,
    introData() {
      const ctx = (S.city.contexto || []).filter((c) => c.turno === 1 && c.aptos && c.secoes);
      const ano = Math.max(...ctx.map((c) => c.ano));
      const c = ctx.find((x) => x.ano === ano && x.cargo === "deputado_estadual") || ctx.find((x) => x.ano === ano);
      return c ? { ...c, municipio: S.city.meta.municipio, uf: S.city.meta.uf } : null;
    },
    show() {
      const app = $("#app");
      if (window.gsap) gsap.to(app, { opacity: 1, duration: 0.6 }); else app.style.opacity = 1;
      if (window.gsap && !matchMedia("(prefers-reduced-motion: reduce)").matches) gsap.from(".hero h1, .hero p", { y: 40, opacity: 0, stagger: 0.12, duration: 0.9, ease: "power3.out", delay: 0.1 });
    },
  };
})();
