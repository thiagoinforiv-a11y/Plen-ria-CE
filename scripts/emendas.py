#!/usr/bin/env python3
"""Emendas parlamentares federais destinadas a um município (Portal da Transparência).

Uso: python3 scripts/emendas.py --municipio Varjota --uf CE [--pasta tse_raw]
Gera data/<uf>/<cidade>.emendas.js com o total empenhado e pago por autor e ano.
Roda na automação do GitHub (este ambiente não alcança o portal).
"""
import argparse
import csv
import io
import json
import os
import sys
import unicodedata
import urllib.request
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URLS = [
    "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO",
    "https://dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/emendas-parlamentares/EmendasParlamentares.zip",
]
csv.field_size_limit(1 << 30)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def valor(v):
    v = (v or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return 0.0


def col(r, *nomes):
    chaves = {norm(k): k for k in r}
    for n in nomes:
        k = chaves.get(norm(n))
        if k is not None:
            return r[k]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--municipio", required=True)
    ap.add_argument("--uf", default="CE")
    ap.add_argument("--pasta", default=os.path.join(RAIZ, "tse_raw"))
    a = ap.parse_args()
    os.makedirs(a.pasta, exist_ok=True)
    arq = os.path.join(a.pasta, "EmendasParlamentares.zip")
    if not os.path.exists(arq):
        for u in URLS:
            try:
                print("↓", u)
                req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (plenaria)"})
                with urllib.request.urlopen(req, timeout=600) as r, open(arq, "wb") as f:
                    f.write(r.read())
                if zipfile.is_zipfile(arq):
                    break
                os.remove(arq)
            except Exception as ex:
                print("  falhou:", ex)
    if not os.path.exists(arq):
        sys.exit("Não consegui baixar as emendas.")
    alvo = f"{norm(a.municipio)} - {a.uf.upper()}"
    autores = {}
    linhas = 0
    with zipfile.ZipFile(arq) as z:
        for n in z.namelist():
            if not n.lower().endswith(".csv"):
                continue
            with z.open(n) as bruto:
                for r in csv.DictReader(io.TextIOWrapper(bruto, encoding="latin-1", newline=""), delimiter=";"):
                    loc = norm(col(r, "Localidade do gasto", "Localidade de aplicação do recurso", "Município"))
                    if alvo not in loc and norm(a.municipio) != loc:
                        continue
                    linhas += 1
                    autor = (col(r, "Nome do Autor da Emenda", "Autor da emenda") or "?").strip()
                    ano = (col(r, "Ano da Emenda", "Ano") or "?").strip()
                    d = autores.setdefault(autor, {"autor": autor, "tipo": col(r, "Tipo de Emenda"), "anos": {}, "empenhado": 0, "pago": 0, "funcoes": {}})
                    e, p = valor(col(r, "Valor Empenhado")), valor(col(r, "Valor Pago")) + valor(col(r, "Valor Restos A Pagar Pagos", "Valor Restos a Pagar Pagos"))
                    y = d["anos"].setdefault(ano, {"empenhado": 0, "pago": 0})
                    y["empenhado"] += e; y["pago"] += p; d["empenhado"] += e; d["pago"] += p
                    fn = col(r, "Nome Função", "Função") or "?"
                    d["funcoes"][fn] = d["funcoes"].get(fn, 0) + p
    print(f"{linhas} linhas de emendas para {alvo}; {len(autores)} autores")
    saida = {"fonte": "Portal da Transparência (CGU) — emendas parlamentares; valores em R$", "municipio": a.municipio, "uf": a.uf.upper(),
             "autores": sorted(autores.values(), key=lambda d: -d["pago"])}
    slug = norm(a.municipio).lower().replace(" ", "-")
    p = os.path.join(RAIZ, "data", a.uf.lower(), f"{slug}.emendas.js")
    with open(p, "w", encoding="utf-8") as f:
        f.write("window.PLENARIA_EMENDAS = window.PLENARIA_EMENDAS || {};\n")
        f.write(f'window.PLENARIA_EMENDAS["{a.uf.lower()}/{slug}"] = ' + json.dumps(saida, ensure_ascii=False) + ";\n")
    print("✔", os.path.relpath(p, RAIZ))


if __name__ == "__main__":
    main()
