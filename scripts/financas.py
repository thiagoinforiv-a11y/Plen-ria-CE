#!/usr/bin/env python3
"""Receitas, despesas e FPM de uma prefeitura (Tesouro Nacional / Siconfi, DCA anual; 2026 parcial pelo RREO).
Uso: python3 scripts/financas.py --ibge 2313955 --nome Varjota --de 2016 --ate 2026  → data/financas/<slug>.json"""
import argparse, json, re, unicodedata, urllib.parse, urllib.request
API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
def get(rota, **q):
    url = f"{API}/{rota}?" + urllib.parse.urlencode(q); itens = []
    while url:
        d = json.load(urllib.request.urlopen(url, timeout=120)); itens += d.get("items", [])
        url = next((l["href"] for l in d.get("links", []) if l.get("rel") == "next"), None) if d.get("hasMore") else None
    return itens
norm = lambda s: unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
def soma(itens, coluna, *padroes, exato=False):
    for x in itens:
        if x["coluna"] != coluna: continue
        c = norm(x["conta"])
        if all(re.search(p, c) for p in padroes): return x["valor"]
    return None
ap = argparse.ArgumentParser(); ap.add_argument("--ibge", required=True); ap.add_argument("--nome", required=True); ap.add_argument("--de", type=int, default=2016); ap.add_argument("--ate", type=int, default=2026)
a = ap.parse_args(); anos = {}
for ano in range(a.de, a.ate + 1):
    r = get("dca", an_exercicio=ano, no_anexo="DCA-Anexo I-C", id_ente=a.ibge)
    if r:
        col = "Receitas Brutas Realizadas" if any(x["coluna"] == "Receitas Brutas Realizadas" for x in r) else r[0]["coluna"]
        dd = get("dca", an_exercicio=ano, no_anexo="DCA-Anexo I-D", id_ente=a.ibge)
        fu = get("dca", an_exercicio=ano, no_anexo="DCA-Anexo I-E", id_ente=a.ibge)
        pago = "Despesas Pagas"; emp = "Despesas Empenhadas"
        fun = {}
        for x in fu:
            if x["coluna"] == emp and re.match(r"^\d{2} - ", x["conta"]): fun[x["conta"][5:].strip()] = x["valor"]
        anos[ano] = {"fonte": "DCA (anual)", "receita_corrente": soma(r, col, r"^1\.0\.0\.0|receitas correntes$"),
            "fpm": soma(r, col, r"fundo de participacao dos municipios|fpm", r"cota") or soma(r, col, r"\bfpm\b"),
            "icms": soma(r, col, r"cota-parte do icms|cota-parte do imposto sobre operacoes"), "impostos_proprios": soma(r, col, r"^1\.1\.0\.0|impostos, taxas"),
                        "despesa_empenhada": soma(dd, emp, r"^despesas \(exceto|^total|despesas correntes") , "despesa_corrente": soma(dd, emp, r"despesas correntes"),
            "pessoal": soma(dd, emp, r"pessoal e encargos"), "investimentos": soma(dd, emp, r"^4\.4\.0|investimentos$"),
            "despesa_capital": soma(dd, emp, r"despesas de capital"), "funcoes": fun}
        print(ano, {k: v for k, v in anos[ano].items() if k != "funcoes"})
    else:  # ano corrente: RREO do último bimestre publicado (o maior bloco é o da prefeitura; o menor, o do RPPS)
        for bim in range(6, 0, -1):
            rr = get("rreo", an_exercicio=ano, nr_periodo=bim, co_tipo_demonstrativo="RREO", no_anexo="RREO-Anexo 01", id_ente=a.ibge)
            if not rr: continue
            mx = lambda col, pad: max([x["valor"] for x in rr if x["coluna"] == col and re.search(pad, norm(x["conta"]))] or [None])
            anos[ano] = {"fonte": f"RREO {bim}º bimestre (parcial, até {['','fev','abr','jun','ago','out','dez'][bim]})",
                         "receita_corrente": mx("Até o Bimestre (c)", r"^receitas correntes$"),
                         "despesa_empenhada": mx("DESPESAS EMPENHADAS ATÉ O BIMESTRE (f)", r"^total das despesas"),
                         "despesa_paga": mx("DESPESAS PAGAS ATÉ O BIMESTRE (j)", r"^total das despesas")}
            print(ano, anos[ano]); break
# FPM mês a mês (RREO Anexo 03, 4º bimestre = jan–ago) para comparar o mesmo período de cada ano
fpm_jan_ago = {}
for ano in range(max(a.de, 2018), a.ate + 1):
    rr = get("rreo", an_exercicio=ano, nr_periodo=4, co_tipo_demonstrativo="RREO", no_anexo="RREO-Anexo 03", id_ente=a.ibge)
    meses = {x["coluna"]: x["valor"] for x in rr if norm(x["conta"]).startswith("cota-parte do fpm")}
    if meses: fpm_jan_ago[ano] = round(sum(meses.get(f"<MR-{k}>" if k else "<MR>", 0) for k in range(8)), 2)
print("FPM jan-ago:", fpm_jan_ago)
slug = norm(a.nome).replace(" ", "-")
json.dump({"municipio": a.nome, "ibge": a.ibge, "fonte": "Tesouro Nacional — Siconfi (DCA e RREO)", "anos": anos, "fpm_jan_ago": fpm_jan_ago}, open(f"data/financas/{slug}.json", "w"), ensure_ascii=False, indent=1)
