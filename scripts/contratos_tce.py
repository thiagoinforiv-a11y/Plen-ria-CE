#!/usr/bin/env python3
"""Contratos de uma prefeitura no TCE-CE (dados abertos), mês a mês. Uso: python3 scripts/contratos_tce.py --tce 177 --nome Varjota --de 2016 --ate 2026
Saída: data/financas/<slug>.contratos.json (CPFs vêm cifrados pelo TCE e são descartados)."""
import argparse, calendar, time, json, unicodedata, urllib.parse, urllib.request
B = "https://api-dados-abertos.tce.ce.gov.br/api/contratos"
ap = argparse.ArgumentParser(); ap.add_argument("--tce", required=True); ap.add_argument("--nome", required=True); ap.add_argument("--de", type=int, default=2016); ap.add_argument("--ate", type=int, default=2026)
a = ap.parse_args(); out = []
def busca(i, f):
    q = urllib.parse.urlencode({"codigo_municipio": a.tce, "data_inicio": i, "data_fim": f})
    for t in range(6):
        try: d = json.load(urllib.request.urlopen(f"{B}?{q}", timeout=300)); return d.get("elements", [])
        except Exception as e: time.sleep(3 * (t + 1)); err = e
    raise err
for ano in range(a.de, a.ate + 1):
    n0 = len(out)
    for m in range(1, 13):
        ult = calendar.monthrange(ano, m)[1]
        el = busca(f"{ano}{m:02d}01", f"{ano}{m:02d}{ult}")
        if len(el) >= 1000:  # mês cheio: divide em quinzenas
            el = busca(f"{ano}{m:02d}01", f"{ano}{m:02d}15") + busca(f"{ano}{m:02d}16", f"{ano}{m:02d}{ult}")
        for x in el:
            out.append({"data": (x.get("data_contrato") or "")[:10], "numero": x.get("numero_contrato"), "tipo": x.get("tipo_contrato"), "modalidade": x.get("modalide_contrato"),
                        "objeto": (x.get("descricao_objeto_contrato") or "").strip(), "valor": x.get("valor_total_contrato"), "processo": x.get("numero_processo_adm"),
                        "inicio": (x.get("data_inicio_vigencia_contrato") or "")[:10], "fim": (x.get("data_fim_vigencia_contrato") or "")[:10], "pncp": (x.get("numero_id_contrato_pncp") or "").strip()})
    print(ano, len(out) - n0, "contratos", round(sum((y["valor"] or 0) for y in out[n0:]) / 1e6, 2), "mi", flush=True)
slug = unicodedata.normalize("NFD", a.nome).encode("ascii", "ignore").decode().lower().replace(" ", "-")
json.dump({"municipio": a.nome, "fonte": "TCE-CE — dados abertos (contratos)", "contratos": out}, open(f"data/financas/{slug}.contratos.json", "w"), ensure_ascii=False)
