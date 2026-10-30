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
    mapCand: "", cmpBy: "bairro", cmpMode: "votos",
    dep: { pid: "", ano: null },
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
    }
    S.city = window.PLENARIA_DATA[reg.id];
    S.ficha = (window.PLENARIA_FICHAS || {})[reg.id] || null;
    S.local = (window.PLENARIA_LOCAL || {})[reg.id] || null;
    S.cityId = reg.id;
    store.set("cidade", reg.id);
    const anos = Object.keys(S.city.eleicoes).sort().reverse();
    // prioriza a eleição mais recente com detalhe por seção
    S.ano = anos.find((a) => S.city.eleicoes[a].nivel === "secao") || anos[0];
    S.cargo = cargosDe(S.ano)[0];
    cache.clear();
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
    `<span class="${cls}" style="position:relative">${esc(initials(x.urna))}${x.foto ? `<img src="${esc(x.foto)}" alt="" loading="lazy" style="position:absolute;inset:0" onerror="this.remove()">` : ""}</span>`;
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

  function renderHero() {
    const a = agg(), m = S.city.meta, c = C();
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

  function renderRanking() {
    const a = agg();
    const rel = new Set(relevantes(a).map((x) => x.sq));
    let lista = a.cands;
    if (S.busca) { const q = S.busca.toLowerCase(); lista = lista.filter((x) => (x.urna + " " + x.nome + " " + x.partido + " " + x.nr).toLowerCase().includes(q)); }
    const total = lista.length;
    if (!S.rankAll && !S.busca) lista = lista.slice(0, Math.max(15, rel.size));
    const max = a.cands[0] ? a.cands[0].votos : 1;
    $("#ranking").innerHTML = `<div class="blk-h"><div><h2>Os mais <em class="s">votados</em></h2><p class="lead">Clique em um nome para abrir o perfil: foto, desempenho por bairro e histórico na cidade. Use ◯ para separar até 4 candidatos para comparar.</p></div>
      <div class="tools"><input class="search" id="busca" type="search" placeholder="Buscar nome, partido ou número" value="${esc(S.busca)}"></div></div>
      <div class="rank">${lista.map((x) => {
        const sl = slotOf(x.sq);
        return `<div class="rrow ${rel.has(x.sq) ? "" : "dim"}" data-sq="${x.sq}" role="button" tabindex="0">
          <div class="pos num">${x._pos}º</div>${avatar(x)}
          <div><div class="nm">${esc(x.urna)}</div><div class="meta">${esc(x.partido || "")} · ${esc(x.nr || "")}${situ(x)}</div></div>
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

  function renderMapa() {
    const el = $("#mapa");
    const head = (extra = "") => `<div class="blk-h"><div><h2>Mapa dos <em class="s">locais de votação</em></h2><p class="lead">Cada círculo é um local de votação na posição cadastrada no TSE; o tamanho acompanha os votos válidos.</p></div>${extra}</div>`;
    if (!porSecao()) { el.innerHTML = head() + naoSecao("local de votação"); return; }
    const a = agg();
    const locs = Object.values(a.locais).filter((l) => l.lat != null && l.lon != null);
    if (locs.length < 2) { el.innerHTML = head() + `<div class="notice">O TSE não publicou coordenadas suficientes dos locais de votação desta cidade em ${S.ano}.</div>`; return; }
    const rel = relevantes(a);
    const sel = `<div class="tools"><select class="pill" id="map-cand"><option value="">Colorir pelo vencedor de cada local</option>${rel.map((x) => `<option value="${x.sq}" ${x.sq === S.mapCand ? "selected" : ""}>Votos de ${esc(x.urna)}</option>`).join("")}</select></div>`;
    // projeção equiretangular corrigida pela latitude
    const lat0 = locs.reduce((s, l) => s + l.lat, 0) / locs.length;
    const kx = Math.cos((lat0 * Math.PI) / 180);
    const xs = locs.map((l) => l.lon * kx), ys = locs.map((l) => -l.lat);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const W = 800, H = 600, P = 60;
    const k = Math.min((W - 2 * P) / (x1 - x0 || 1e-6), (H - 2 * P) / (y1 - y0 || 1e-6));
    const ox = (W - (x1 - x0) * k) / 2, oy = (H - (y1 - y0) * k) / 2;
    const vmax = Math.max(...locs.map((l) => l.validos), 1);
    // cores: os 3 que mais venceram locais ganham cor; demais = cinza
    const vit = {};
    locs.forEach((l) => l.rank[0] && (vit[l.rank[0][0]] = (vit[l.rank[0][0]] || 0) + 1));
    const cores = {};
    Object.entries(vit).sort((p, q) => q[1] - p[1]).slice(0, 3).forEach(([sq], i) => (cores[sq] = SLOTS[i]));
    const cand = S.mapCand && a.bySq[S.mapCand];
    const shareMax = cand ? Math.max(...locs.map((l) => (l.cand[cand.sq] || 0) / (l.validos || 1)), 1e-6) : 1;
    const circles = locs.sort((p, q) => q.validos - p.validos).map((l) => {
      const cx = ox + (l.lon * kx - x0) * k, cy = oy + (-l.lat - y0) * k;
      const r = 6 + 26 * Math.sqrt(l.validos / vmax);
      const w = l.rank[0];
      let fill, op = 0.9;
      if (cand) { const s = (l.cand[cand.sq] || 0) / (l.validos || 1); fill = "#3987e5"; op = 0.12 + 0.85 * (s / shareMax); }
      else fill = (w && cores[w[0]]) || "var(--other)";
      const t = `<b>${esc(l.nome)}</b><br>${esc(l.bairro)} · ${l.secoes.length} seções · ${fmt(l.validos)} válidos<br>` +
        (cand ? `${esc(cand.urna)}: ${fmt(l.cand[cand.sq] || 0)} votos (${pct((l.cand[cand.sq] || 0) / (l.validos || 1))})` : w ? `1º: ${esc(a.bySq[w[0]].urna)} — ${fmt(w[1])} (${pct(w[1] / l.validos)})` : "");
      return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r.toFixed(1)}" fill="${fill}" fill-opacity="${op.toFixed(2)}" stroke="var(--surface)" stroke-width="2" data-local="${esc(l.id)}" ${tip(t)} style="cursor:pointer"/>`;
    }).join("");
    const legenda = cand
      ? `<span><i style="background:#3987e5"></i>mais votos de ${esc(cand.urna)}</span><span><i style="background:rgba(57,135,229,.15)"></i>menos votos</span>`
      : Object.entries(cores).map(([sq, c]) => `<span><i style="background:${c}"></i>${esc(a.bySq[sq].urna)} (${vit[sq]} locais)</span>`).join("") + `<span><i style="background:var(--other)"></i>outros</span>`;
    el.innerHTML = head(sel) + `<div class="map-wrap"><div><div class="map"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Mapa dos locais de votação">${circles}</svg></div><div class="legend">${legenda}</div></div>
      <div class="card" id="map-side"><div class="muted" style="font-size:14px">Passe o mouse ou toque em um local para ver o detalhe.</div></div></div>`;
  }
  function mapSide(lid) {
    const a = agg(), l = a.locais[lid];
    if (!l) return;
    const link = l.lat != null ? `https://www.google.com/maps/search/?api=1&query=${l.lat},${l.lon}` : null;
    $("#map-side").innerHTML = `<div style="font-weight:900;font-size:20px;letter-spacing:-.02em">${esc(l.nome)}</div>
      <div class="muted" style="font-size:13px;margin:4px 0 14px">${esc(l.endereco || "")}${l.endereco ? " · " : ""}${esc(l.bairro)}<br>Seções: ${l.secoes.map((s) => s.split("-")[1]).join(", ")} · ${fmt(l.aptos)} aptos</div>
      ${l.rank.slice(0, 6).map(([sq, v]) => `<div class="hbar" data-sq="${sq}" style="cursor:pointer"><div class="lb">${esc(a.bySq[sq].urna)}</div><div class="t"><i style="width:${(v / l.rank[0][1]) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / l.validos)}</div></div>`).join("")}
      ${link ? `<a class="btn more" style="display:inline-block;text-decoration:none" href="${link}" target="_blank" rel="noopener">Abrir no mapa ↗</a>` : ""}`;
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
    const ligado = (d) => `<div class="lig"><div><b>${esc(d.nome)}</b> <span class="muted">${esc([d.cargo, d.partido].filter(Boolean).join(" · "))}</span></div>
      <div class="r">${esc(d.resultado || "")}${d.votosCidade != null ? ` · <b class="num">${fmt(d.votosCidade)}</b> em ${esc(m.municipio)}` : d.votosCidadeTxt ? ` · ${esc(d.votosCidadeTxt)} em ${esc(m.municipio)}` : ""}</div>
      ${d.selo ? `<div class="f">${selo(d.selo)} ${fontes(d.fontes)}</div>` : ""}</div>`;
    el.innerHTML = head +
      `<div class="grid poder">${(F.poder || []).map((p) => `<div class="card pcard"><div class="l">${esc(p.papel)}</div><div class="v">${esc(p.nome)}</div>${p.detalhe ? `<div class="d">${esc(p.detalhe)}</div>` : ""}<div class="f">${selo(p.selo)} ${fontes(p.fontes)}</div></div>`).join("")}</div>` +
      (grupos.length ? sub("Grupos políticos") + `<div class="grid grupos">${grupos.map((g, i) => { const [pl, pc] = POSICAO[g.posicao] || [g.posicao || "", ""]; return `<div class="card gcard" style="--g:${SLOTS[i] || "var(--other)"}">
        <div class="gh"><div><div class="l">${esc(g.nome)}</div><div class="v">${esc(g.lider || "")}</div></div>${pl ? `<span class="pos ${pc}">${esc(pl)}</span>` : ""}</div>
        ${g.resumo ? `<p class="d">${esc(g.resumo)}</p>` : ""}
        ${(g.ligados || []).length ? `<div class="k">Deputados e lideranças ligados</div>${g.ligados.map(ligado).join("")}` : ""}
        ${g.vereadores ? `<div class="k">Câmara</div><p class="d">${esc(g.vereadores)}</p>` : ""}
        ${g.forca ? `<div class="forca"><span>Força nas urnas 2026</span><b>${esc(g.forca)}</b></div>` : ""}</div>`; }).join("")}</div>` : "") +
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
        <div class="pf-photo">${esc(initials(x.urna))}${x.foto ? `<img src="${esc(x.foto)}" alt="Foto de ${esc(x.urna)}" onerror="this.remove()" style="position:absolute;inset:0">` : ""}</div>
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
        </div>` : `<div class="notice" style="margin-top:16px">Locais e bairros não disponíveis para ${esc(ent.ano)} (só totais do município).</div>`}
        <h4>Histórico em ${esc(m.municipio)}</h4>
        <div class="timeline">${hist.map((h) => { const [hs] = statusEleito(h.x.situacao); return `<div class="tl ${h.ano == ent.ano && h.cargo === ent.cargo ? "cur" : ""}"><div class="y">${h.ano} <span class="muted" style="font-weight:500;font-size:14px">· ${esc(cargoCurto(h.cargo))} · ${esc(h.x.partido || "")}</span></div>
          <div class="c">${fmt(h.x.votos)} votos na cidade · ${pct(h.share)} dos válidos · ${h.pos}º de ${h.n}${h.x.uf && h.x.uf.total ? ` · ${fmt(h.x.uf.total)} no estado` : ""} · ${esc(hs)}</div><div class="t"><i style="width:${(h.x.votos / hmax) * 100}%"></i></div></div>`; }).join("")}</div>
      </div></div>`;
  }

  function renderAll() {
    renderControls(); renderHero(); renderKPIs(); renderFicha(); renderDeputado(); renderRanking(); renderBairros(); renderMapa(); renderSecoes(); renderComparar(); renderHistorico(); renderFooter();
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
  function openProfile(sq) {
    const a = agg(), x = a.bySq[sq];
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
      <div class="pf-id"><div class="pf-photo">${esc(initials(x.urna))}${x.foto ? `<img src="${esc(x.foto)}" alt="Foto de ${esc(x.urna)}" onerror="this.remove()" style="position:absolute;inset:0">` : ""}</div>
      <div><div style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;opacity:.7">${esc(cargoCurto(S.cargo))} · ${S.ano}</div><h3>${esc(x.urna)}</h3><div class="full">${esc(x.nome)}</div>
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
        ${bairros.length ? `<h4>Por bairro</h4>${bairros.map(({ b, v }) => `<div class="hbar" ${tip(`${esc(b.nome)}: ${fmt(v)} votos · ${pct(v / (b.validos || 1))} dos válidos do bairro`)}><div class="lb">${esc(b.nome)}</div><div class="t"><i style="width:${(v / bmax) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / (b.validos || 1))}</div></div>`).join("")}` : ""}
        ${secs.length ? `<h4>Melhores seções</h4>${secs.map(({ s, v }) => `<div class="hbar"><div class="lb">Seção ${s.secao}</div><div class="t"><i style="width:${(v / secs[0].v) * 100}%"></i></div><div class="x num">${fmt(v)} · ${pct(v / (s.validos || 1))}</div></div><div class="muted" style="font-size:12px;margin:-2px 0 6px">${esc(s.localNome)} · ${esc(s.bairro)}</div>`).join("")}` : ""}
        <h4>Histórico em ${esc(m.municipio)}</h4>
        <div class="timeline">${hist.map((h) => `<div class="tl ${h.ano == S.ano && h.cargo === S.cargo ? "cur" : ""}"><div class="y">${h.ano} <span class="muted" style="font-weight:500;font-size:14px">· ${esc(cargoCurto(h.cargo))}</span></div>
          <div class="c">${fmt(h.x.votos)} votos · ${pct(h.share)} dos válidos · ${h.pos}º de ${h.n}${h.x.situacao ? ` · ${esc(situTxt(h.x.situacao))}` : ""} · ${esc(h.x.partido || "")}</div><div class="t"><i style="width:${(h.x.votos / hmax) * 100}%"></i></div></div>`).join("")}</div>
        ${hist.length < 2 ? `<p class="muted" style="font-size:13px">Sem outras candidaturas ligadas a esta pessoa nos anos carregados para ${esc(m.municipio)}.</p>` : ""}
        ${fatos.length ? `<h4>Ficha</h4><dl class="facts">${fatos.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl>` : ""}
        <div style="margin-top:24px;display:flex;gap:10px;flex-wrap:wrap">
          <button class="btn primary" type="button" data-cmp="${x.sq}">${S.cmp.includes(x.sq) ? "✓ Na comparação" : "+ Comparar"}</button>
          ${porSecao() ? `<button class="btn" type="button" id="pf-secoes" data-sq="${x.sq}">Ver nas seções</button>` : ""}
        </div>
      </div>`;
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
      S.cmp = []; S.secSel = []; S.secCand = ""; S.mapCand = "";
      renderAll();
    });
    document.addEventListener("click", (ev) => {
      const t = ev.target;
      const cargo = t.closest("[data-cargo]");
      if (cargo) { S.cargo = cargo.dataset.cargo; S.cmp = []; S.secSel = []; S.secCand = ""; S.mapCand = ""; renderAll(); return; }
      const cmp = t.closest("[data-cmp]");
      if (cmp) { ev.stopPropagation(); toggleCmp(cmp.dataset.cmp); if (cmp.closest("#drawer")) cmp.textContent = S.cmp.includes(cmp.dataset.cmp) ? "✓ Na comparação" : "+ Comparar"; return; }
      const rm = t.closest("[data-rm]");
      if (rm) { toggleCmp(rm.dataset.rm); return; }
      if (t.closest("#pf-secoes")) { S.secCand = t.closest("#pf-secoes").dataset.sq; S.secSort = "cand"; closeProfile(); renderSecoes(); $("#secoes").scrollIntoView({ behavior: "smooth" }); return; }
      const sq = t.closest("[data-sq]");
      if (sq && !t.closest("#drawer .hbar")) { ev.preventDefault(); openProfile(sq.dataset.sq); return; }
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
      const loc = t.closest("[data-local]");
      if (loc) mapSide(loc.dataset.local);
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") closeProfile();
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches("[role=button][data-sq]")) { ev.preventDefault(); openProfile(ev.target.dataset.sq); }
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
      if (t.id === "map-cand") { S.mapCand = t.value; renderMapa(); }
      if (t.id === "cmp-add" && t.value) toggleCmp(t.value);
      if (t.id === "dep-sel") { S.dep = { pid: t.value, ano: null }; renderDeputado(); }
      if (t.id === "dep-ano") { S.dep.ano = t.value; renderDeputado(); }
      if (t.id === "dep-city") { const pid = S.dep.pid; loadCity(t.value).then(() => { S.dep.pid = pid; S.cmp = []; S.secSel = []; renderAll(); $("#deputado").scrollIntoView(); }); }
    });
    document.addEventListener("mouseover", (ev) => { const l = ev.target.closest("[data-local]"); if (l) mapSide(l.dataset.local); });
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
    ["visao", "ficha", "deputado", "ranking", "bairros", "mapa", "secoes", "comparar", "historico"].forEach((id) => io.observe(document.getElementById(id)));
    if (window.gsap) gsap.set("#drawer", { x: 0, xPercent: 100 });
    $("#btn-intro").addEventListener("click", () => window.Intro && window.Intro.play());
  }

  let revealIO;
  function revealOnScroll() {
    if (!window.gsap || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    revealIO ||= new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { gsap.to(e.target, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }); revealIO.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px" });
    $$("section.blk:not(.seen), #sec-kpis:not(.seen)").forEach((el) => { el.classList.add("reveal", "seen"); revealIO.observe(el); });
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
