/* Quociente eleitoral, partidário e sobras (eleições proporcionais).
 * Usado pela página e pela conferência automática (scripts/verificar.mjs).
 * Regras: art. 106–109 do Código Eleitoral.
 *  - QE = válidos ÷ vagas (fração > 0,5 arredonda para cima).
 *  - QP = votos do partido ÷ QE (parte inteira). Até 2016 havia coligações: as cadeiras saíam por coligação.
 *  - 2020: cada eleito precisa de 10% do QE; todos os partidos disputam as sobras por maiores médias.
 *  - 2022+: QP exige 10% do QE; sobras para partidos com 80% do QE e candidatos com 20%;
 *    o que restar vai a todos os partidos por maiores médias (STF, ADIs 7228/7263). */
(function (raiz) {
  function quociente(cargo, ano) {
    const vagas = cargo.vagas, partidos = cargo.partidos;
    if (!vagas || !partidos) return null;
    const validos = Object.values(partidos).reduce((t, p) => t + p.total, 0);
    const bruto = validos / vagas;
    const QE = bruto - Math.floor(bruto) > 0.5 ? Math.ceil(bruto) : Math.floor(bruto);
    const cands = cargo.candidatos;
    const P = Object.entries(partidos).map(([sigla, p]) => ({
      sigla, total: p.total, nominais: p.nominais, legenda: p.legenda, qp: p.total / QE,
      lista: cands.filter((x) => x.partido === sigla).sort((a, b) => b.votos - a.votos), qpCad: 0, medCad: 0, eleitos: [],
    })).sort((a, b) => b.total - a.total);
    const coligacoes = +ano < 2020;
    const res = { ano: +ano, vagas, validos, QE, partidos: P, coligacoes, simulado: !coligacoes };
    if (coligacoes) return res;
    const minQP = 0.1 * QE, minSobra2 = +ano >= 2022 ? 0.2 * QE : 0.1 * QE, minPart2 = +ano >= 2022 ? 0.8 * QE : 0;
    const prox = (p, min) => p.lista.find((x) => !p.eleitos.includes(x) && x.votos >= min);
    let livres = vagas;
    for (const p of P) {
      for (let i = 0; i < Math.floor(p.qp) && livres > 0; i++) { const x = prox(p, minQP); if (!x) break; p.eleitos.push(x); p.qpCad++; livres--; }
    }
    const sobra = (filtroPart, min) => {
      while (livres > 0) {
        let best = null, bm = -1;
        for (const p of P) {
          if (!filtroPart(p) || !prox(p, min)) continue;
          const m = p.total / (p.eleitos.length + 1);
          if (m > bm) { bm = m; best = p; }
        }
        if (!best) break;
        best.eleitos.push(prox(best, min)); best.medCad++; livres--;
      }
    };
    sobra((p) => p.total >= minPart2, minSobra2);
    if (+ano >= 2022) sobra(() => true, 0);
    res.sobrou = livres;
    return res;
  }
  // Eleitos com menos votos do que alguém que ficou de fora: o voto do partido/coligação os "puxou".
  function puxados(cargo) {
    const c = cargo.candidatos;
    const eleito = (x) => (x.situacao || "").startsWith("eleito");
    const fora = c.filter((x) => !eleito(x));
    const melhorFora = fora[0];
    return c.filter(eleito).filter((x) => melhorFora && x.votos < melhorFora.votos).map((x) => ({
      x, acima: fora.filter((y) => y.votos > x.votos),
      puxador: c.filter((y) => y.partido === x.partido).sort((a, b) => b.votos - a.votos)[0],
    }));
  }
  raiz.PlenariaQuociente = { quociente, puxados };
})(typeof window !== "undefined" ? window : globalThis);
