"""Raio-X político de Varjota (parte 2): finanças (SICONFI/DCA), território (bairros),
vereadores 2020×2024 e redutos por bairro.

Uso: python3 raiox.py      (lê ../dados, grava ../dados/raiox.json e tabelas CSV)
"""
import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
D = BASE / "dados"
OUT = {}


def rd(n): return pd.read_csv(D / n, sep=";", low_memory=False)


# ------------------------------------------------------------- finanças (DCA)
fin = []
for a in range(2019, 2026):
    try:
        c = json.load(open(D / "siconfi" / f"dca_{a}_C.json"))["items"]
        dd = json.load(open(D / "siconfi" / f"dca_{a}_D.json"))["items"]
        e = json.load(open(D / "siconfi" / f"dca_{a}_E.json"))["items"]
    except FileNotFoundError:
        continue
    def val(items, prefix, col):
        for x in items:
            if x["conta"].startswith(prefix) and x["coluna"] == col:
                return float(x["valor"])
        return None
    rb = val(c, "RECEITAS (EXCETO", "Receitas Brutas Realizadas")
    ded = val(c, "RECEITAS (EXCETO", "Deduções - FUNDEB") or 0
    trib = val(c, "1.1.0.0.00.0.0", "Receitas Brutas Realizadas")
    transf = val(c, "1.7.0.0.00.0.0", "Receitas Brutas Realizadas")
    cap = val(c, "2.0.0.0.00.0.0", "Receitas Brutas Realizadas")
    emp = "Despesas Empenhadas"
    row = {"ano": a, "receita_liquida": round(rb - ded, 2) if rb else None, "receita_tributaria_propria": trib,
           "transferencias_correntes": transf, "receitas_capital": cap,
           "despesa_total": val(dd, "Total Geral da Despesa", emp), "pessoal": val(dd, "3.1.00.00.00", emp),
           "investimentos": val(dd, "4.4.00.00.00", emp)}
    for cod, nome in [("10 -", "saude"), ("12 -", "educacao"), ("15 -", "urbanismo"), ("08 -", "assistencia_social"),
                      ("20 -", "agricultura"), ("17 -", "saneamento"), ("04 -", "administracao"), ("01 -", "legislativa"),
                      ("26 -", "transporte"), ("27 -", "desporto_lazer"), ("13 -", "cultura")]:
        row[nome] = val(e, cod, emp)
    fin.append(row)
fin = pd.DataFrame(fin)
fin["pct_pessoal"] = (100 * fin.pessoal / fin.despesa_total).round(1)
fin["pct_invest"] = (100 * fin.investimentos / fin.despesa_total).round(1)
fin["pct_receita_propria"] = (100 * fin.receita_tributaria_propria / fin.receita_liquida).round(1)
fin.to_csv(D / "financas_dca_2019_2025.csv", index=False, sep=";")
OUT["financas"] = fin.round(2).to_dict("records")

# ------------------------------------------------------------- locais → bairros
loc = {}
for y in (2020, 2024):
    l = rd(f"locais_{y}.csv")
    l = l[l.CD_MUNICIPIO == 98574]
    if "NR_TURNO" in l: l = l[l.NR_TURNO == 1]
    g = l.groupby("NR_LOCAL_VOTACAO").agg(bairro=("NM_BAIRRO", "first"), lat=("NR_LATITUDE", "first"),
                                          lon=("NR_LONGITUDE", "first"), nome=("NM_LOCAL_VOTACAO", "first"),
                                          eleitores=("QT_ELEITOR_SECAO", "sum"))
    loc[y] = g
URB = {"CENTRO", "EMPRÉSTIMOS", "PEDREIRA", "ACAMPAMENTO DNOCS", "ACAMPAMENTO", "ARARINHA", "BALNEARIO", "BALNEÁRIO"}
def norm_b(b):
    b = str(b).upper().strip()
    if b in ("ACAMPAMENTO",): return "ACAMPAMENTO DNOCS"
    if b in ("ZONA RURAL",): return "VÁRZEA DA PALHA"
    if b == "BALNEARIO": return "BALNEÁRIO"
    if b.startswith("OLHO D"): return "OLHO D'ÁGUA DOS TRAJANOS"
    return b
def zona(b): return "Urbana (sede)" if b in {norm_b(x) for x in URB} else "Rural / distritos"

# ------------------------------------------------------------- votos por seção
sec = {}
for y in (2020, 2024):
    s = rd(f"votacao_secao_{y}_CE.csv")
    s = s[s.CD_MUNICIPIO == 98574]
    s["cargo"] = s.DS_CARGO.str.upper()
    lk = loc[y]
    # bairro do cadastro do ano; se faltar, o do cadastro de 2024; se ainda faltar, local extinto
    s["bairro"] = (s.NR_LOCAL_VOTACAO.map(lk.bairro).fillna(s.NR_LOCAL_VOTACAO.map(loc[2024].bairro))
                   .fillna("LOCAL EXTINTO EM 2024").map(norm_b))
    s["zona"] = s.bairro.map(zona)
    sec[y] = s

terr = {}
for y in (2020, 2024):
    s = sec[y]; p = s[(s.cargo == "PREFEITO") & ~s.NM_VOTAVEL.str.startswith("VOTO")]
    t = p.pivot_table(index="bairro", columns="NM_VOTAVEL", values="QT_VOTOS", aggfunc="sum", fill_value=0)
    el = [c for c in t.columns if "ELMO" in c][0]
    t["validos"] = t.drop(columns=[]).sum(axis=1)
    t["pct_elmo"] = (100 * t[el] / t.validos).round(1)
    terr[y] = t[["validos", "pct_elmo"]]
    z = p.groupby(["zona", p.NM_VOTAVEL.str.contains("ELMO")]).QT_VOTOS.sum().unstack()
    OUT[f"zona_prefeito_{y}"] = {k: {"elmo": int(r[True]), "outro": int(r[False]),
                                     "pct_elmo": round(100 * r[True] / (r[True] + r[False]), 1)} for k, r in z.iterrows()}
tb = terr[2020].join(terr[2024], lsuffix="_2020", rsuffix="_2024", how="outer")
tb["variacao_pp"] = (tb.pct_elmo_2024 - tb.pct_elmo_2020).round(1)
tb["zona"] = [zona(b) for b in tb.index]
tb = tb.sort_values("validos_2024", ascending=False)
tb.to_csv(D / "territorio_prefeito_bairros.csv", sep=";")
OUT["territorio_prefeito"] = tb.reset_index().round(1).to_dict("records")

# coordenadas por bairro (média dos locais válidos) para o mapa
l24 = loc[2024].copy(); l24 = l24[(l24.lat < -3.9) & (l24.lat > -4.4)]
l24["bairro"] = l24.bairro.map(norm_b)
coords = l24.groupby("bairro")[["lat", "lon"]].mean()
OUT["coords_bairros"] = coords.round(5).reset_index().to_dict("records")
OUT["locais_mapa"] = l24.reset_index()[["NR_LOCAL_VOTACAO", "nome", "bairro", "lat", "lon", "eleitores"]].to_dict("records")

# ------------------------------------------------------------- vereadores 2020 × 2024
c20 = rd("consulta_cand_2020_CE.csv"); c24 = rd("consulta_cand_2024_CE.csv")
v20 = rd("votacao_candidato_munzona_2020_CE.csv"); v24 = rd("votacao_candidato_munzona_2024_CE.csv")
def base(c, v):
    c = c[c.DS_CARGO.isin(["VEREADOR", "PREFEITO", "VICE-PREFEITO"])]
    vv = v.groupby("SQ_CANDIDATO").QT_VOTOS_NOMINAIS.sum()
    c = c.assign(votos=c.SQ_CANDIDATO.map(vv))
    ver = c[c.DS_CARGO == "VEREADOR"].copy()
    ver["rank"] = ver.votos.rank(ascending=False, method="min")
    c = c.merge(ver[["SQ_CANDIDATO", "rank"]], on="SQ_CANDIDATO", how="left")
    return c[["NR_TITULO_ELEITORAL_CANDIDATO", "NM_CANDIDATO", "NM_URNA_CANDIDATO", "DS_CARGO", "SG_PARTIDO", "votos", "DS_SIT_TOT_TURNO", "rank", "DS_GENERO"]]
a, b = base(c20, v20), base(c24, v24)
m = a.merge(b, on="NR_TITULO_ELEITORAL_CANDIDATO", how="outer", suffixes=("_2020", "_2024"))
m["nome"] = m.NM_URNA_CANDIDATO_2024.fillna(m.NM_URNA_CANDIDATO_2020)
m["nome_completo"] = m.NM_CANDIDATO_2024.fillna(m.NM_CANDIDATO_2020)
def var(r):
    if pd.isna(r.votos_2020) and pd.isna(r.votos_2024): return ""
    if pd.isna(r.votos_2020): return "Não concorreu em 2020 — comparação não aplicável"
    if pd.isna(r.votos_2024): return "Não concorreu em 2024 — comparação não aplicável"
    if r.DS_CARGO_2020 != r.DS_CARGO_2024: return f"Mudou de cargo ({r.DS_CARGO_2020.title()} → {r.DS_CARGO_2024.title()}) — comparação não aplicável"
    d = r.votos_2024 - r.votos_2020; pc = 100 * d / r.votos_2020
    lab = "Crescimento" if pc > 10 else ("Queda" if pc < -10 else "Estabilidade")
    return f"{lab}: {d:+.0f} votos ({pc:+.0f}%)"
m["comparacao"] = m.apply(var, axis=1)
m["mudou_partido"] = (m.SG_PARTIDO_2020.notna() & m.SG_PARTIDO_2024.notna() & (m.SG_PARTIDO_2020 != m.SG_PARTIDO_2024))
cols = ["nome", "nome_completo", "DS_CARGO_2020", "SG_PARTIDO_2020", "votos_2020", "rank_2020", "DS_SIT_TOT_TURNO_2020",
        "DS_CARGO_2024", "SG_PARTIDO_2024", "votos_2024", "rank_2024", "DS_SIT_TOT_TURNO_2024", "comparacao", "mudou_partido"]
m = m[cols].sort_values(["votos_2024", "votos_2020"], ascending=False)
m.to_csv(D / "tabela_candidatos_2020_2024.csv", sep=";", index=False)
OUT["tabela_candidatos"] = m.fillna("").to_dict("records")

# ------------------------------------------------------------- redutos dos vereadores (bairro mais forte)
red = {}
for y in (2020, 2024):
    s = sec[y]; v = s[s.cargo == "VEREADOR"]
    nom = v[v.SQ_CANDIDATO > 0] if "SQ_CANDIDATO" in v else v
    g = nom.groupby(["NM_VOTAVEL", "bairro"]).QT_VOTOS.sum().reset_index()
    tot = g.groupby("NM_VOTAVEL").QT_VOTOS.sum()
    g["pct_do_candidato"] = 100 * g.QT_VOTOS / g.NM_VOTAVEL.map(tot)
    bt = s[s.cargo == "VEREADOR"].groupby("bairro").QT_VOTOS.sum()
    g["pct_do_bairro"] = 100 * g.QT_VOTOS / g.bairro.map(bt)
    top = g.sort_values("QT_VOTOS", ascending=False).groupby("NM_VOTAVEL").head(1)
    top = top[top.NM_VOTAVEL.map(tot) >= 200].assign(total=lambda x: x.NM_VOTAVEL.map(tot))
    red[y] = top.sort_values("total", ascending=False).round(1)
    # índice de concentração: % dos votos no bairro principal
    lider = g.sort_values("QT_VOTOS", ascending=False).groupby("bairro").head(1).sort_values("QT_VOTOS", ascending=False)
    OUT[f"lider_por_bairro_{y}"] = lider.round(1).to_dict("records")
    OUT[f"redutos_{y}"] = red[y].to_dict("records")

# ------------------------------------------------------------- linha do tempo (fatos com fonte)
OUT["linha_do_tempo"] = [
    {"data": "2009–2016", "fato": "Rosa Paulino (MDB) prefeita por dois mandatos", "fonte": "O Povo (coluna Tânia Alves, 19/11/2020); lei municipal 574/2015 assinada por Rosa Cândida de Oliveira Ximenes", "confianca": "média"},
    {"data": "2017–2020", "fato": "Célia Rodrigues (MDB) prefeita; MDB completa 12 anos no poder", "fonte": "O Povo (19/11/2020)", "confianca": "média"},
    {"data": "fev/2021", "fato": "MPCE deflagra operação sobre contratos de coleta de lixo (2016–2020) com suspeita de uso de 'laranjas'", "fonte": "MPCE (nota oficial)", "confianca": "alta (existência da operação); sem informação de desfecho"},
    {"data": "15/11/2020", "fato": "Elmo Monte (PDT) eleito com 53,1%; fim do ciclo do MDB", "fonte": "TSE", "confianca": "alta"},
    {"data": "2021", "fato": "MP Eleitoral pede cassação de Elmo e da vice Alessandra Araújo Pinheiro (Loura do Povo) por abuso de poder econômico e compra de votos", "fonte": "MPCE (nota oficial)", "confianca": "alta (pedido); desfecho NÃO LOCALIZADO — ambos cumpriram o mandato"},
    {"data": "16/09/2021", "fato": "TRE-CE mantém multa a Rosa Paulino por aglomeração na campanha de 2020", "fonte": "O Povo (16/09/2021)", "confianca": "alta"},
    {"data": "2023–2024", "fato": "Grupo de Cid Gomes migra do PDT para o PSB; Elmo acompanha", "fonte": "Diário do Nordeste; TSE (filiação de 2024)", "confianca": "alta"},
    {"data": "06/10/2024", "fato": "Elmo (PSB) reeleito com 64,3%; ex-vice Loura do Povo concorre como vice da oposição (PP)", "fonte": "TSE", "confianca": "alta"},
    {"data": "19/08/2025", "fato": "TAC entre MPCE e Prefeitura para melhorar infraestrutura das UBS", "fonte": "MPCE (nota oficial)", "confianca": "alta (existência); conteúdo detalhado não lido"},
    {"data": "set/2026", "fato": "Vice-prefeito Erivaldo Mororó anuncia rompimento com Elmo; cita apoio a Ciro Gomes, falta de acesso ao prefeito e omissão do nome em placas; diz que não vai para a oposição", "fonte": "Blog do Amaury Alencar (set/2026)", "confianca": "média (fonte única, blog local)"},
    {"data": "04/10/2026", "fato": "Ciro Gomes (PSDB) vence em Varjota com 58,1%; Elmano (PT) reeleito no estado", "fonte": "TSE", "confianca": "alta"},
]

(D / "raiox.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1, default=str))
print(fin.to_string())
print(tb.to_string())
print(json.dumps({k: OUT[k] for k in ("zona_prefeito_2020", "zona_prefeito_2024")}, ensure_ascii=False))
print(red[2024][["NM_VOTAVEL", "bairro", "QT_VOTOS", "total", "pct_do_candidato", "pct_do_bairro"]].to_string())
print(pd.DataFrame(OUT["lider_por_bairro_2024"])[["bairro", "NM_VOTAVEL", "QT_VOTOS", "pct_do_bairro"]].to_string())
