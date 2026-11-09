#!/usr/bin/env python3
"""Estudo de gastos de uma Câmara ou Prefeitura do Ceará, com pontos de atenção (ataque × defesa).

Uso:
  python3 scripts/gastos/estudo.py --cidade Varjota --orgao camara --de 2025 --ate 2026
  python3 scripts/gastos/estudo.py --cidade "Santa Quitéria" --orgao prefeitura --de 2025 --ate 2026
Saída (fora do git): entregas/estudos/<cidade>-<orgao>-<de>-<ate>.xlsx e o .json bruto (reaproveitado com --cache).
Fontes: PNCP, TCE-CE (dados abertos) e Tesouro Nacional (Siconfi, via scripts/financas.py). Ver scripts/gastos/README.md."""
import argparse, collections, json, os, re, subprocess, sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
sys.path.insert(0, os.path.dirname(__file__))
import alertas, coleta

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATS = [("Combustível", r"combust|gasolin|diesel|etanol"), ("Locação de veículos e máquinas", r"loca[çc][ãa]o de (ve[ií]cul|m[áa]quin|caminh|[ôo]nibus|carro|moto)|caminh[ãa]o pipa"),
 ("Transporte escolar", r"transporte escolar"), ("Obras e engenharia", r"obra|constru[çc]|reforma|pavimenta|engenharia|amplia[çc][ãa]o|drenagem|passagem molhada|cal[çc]ament|usina|fotovolt"),
 ("Medicamentos e saúde", r"medicament|hospital|odontol|laborat|exame|sa[úu]de|farm[áa]c|enfermag"), ("Merenda e alimentação", r"merenda|aliment|g[êe]neros|refei[çc]|lanche|quentinha|hortifrut"),
 ("Shows, festas e eventos", r"show|festa|evento|banda|carnaval|r[ée]veillon|palco|sonoriza|buffet|decora|galeria de fotos"), ("Material de limpeza", r"limpeza|higien|descart"),
 ("Material de expediente", r"expediente|papelaria"), ("Material permanente (móveis/equipamentos)", r"permanente|m[óo]veis|mobili|equipamento|eletrodom|ar condicion|refrigera"),
 ("Peças e manutenção de veículos", r"pe[çc]as|pneu|frota|oficina"), ("Coleta de lixo e limpeza urbana", r"lixo|res[ií]duo|limpeza urbana|varri[çc]"),
 ("Jurídico / advocacia", r"jur[ií]dic|advoc|lei org"), ("Assessoria e consultoria", r"assessor|consult|contab|auditoria|plano|transpar[êe]ncia|escritura|demonstrativ|pca|controle (intern|extern)|ouvidoria|governan|balc[ãa]o|procon"),
 ("Sistemas, internet e TI", r"software|sistema|licen[çc]a de uso|internet|link|inform[áa]tica|site"), ("Comunicação e publicidade", r"comunica|publicidad|imprensa|divulga|marketing|filmagem|transmiss"),
 ("Viagens e hospedagem", r"viage|passage|hosped"), ("Serviços gerais e mão de obra", r"m[ãa]o de obra|terceiriza|servi[çc]os gerais|vigil[âa]ncia|portaria")]
def cat(o):
    for k, r in CATS:
        if re.search(r, (o or "").lower()): return k
    return "Outros"
BR = alertas.BR

def financas(nome, ibge, de):
    arq = os.path.join(RAIZ, "data", "financas", coleta.slug(nome) + ".json")
    if not os.path.exists(arq):
        subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "financas.py"), "--ibge", ibge, "--nome", nome, "--de", str(de - 1), "--ate", "2026"], cwd=RAIZ, check=False)
    return json.load(open(arq))["anos"] if os.path.exists(arq) else {}

def indice_outros(pasta, proprio):
    """Fornecedores (CNPJ) de outros estudos já feitos nesta pasta: {cnpj: ['Câmara de X: objeto (valor)']}."""
    arq = os.path.join(pasta, "fornecedores.json"); I = json.load(open(arq)) if os.path.exists(arq) else {}
    return {cn: [o for o in v if not o.startswith(proprio + ":")] for cn, v in I.items() if any(not o.startswith(proprio + ":") for o in v)}, I, arq

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cidade", required=True); ap.add_argument("--orgao", choices=["camara", "prefeitura"], required=True)
    ap.add_argument("--de", type=int, default=2025); ap.add_argument("--ate", type=int, default=2026); ap.add_argument("--saida", default=os.path.join(RAIZ, "entregas", "estudos"))
    ap.add_argument("--cache", action="store_true", help="reaproveita o .json bruto já baixado"); a = ap.parse_args()
    anos = list(range(a.de, a.ate + 1)); os.makedirs(a.saida, exist_ok=True)
    nome_org = ("Câmara de " if a.orgao == "camara" else "Prefeitura de ") + a.cidade
    base = os.path.join(a.saida, f"{coleta.slug(a.cidade)}-{a.orgao}-{a.de}-{a.ate}")
    cod, ibge = coleta.municipio_tce(a.cidade); print(nome_org, "· TCE", cod, "· IBGE", ibge, flush=True)
    if a.cache and os.path.exists(base + ".json"): D = json.load(open(base + ".json"))
    else:
        cam, pref = coleta.orgaos(cod, a.ate)
        cnpjs = cam if a.orgao == "camara" else pref
        print("  CNPJs:", cnpjs, flush=True)
        D = coleta.pncp(cnpjs, anos)
        semres = sum(1 for x in D["contratacoes"] if not x.get("valorTotalHomologado"))
        D["tce"] = coleta.tce_contratos(cod, anos, filtro_camara=(a.orgao == "camara")) if (a.orgao == "camara" or not D["contratacoes"] or semres / len(D["contratacoes"]) >= 0.3) else []
        json.dump(D, open(base + ".json", "w"), ensure_ascii=False)
    F = financas(a.cidade, ibge, a.de)
    # processos e itens
    comp, ri = [], []
    for x in sorted(D["contratacoes"], key=lambda x: x["dataPublicacaoPncp"]):
        k = x["numeroControlePNCP"]; fl = collections.OrderedDict()
        for i in D["itens"].get(k, []):
            for r in i["resultados"]:
                key = (r["fornecedor"], (r.get("ni") or "").lstrip("0")); fl[key] = fl.get(key, 0) + (r["v_total"] or 0)
        c = dict(org=x["_org"], ano=x["anoCompra"], pub=x["dataPublicacaoPncp"][:10], mod=x["modalidadeNome"], cat=cat(x["objetoCompra"]), obj=(x["objetoCompra"] or "").strip(),
                 est=x.get("valorTotalEstimado"), hom=x.get("valorTotalHomologado"), sit=x.get("situacaoCompraNome"), k=k, forn_list=[(n, cn, v) for (n, cn), v in fl.items()],
                 link=f"https://pncp.gov.br/app/editais/{x['orgaoEntidade']['cnpj']}/{x['anoCompra']}/{x['sequencialCompra']}")
        comp.append(c)
        for i in D["itens"].get(k, []):
            for r in (i["resultados"] or [{"fornecedor": "[sem resultado]", "ni": "", "v_unit": None, "v_total": None, "qtd": None}]):
                ri.append(dict(org=c["org"], ano=c["ano"], cat=c["cat"], item=(i["descricao"] or "").strip(), qtd=r.get("qtd") or i["qtd"], unid=i["unid"], fornecedor=r["fornecedor"], cnpj=(r.get("ni") or "").lstrip("0"),
                               v_unit=r["v_unit"], v_total=r["v_total"], v_est=i["v_unit_est"], k=k, link=c["link"]))
    tce = D.get("tce") or []
    rep = None
    if a.orgao == "camara" and F:
        ys = sorted(y for y in F if (F[y].get("funcoes") or {}).get("Legislativa"))
        if len(ys) >= 2: rep = (ys[-2], F[ys[-2]]["funcoes"]["Legislativa"], ys[-1], F[ys[-1]]["funcoes"]["Legislativa"])
    outros, IDX, arq_idx = indice_outros(a.saida, nome_org)
    cp = [dict(fornecedor=x["nomeRazaoSocialFornecedor"], cnpj=(x.get("niFornecedor") or "").lstrip("0"), valor=x.get("valorGlobal"), objeto=x.get("objetoContrato"), data=x.get("dataAssinatura")) for x in D["contratos"]]
    if a.cache and "tce" not in D: D["tce"] = []
    AL = alertas.gerar(comp, ri, tce, rep, outros, cp)
    # índice de fornecedores para cruzar com os próximos estudos
    for k in list(IDX):
        IDX[k] = [o for o in IDX[k] if not o.startswith(nome_org + ":")]
    for c in comp:
        for n, cn, v in c["forn_list"]:
            if cn: IDX.setdefault(cn, []).append(f"{nome_org}: {n} — {c['obj'][:70]} ({BR(v or 0)})")
    for x in cp:
        if x["cnpj"]: IDX.setdefault(x["cnpj"], []).append(f"{nome_org}: {x['fornecedor']} — {(x['objeto'] or '')[:70]} ({BR(x['valor'] or 0)})")
    for c in tce:
        if c["cnpj"] and not c["aditivo"]: IDX.setdefault(c["cnpj"], []).append(f"{nome_org}: {c['fornecedor']} — {c['objeto'][:70]} ({BR(c['valor'] or 0)})")
    json.dump({k: v for k, v in IDX.items() if v}, open(arq_idx, "w"), ensure_ascii=False, indent=0)
    planilha(base + ".xlsx", nome_org, anos, comp, ri, tce, F, AL, a.orgao)
    exportar(base + ".painel.json", nome_org, anos, comp, ri, tce, F, AL, a.orgao)
    print(f"✔ {base}.xlsx · {len(comp)} processos · {len(ri)} itens · {len(tce)} contratos TCE · {len(AL)} alertas", flush=True)
    for x in AL[:12]: print(f"  [{x['gravidade']}] {x['tipo']}: {x['fato'][:150]}")

def exportar(arq, nome_org, anos, comp, ri, tce, F, AL, orgao):
    """Dados prontos para o painel (uma linha por processo, item e alerta, com o órgão)."""
    P = [dict(orgao=nome_org, processo=c["k"], ano=c["ano"], publicado=c["pub"], modalidade="Pregão" if "Preg" in c["mod"] else c["mod"].split(" - ")[0], categoria=c["cat"], objeto=c["obj"][:300],
              estimado=c["est"], contratado=c["hom"], fornecedor="; ".join(n for n, cn, v in c["forn_list"]) or "Sem resultado publicado", cnpj=";".join(cn for n, cn, v in c["forn_list"] if cn), link=c["link"]) for c in comp]
    semres = sum(1 for c in comp if not c["hom"]) / len(comp) if comp else 1
    if not comp or semres >= 0.3:  # sem resultado no PNCP: entram os contratos do TCE-CE
        P += [dict(orgao=nome_org, processo=f"TCE-{i}-{c['data']}", ano=int(c["data"][:4]), publicado=c["data"], modalidade="Contrato (TCE-CE)", categoria=cat(c["objeto"]), objeto=c["objeto"][:300],
                   estimado=None, contratado=c["valor"], fornecedor=c["fornecedor"], cnpj=c["cnpj"], link="") for i, c in enumerate(tce) if not c["aditivo"]]
    I = [dict(id=f"{r['k']}#{n}", orgao=nome_org, ano=r["ano"], categoria=r["cat"], item=r["item"][:220], qtd=r["qtd"], unid=r["unid"], fornecedor=r["fornecedor"], preco_unit=r["v_unit"], total=r["v_total"],
              preco_est=r["v_est"], processo=r["k"], link=r["link"]) for n, r in enumerate(ri)]
    A = [dict(id=f"{nome_org}#{n}", orgao=nome_org, **{k: (v if not isinstance(v, str) else v[:900]) for k, v in x.items()}) for n, x in enumerate(AL)]
    E = []
    for y in [str(anos[0] - 1)] + [str(y) for y in anos]:
        a = F.get(y) or {}
        v = (a.get("funcoes") or {}).get("Legislativa") if orgao == "camara" else a.get("receita_corrente")
        if v: E.append(dict(orgao=nome_org, ano=int(y), valor=v, indicador="Repasse da Prefeitura" if orgao == "camara" else "Receita corrente", fonte=a.get("fonte", "DCA")))
    json.dump(dict(processos=P, itens=I, alertas=A, entradas=E), open(arq, "w"), ensure_ascii=False)

def planilha(arq, nome_org, anos, comp, ri, tce, F, AL, orgao):
    wb = Workbook(); H = Font(bold=True, color="FFFFFF"); FL = PatternFill("solid", fgColor="1F3FAE"); M = '"R$" #,##0.00'
    COR = {"Alta": "F8D7DA", "Média": "FFF3CD", "Baixa": "E2E8F0"}
    def aba(ws, cab, rows, larg, money=(), pct=()):
        ws.append(cab)
        for c in ws[1]: c.font = H; c.fill = FL; c.alignment = Alignment(wrap_text=True, vertical="top")
        for r in rows: ws.append(r)
        for i, w in enumerate(larg, 1):
            L = ws.cell(1, i).column_letter; ws.column_dimensions[L].width = w
            for c in ws[L][1:]:
                c.alignment = Alignment(wrap_text=True, vertical="top")
                if i in money: c.number_format = M
                if i in pct: c.number_format = "0.0%"
        ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    ws = wb.active; ws.title = "Pontos de atenção"
    aba(ws, ["Gravidade", "Ponto", "O fato (números)", "Valor envolvido", "Por que chama atenção", "Linha de ataque (a pergunta)", "Defesa provável do gestor", "O que pedir (Lei de Acesso)", "Base legal", "Referência", "Link"],
        [[x["gravidade"], x["tipo"], x["fato"], x["valor"], x["por_que"], x["ataque"], x["defesa"], x["pedir"], x["base"], x["referencia"], x["link"]] for x in AL], [9, 22, 50, 14, 45, 45, 40, 45, 28, 22, 28], money=(4,))
    for r in ws.iter_rows(min_row=2):
        r[0].fill = PatternFill("solid", fgColor=COR.get(r[0].value, "FFFFFF"))
    n_sem = sum(1 for c in comp if re.search("Dispensa|Inexig", c["mod"])); tot = collections.Counter()
    for c in comp: tot[c["ano"]] += c["hom"] or 0
    res = [["Órgão", nome_org], ["Período", f"{anos[0]} a {anos[-1]} (até a data da coleta)"], ["Processos no PNCP", len(comp)], ["Sem licitação (dispensa/inexigibilidade)", n_sem],
           ["% sem licitação", (n_sem / len(comp)) if comp else None]] + [[f"Homologado no PNCP em {y}", v] for y, v in sorted(tot.items())]
    if tce: res += [["Contratos no TCE-CE (novos, sem aditivos)", sum(1 for c in tce if not c["aditivo"])], ["Valor desses contratos", sum(c["valor"] or 0 for c in tce if not c["aditivo"])]]
    for y in [str(anos[0] - 1)] + [str(y) for y in anos]:
        a = F.get(y)
        if not a: continue
        if orgao == "camara": res.append([f"Repasse à Câmara {y} (função Legislativa)", (a.get("funcoes") or {}).get("Legislativa") or "não publicado"])
        else: res += [[f"Receita corrente {y} ({a.get('fonte', '')})", a.get("receita_corrente")], [f"FPM {y}", a.get("fpm")], [f"Despesa empenhada {y}", a.get("despesa_empenhada")]]
    r2 = wb.create_sheet("Resumo"); aba(r2, ["Indicador", "Valor"], res, [52, 40])
    for r in r2.iter_rows(min_row=2):
        v = r[1].value
        if isinstance(v, float) and abs(v) <= 1: r[1].number_format = "0.0%"
        elif isinstance(v, (int, float)) and v > 1000: r[1].number_format = M
    r2["D1"] = "Fontes: PNCP, TCE-CE (dados abertos) e Tesouro Nacional (Siconfi). Alertas são indícios para pedir documentos, não conclusões."
    aba(wb.create_sheet("Licitações e dispensas"), ["Órgão", "Ano", "Publicado", "Modalidade", "Situação", "Categoria", "Objeto", "Estimado", "Contratado", "Quem ganhou", "Nº PNCP", "Link"],
        [[c["org"], c["ano"], c["pub"], c["mod"], c["sit"], c["cat"], c["obj"], c["est"], c["hom"], "; ".join(f"{n} ({BR(v)})" for n, cn, v in c["forn_list"]) or "[sem resultado publicado]", c["k"], c["link"]] for c in comp],
        [14, 6, 11, 16, 14, 22, 60, 14, 14, 50, 26, 30], money=(8, 9))
    if tce:
        aba(wb.create_sheet("Contratos TCE-CE"), ["Data", "Aditivo?", "Fornecedor", "CNPJ", "Categoria", "Objeto", "Valor", "Vigência até", "Processo"],
            [[c["data"], "sim" if c["aditivo"] else "", c["fornecedor"], c["cnpj"], cat(c["objeto"]), c["objeto"], c["valor"], c["fim"], c["processo"]] for c in sorted(tce, key=lambda c: c["data"])], [11, 8, 36, 16, 22, 70, 14, 12, 18], money=(7,))
    linhas = [[r["org"], r["ano"], r["cat"], r["item"], r["qtd"], r["unid"], r["fornecedor"], r["v_unit"], r["v_total"], r["v_est"], (r["v_unit"] / r["v_est"] - 1) if r["v_unit"] and r["v_est"] else None, r["k"], r["link"]] for r in ri]
    cab = ["Órgão", "Ano", "Categoria", "Item", "Qtd", "Unid.", "Fornecedor", "Preço unit. pago", "Total", "Preço unit. estimado", "Pago × estimado", "Processo", "Link"]
    larg = [14, 6, 22, 60, 8, 8, 34, 14, 14, 14, 10, 26, 30]
    aba(wb.create_sheet("Itens comprados"), cab, linhas, larg, money=(8, 9, 10), pct=(11,))
    serv = re.compile(r"Assessoria|Jurídico|Comunicação|Viagens|Obras|Shows|Serviços gerais|Coleta|Transporte escolar|Locação|Sistemas")
    aba(wb.create_sheet("Produtos mais caros"), cab, sorted([l for l in linhas if l[7] and l[7] >= 500 and not serv.search(l[2])], key=lambda l: -l[7]), larg, money=(8, 9, 10), pct=(11,))
    pf = collections.defaultdict(lambda: [0.0, set(), set(), ""])
    for r in ri:
        if r["v_total"]: f = pf[r["fornecedor"]]; f[0] += r["v_total"]; f[1].add(r["cat"]); f[2].add(r["k"]); f[3] = r["cnpj"]
    tg = sum(v[0] for v in pf.values()) or 1
    aba(wb.create_sheet("Por fornecedor"), ["Fornecedor", "CNPJ/CPF", "Total", "% do total", "Nº de processos", "Categorias"],
        [[f, v[3], v[0], v[0] / tg, len(v[2]), ", ".join(sorted(v[1]))] for f, v in sorted(pf.items(), key=lambda z: -z[1][0])], [46, 16, 16, 10, 10, 60], money=(3,), pct=(4,))
    pc = collections.defaultdict(lambda: collections.defaultdict(float))
    for c in comp: pc[c["cat"]][c["ano"]] += c["hom"] or 0
    for c in tce:
        if not c["aditivo"] and not comp: pc[cat(c["objeto"])][int(c["data"][:4])] += c["valor"] or 0
    ys = sorted({y for v in pc.values() for y in v})
    aba(wb.create_sheet("Por categoria"), ["Categoria"] + [str(y) for y in ys] + ["Total"], [[k] + [v.get(y, 0) for y in ys] + [sum(v.values())] for k, v in sorted(pc.items(), key=lambda z: -sum(z[1].values()))],
        [44] + [16] * (len(ys) + 1), money=tuple(range(2, len(ys) + 3)))
    wb.save(arq)

if __name__ == "__main__": main()
