#!/usr/bin/env python3
"""Raio-X financeiro detalhado de uma prefeitura (Siconfi/DCA): receitas, despesas por tipo e por área, ano a ano,
com variação anual. Junta os contratos do TCE-CE (data/financas/<slug>.contratos.json) por categoria.
Uso: python3 scripts/raiox_financas.py --ibge 2313955 --nome Varjota  → data/financas/<slug>.detalhe.json + entregas/<slug>-financas.html"""
import argparse, collections, html, json, re, unicodedata, urllib.parse, urllib.request
API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
def get(r, **q): return json.load(urllib.request.urlopen(f"{API}/{r}?" + urllib.parse.urlencode(q), timeout=180))["items"]
norm = lambda s: unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
ap = argparse.ArgumentParser(); ap.add_argument("--ibge", required=True); ap.add_argument("--nome", required=True); ap.add_argument("--de", type=int, default=2016); ap.add_argument("--ate", type=int, default=2025)
a = ap.parse_args(); slug = norm(a.nome).replace(" ", "-")
REC = [("Receita corrente", r"^receitas correntes$"), ("FPM", r"fundo de participacao dos municipios|cota-parte do fpm"), ("ICMS (cota-parte)", r"cota-parte do icms|cota-parte do imposto sobre operacoes"),
       ("IPTU", r"propriedade predial e territorial urbana"), ("ISS", r"^impostos sobre servicos|imposto sobre servicos de qualquer natureza"), ("ITBI", r"transmissao .?inter vivos"),
       ("Transferências do SUS", r"sistema unico de saude|\bsus\b"), ("Receita de capital (convênios, operações)", r"^receitas de capital$")]
DESP = [("Despesa total", r"^3|^4", None), ("Pessoal e encargos", "3.1.00", None), ("Contratação temporária", "3.1.90.04", None), ("Material de consumo", "3.3.90.30", None),
        ("Consultoria", "3.3.90.35", None), ("Serviços de terceiros — pessoa física", "3.3.90.36", None), ("Serviços de terceiros — empresas", "3.3.90.39", None),
        ("Terceirização de mão de obra", "3.3.90.34", None), ("Tecnologia da informação", "3.3.90.40", None), ("Diárias", "3.3.90.14", None),
        ("Obras e instalações", "4.4.90.51", None), ("Equipamentos e material permanente", "4.4.90.52", None), ("Pagamento de dívida", "4.6.00", None),
        ("Sentenças judiciais (precatórios)", "3.1.90.91", None), ("Consórcios públicos", "3.3.71", None)]
dados = {}
for ano in range(a.de, a.ate + 1):
    r = get("dca", an_exercicio=ano, no_anexo="DCA-Anexo I-C", id_ente=a.ibge); dd = get("dca", an_exercicio=ano, no_anexo="DCA-Anexo I-D", id_ente=a.ibge); fu = get("dca", an_exercicio=ano, no_anexo="DCA-Anexo I-E", id_ente=a.ibge)
    if not r: continue
    colr = "Receitas Brutas Realizadas" if any(x["coluna"] == "Receitas Brutas Realizadas" for x in r) else r[0]["coluna"]
    rr = [x for x in r if x["coluna"] == colr]; L = {}
    for nome, pad in REC:
        v = next((x["valor"] for x in rr if re.search(pad, norm(re.sub(r"^[\d.]+ ?- ?", "", x["conta"])))), None); L[nome] = v
    fb = [x for x in rr if "fundeb" in norm(x["conta"])]  # FUNDEB = soma das linhas de nível mais alto (estado + complementação da União)
    if fb:
        prof = lambda x: len([s for s in x["cod_conta"][2:].split(".") if s.strip("0")])
        m = min(prof(x) for x in fb); L["FUNDEB (estado + complementação da União)"] = sum(x["valor"] for x in fb if prof(x) == m)
    emp = [x for x in dd if x["coluna"] == "Despesas Empenhadas"]
    for nome, cod, _ in DESP:
        if nome == "Despesa total": L[nome] = sum(x["valor"] for x in emp if re.match(r"^\d\.0\.00\.00\.00", x["conta"]) and x["conta"][0] in "34"); continue
        L[nome] = sum(x["valor"] for x in emp if x["conta"].startswith(cod + ".00" if cod.count(".") == 2 and len(cod) == 7 else cod) and re.match(r"^[\d.]+ ", x["conta"]) and x["conta"].split(" ")[0] in (cod + ".00.00", cod + ".00", cod + ".00.00.00")) or None
    for x in fu:
        if x["coluna"] == "Despesas Empenhadas" and re.match(r"^\d{2} - ", x["conta"]): L["Área: " + x["conta"][5:].strip()] = x["valor"]
    dados[ano] = L; print(ano, "ok", flush=True)
# contratos do TCE por categoria (só contratos originais, sem aditivos)
CAT = [("Festas, shows e eventos", r"show|festa|evento|carnaval|banda|palco|som e ilumina|reveillon|festiv|atracao musical"), ("Consultoria, assessoria, jurídico e contábil", r"consultori|assessori|servicos juridicos|advocac|advogad|contabilidade|auditoria\b"),
       ("Saúde", r"saude|hospital|medic|odonto|exame|laborator|organizacao social|o\.s\.|ubs|farmac"), ("Obras, reformas e pavimentação", r"obra|pavimenta|reforma|constru|amplia|engenharia|calcament|drenag"),
       ("Educação, merenda e transporte escolar", r"escola|ensino|merenda|aliment.*escolar|pnae|educa|creche|transporte escolar"), ("Combustível e veículos", r"combust|gasolina|diesel|locacao de veiculo|pecas|pneu|veicul"),
       ("Limpeza e coleta de lixo", r"limpeza|lixo|residuo|coleta"), ("Publicidade e comunicação", r"publicidade|propaganda|divulgac|comunicacao|marketing")]
try: C = json.load(open(f"data/financas/{slug}.contratos.json"))["contratos"]
except FileNotFoundError: C = []
vistos, cont = set(), collections.defaultdict(lambda: collections.defaultdict(float)); top = collections.defaultdict(list)
for x in C:
    k = (x["numero"], x["data"], x["valor"], x["objeto"][:40])
    if x["modalidade"] != "OR" or k in vistos or not x["valor"]: continue
    vistos.add(k); o = norm(x["objeto"]); ano = int(x["data"][:4])
    for nome, p in CAT:
        if re.search(p, o): cont[nome][ano] += x["valor"]; top[nome].append(x); break
json.dump({"municipio": a.nome, "siconfi": dados, "contratos_categoria": {k: dict(v) for k, v in cont.items()}}, open(f"data/financas/{slug}.detalhe.json", "w"), ensure_ascii=False, indent=1)

# ---------- relatório HTML (abre no celular)
anos = sorted(dados); f = lambda v: "—" if v in (None, 0) else f"{v/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def var(v0, v1):
    if not v0 or not v1: return ""
    p = (v1 / v0 - 1) * 100; c = "#0a7d32" if p >= 0 else "#c0262d"; return f'<small style="color:{c}">{"▲" if p >= 0 else "▼"}{abs(p):.0f}%</small>'
def tabela(titulo, linhas, fonte):
    h = f"<h2>{html.escape(titulo)}</h2><div class=t><table><tr><th>R$ milhões</th>" + "".join(f"<th>{y}</th>" for y in anos) + "<th>2016→" + str(anos[-1]) + "</th></tr>"
    for n in linhas:
        vs = [dados[y].get(n) for y in anos]
        h += f"<tr><td>{html.escape(n.replace('Área: ', ''))}</td>" + "".join(f"<td>{f(v)}<br>{var(vs[i-1], v) if i else ''}</td>" for i, v in enumerate(vs)) + f"<td><b>{var(next((v for v in vs if v), None), vs[-1])}</b></td></tr>"
    return h + f"</table></div><p class=f>{fonte}</p>"
areas = sorted({k for y in anos for k in dados[y] if k.startswith("Área: ")}, key=lambda k: -(dados[anos[-1]].get(k) or 0))[:10]
cy = sorted({y for v in cont.values() for y in v})
hc = "<h2>Contratos assinados por tipo (só contratos novos, sem aditivos)</h2><div class=t><table><tr><th>R$ milhões</th>" + "".join(f"<th>{y}</th>" for y in cy) + "</tr>"
for nome, _ in CAT:
    vs = [cont[nome].get(y) for y in cy]; hc += f"<tr><td>{nome}</td>" + "".join(f"<td>{f(v)}<br>{var(vs[i-1], v) if i else ''}</td>" for i, v in enumerate(vs)) + "</tr>"
hc += "</table></div><p class=f>Fonte: TCE-CE, dados abertos. Valor do contrato = teto contratado, não o pago. Categoria definida por palavras do objeto (ordem de grandeza).</p>"
for nome in ("Festas, shows e eventos", "Consultoria, assessoria, jurídico e contábil"):
    hc += f"<h3>Maiores contratos — {nome}</h3><ul>" + "".join(f"<li>{x['data'][:10]} · <b>R$ {x['valor']:,.0f}</b> · {html.escape(x['objeto'][:140])} <small>({html.escape(x['processo'] or '')})</small></li>".replace(",", ".") for x in sorted(top[nome], key=lambda x: -x["valor"])[:8]) + "</ul>"
doc = f"""<!doctype html><html lang=pt-BR><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Raio-X financeiro — {a.nome}</title>
<style>body{{font:15px/1.4 system-ui,sans-serif;margin:16px;color:#111;background:#fff}}h1{{font-size:22px}}h2{{font-size:18px;margin-top:28px;border-left:6px solid #1f3fae;padding-left:8px}}
.t{{overflow-x:auto}}table{{border-collapse:collapse;font-size:13px;min-width:900px}}td,th{{border-bottom:1px solid #ddd;padding:5px 7px;text-align:right;white-space:nowrap}}td:first-child,th:first-child{{text-align:left;position:sticky;left:0;background:#fff;white-space:normal;min-width:170px}}
th{{background:#1f3fae;color:#fff}}th:first-child{{background:#1f3fae}}.f{{font-size:12px;color:#666}}li{{margin:6px 0}}</style>
<h1>Raio-X financeiro da Prefeitura de {a.nome} ({anos[0]}–{anos[-1]})</h1><p class=f>Valores nominais (sem correção da inflação). Despesa = empenhada. ▲▼ = variação em relação ao ano anterior. Fontes: Tesouro Nacional (Siconfi, DCA) e TCE-CE.</p>
{tabela("Quanto entra", [n for n, _ in REC] + ["FUNDEB (estado + complementação da União)"], "Fonte: Siconfi, DCA Anexo I-C (receitas brutas realizadas).")}
{tabela("Quanto sai — por tipo de gasto", [n for n, _, _ in DESP], "Fonte: Siconfi, DCA Anexo I-D (despesas empenhadas, por elemento).")}
{tabela("Quanto sai — por área", areas, "Fonte: Siconfi, DCA Anexo I-E (despesas empenhadas por função).")}
{hc}</html>"""
open(f"entregas/{slug}-financas.html", "w").write(doc); print("✔", f"entregas/{slug}-financas.html")
