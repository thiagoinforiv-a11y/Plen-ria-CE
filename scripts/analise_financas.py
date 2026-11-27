#!/usr/bin/env python3
"""Análise de 10 anos (valores corrigidos pela inflação) a partir de data/financas/<slug>.detalhe.json.
Uso: python3 scripts/analise_financas.py --nome Varjota  → entregas/<slug>-analise-10-anos.html
IPCA anual (IBGE); 2025 estimado em 4,5% — atualizar quando o número oficial for consultado."""
import argparse, html, json, unicodedata
ap = argparse.ArgumentParser(); ap.add_argument("--nome", required=True); a = ap.parse_args()
slug = unicodedata.normalize("NFD", a.nome).encode("ascii", "ignore").decode().lower().replace(" ", "-")
D = json.load(open(f"data/financas/{slug}.detalhe.json")); S = D["siconfi"]; C = D["contratos_categoria"]
IPCA = {2016: 6.29, 2017: 2.95, 2018: 3.75, 2019: 4.31, 2020: 4.52, 2021: 10.06, 2022: 5.79, 2023: 4.62, 2024: 4.83, 2025: 4.5}
anos = sorted(int(y) for y in S); fim = anos[-1]
fat = {y: 1.0 for y in anos}
for y in anos:
    for b in range(y + 1, fim + 1): fat[y] *= 1 + IPCA[b] / 100
v = lambda k, y: (S[str(y)].get(k) or 0) / 1e6
r = lambda k, y: v(k, y) * fat[y]
MAND = [("Rosa Paulino", [2016]), ("Célia", [2017, 2018, 2019, 2020]), ("Elmo · 1º mandato", [2021, 2022, 2023, 2024]), ("Elmo · 2º mandato (só 2025)", [2025])]
media = lambda k, A: sum(r(k, y) for y in A if y in fat) / len([y for y in A if y in fat])
br = lambda x, d=1: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def barras(k, cor="#1f3fae", real=True):
    vs = [(y, r(k, y) if real else v(k, y)) for y in anos]; mx = max(x for _, x in vs) or 1; w = 34; h = 150
    s = f'<svg viewBox="0 0 {len(vs)*w+10} {h+40}" style="width:100%;max-width:560px">'
    for i, (y, x) in enumerate(vs):
        bh = x / mx * h; s += f'<rect x="{i*w+6}" y="{h-bh+14}" width="{w-10}" height="{bh}" fill="{cor}" rx="3"/><text x="{i*w+w/2+1}" y="{h-bh+10}" font-size="9" text-anchor="middle">{br(x)}</text><text x="{i*w+w/2+1}" y="{h+28}" font-size="9" text-anchor="middle" fill="#555">{str(y)[2:]}</text>'
    return s + "</svg>"
def tab_mand(chaves):
    t = "<div class=t><table><tr><th>Média por ano (R$ mi, corrigido)</th>" + "".join(f"<th>{m}</th>" for m, _ in MAND) + "</tr>"
    for k in chaves: t += f"<tr><td>{html.escape(k.replace('Área: ',''))}</td>" + "".join(f"<td>{br(media(k, A))}</td>" for _, A in MAND) + "</tr>"
    return t + "</table></div>"
rc = "Receita corrente"; fb = "FUNDEB (estado + complementação da União)"; tp = "Serviços de terceiros — empresas"
dep = {y: (v("FPM", y) + v("ICMS (cota-parte)", y) + v(fb, y) + v("Transferências do SUS", y)) / v(rc, y) * 100 for y in anos}
prop = {y: (v("IPTU", y) + v("ISS", y) + v("ITBI", y)) / v(rc, y) * 100 for y in anos}
fest = {y: (C.get("Festas, shows e eventos", {}).get(str(y), 0) / 1e6) * fat.get(y, 1) for y in anos}
x = lambda k: r(k, fim) / r(k, anos[0])
cresc_rc = r(rc, fim) - r(rc, anos[0]); parte = {k: (r(k, fim) - r(k, anos[0])) / cresc_rc * 100 for k in ("FPM", fb, "ICMS (cota-parte)", "Transferências do SUS")}
achados = [
    f"<b>A receita dobrou de verdade.</b> Mesmo descontando a inflação, a receita corrente foi de R$ {br(r(rc, anos[0]))} mi ({anos[0]}) para R$ {br(r(rc, fim))} mi ({fim}): <b>{br(x(rc),2)} vezes</b>. O salto começa em 2022.",
    f"<b>Quem pagou esse crescimento foi Brasília.</b> Do aumento real de R$ {br(cresc_rc)} mi na receita, o FUNDEB respondeu por {br(parte[fb],0)}%, o FPM por {br(parte['FPM'],0)}%, o SUS por {br(parte['Transferências do SUS'],0)}% e o ICMS por {br(parte['ICMS (cota-parte)'],0)}%. O novo FUNDEB (lei de 2020, com complementação maior da União a partir de 2021) é o principal motor: <b>{br(x(fb),2)} vezes</b> em termos reais.",
    f"<b>A cidade vive de repasse.</b> FPM, ICMS, FUNDEB e SUS somam <b>{br(dep[fim],0)}%</b> da receita em {fim}. Os impostos da própria cidade (IPTU, ISS, ITBI) são só <b>{br(prop[fim],1)}%</b>. O IPTU praticamente não mudou em 10 anos (R$ {br(r('IPTU', fim),2)} mi em {fim}).",
    f"<b>O gasto que mais cresceu foi com empresas contratadas</b> (serviços de terceiros — pessoa jurídica): <b>{br(x(tp),1)} vezes</b> em termos reais, de R$ {br(r(tp, anos[0]))} mi para R$ {br(r(tp, fim))} mi. Hoje é quase um terço da despesa. Pessoal cresceu menos ({br(x('Pessoal e encargos'),2)}×), e o peso da folha caiu de {br(v('Pessoal e encargos', anos[0])/v(rc, anos[0])*100,0)}% para {br(v('Pessoal e encargos', fim)/v(rc, fim)*100,0)}% da receita.",
    f"<b>Educação e saúde receberam a maior parte do dinheiro novo:</b> educação {br(x('Área: Educação'),1)}× e saúde {br(x('Área: Saúde'),1)}×. Assistência social quase não mudou ({br(x('Área: Assistência Social'),2)}×).",
    f"<b>Obras tiveram pico em 2024.</b> O gasto com obras ficou entre R$ 2 e 10 mi por ano e saltou para R$ {br(r('Obras e instalações', 2024))} mi em 2024, ano de eleição municipal, voltando a R$ {br(r('Obras e instalações', fim))} mi em {fim}.",
    f"<b>Festas e shows multiplicaram.</b> Em contratos assinados (TCE-CE), passaram de menos de R$ 1 mi por ano até 2021 para R$ {br(fest.get(2023,0),1)} mi (2023), R$ {br(fest.get(2024,0),1)} mi (2024) e R$ {br(fest.get(fim,0),1)} mi ({fim}), em valores corrigidos.",
    f"<b>As contas fecham no limite.</b> A despesa empenhada acompanha a receita quase real por real todo ano; em {fim} a sobra foi de R$ {br(v(rc, fim) - v('Despesa total', fim))} mi (sem contar receitas de capital).",
]
doc = f"""<!doctype html><html lang=pt-BR><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Raio-X 10 anos — {a.nome}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:16px;max-width:760px;color:#111;background:#fff}}h1{{font-size:24px;line-height:1.2}}h2{{font-size:19px;margin-top:30px;border-left:6px solid #1f3fae;padding-left:8px}}
li{{margin:10px 0}}.f{{font-size:12px;color:#666}}.t{{overflow-x:auto}}table{{border-collapse:collapse;font-size:13px}}td,th{{border-bottom:1px solid #ddd;padding:6px 8px;text-align:right}}td:first-child,th:first-child{{text-align:left}}th{{background:#1f3fae;color:#fff}}
.g{{margin:6px 0 18px}}.g b{{display:block;font-size:14px}}</style>
<h1>Raio-X dos recursos da Prefeitura de {a.nome}: 10 anos ({anos[0]}–{fim})</h1>
<p class=f>Valores corrigidos pela inflação (IPCA) para preços de {fim}, salvo indicação. IPCA de 2025 estimado em 4,5%. Fontes: Tesouro Nacional (Siconfi/DCA) e TCE-CE (contratos).</p>
<h2>O que os números dizem</h2><ol>{"".join(f"<li>{t}</li>" for t in achados)}</ol>
<h2>Gráficos (R$ milhões, corrigidos)</h2>
<div class=g><b>Receita corrente</b>{barras(rc)}</div><div class=g><b>FPM</b>{barras('FPM')}</div><div class=g><b>FUNDEB (estado + União)</b>{barras(fb,'#0a7d32')}</div>
<div class=g><b>Serviços de terceiros — empresas</b>{barras(tp,'#c0262d')}</div><div class=g><b>Pessoal e encargos</b>{barras('Pessoal e encargos','#555')}</div><div class=g><b>Obras e instalações</b>{barras('Obras e instalações','#b8860b')}</div>
<h2>Comparação por mandato</h2>{tab_mand([rc,'FPM',fb,'Pessoal e encargos',tp,'Obras e instalações','Área: Saúde','Área: Educação','Área: Assistência Social'])}
<p class=f>Atenção: boa parte da diferença entre mandatos vem de mudanças federais (novo FUNDEB, aumento do FPM), não só da gestão local. 2016 foi o último ano de Rosa Paulino; 2025 é o primeiro ano do 2º mandato de Elmo.</p>
<h2>Dependência de repasses</h2><div class=t><table><tr><th>Ano</th>{"".join(f"<th>{y}</th>" for y in anos)}</tr><tr><td>FPM+ICMS+FUNDEB+SUS / receita</td>{"".join(f"<td>{br(dep[y],0)}%</td>" for y in anos)}</tr><tr><td>IPTU+ISS+ITBI / receita</td>{"".join(f"<td>{br(prop[y],1)}%</td>" for y in anos)}</tr></table></div>
<h2>Cuidados</h2><ul><li>Despesa = empenhada (compromisso assumido), não necessariamente paga.</li><li>Contratos do TCE-CE = valor máximo contratado; categoria por palavras do objeto (ordem de grandeza).</li><li>Números de 2026 ainda parciais e fora desta comparação anual.</li></ul></html>"""
open(f"entregas/{slug}-analise-10-anos.html", "w").write(doc); print("✔", f"entregas/{slug}-analise-10-anos.html")
for t in achados: print("-", html.unescape(t.replace("<b>", "").replace("</b>", "")))
