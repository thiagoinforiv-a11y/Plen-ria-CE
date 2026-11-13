"""Análise eleitoral de Varjota-CE (2020, 2022, 2024) com projeção 2028.

Fonte: Portal de Dados Abertos do TSE (cdn.tse.jus.br/estatistica/sead/odsele).
Uso:  python3 analise.py <pasta_com_csvs_filtrados_de_varjota>
Gera: ../dados/metricas.json e ../graficos/*.png
"""
import json, math, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SRC = Path(sys.argv[1])
BASE = Path(__file__).resolve().parent.parent
OUT_G = BASE / "graficos"; OUT_G.mkdir(exist_ok=True)
VAGAS = 11

COR = {"PSB": "#E8A33D", "PDT": "#D9534F", "MDB": "#2F6DB5", "PT": "#B8282E",
       "PL": "#1F8A70", "FE BRASIL": "#B8282E", "OUTROS": "#8A8F98"}
GOV, OPO = "#C0392B", "#2F6DB5"
INK, MUTED, BG = "#1d2330", "#6b7280", "#ffffff"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#c9ccd3", "axes.titleweight": "bold",
                     "axes.titlesize": 17, "axes.titlelocation": "left", "figure.dpi": 110})


def rd(name):
    return pd.read_csv(SRC / name, sep=";", low_memory=False)


def quociente(validos, vagas=VAGAS):
    q = validos / vagas
    return math.floor(q) if q - math.floor(q) <= 0.5 else math.ceil(q)  # art. 106 CE


def distribui(votos: dict, qe: int, vagas=VAGAS):
    """QP + sobras pelo método das maiores médias (D'Hondt), exigindo 80% do QE."""
    qp = {p: v // qe for p, v in votos.items()}
    cad = dict(qp); rodadas = []
    while sum(cad.values()) < vagas:
        aptos = {p: v for p, v in votos.items() if v >= 0.8 * qe} or votos
        med = {p: votos[p] / (cad[p] + 1) for p in aptos}
        win = max(med, key=med.get)
        rodadas.append({"vencedor": win, "medias": {k: round(x, 1) for k, x in med.items()}})
        cad[win] += 1
    return qp, cad, rodadas


M = {}
# ------------------------------------------------------------------ comparecimento
det = {}
for y in (2020, 2024):
    d = rd(f"detalhe_votacao_munzona_{y}_CE.csv")
    for _, r in d.iterrows():
        det[(y, r.DS_CARGO.upper())] = r
d22 = rd("det2022.csv").iloc[0]
M["eleitorado"] = {"2020": int(det[(2020, "PREFEITO")].QT_APTOS), "2022": int(d22.QT_APTOS),
                   "2024": int(det[(2024, "PREFEITO")].QT_APTOS)}
M["comparecimento"] = {}
for y in (2020, 2024):
    r = det[(y, "PREFEITO")]; v = det[(y, "VEREADOR")]
    M["comparecimento"][str(y)] = {
        "aptos": int(r.QT_APTOS), "compareceram": int(r.QT_COMPARECIMENTO), "abstencao": int(r.QT_ABSTENCOES),
        "pct_comparecimento": round(100 * r.QT_COMPARECIMENTO / r.QT_APTOS, 2),
        "prefeito_validos": int(r.QT_TOTAL_VOTOS_VALIDOS), "prefeito_brancos": int(r.QT_VOTOS_BRANCOS),
        "prefeito_nulos": int(r.QT_TOTAL_VOTOS_NULOS), "vereador_validos": int(v.QT_TOTAL_VOTOS_VALIDOS),
        "vereador_nominais": int(v.QT_VOTOS_NOMINAIS_VALIDOS), "vereador_legenda": int(v.QT_TOTAL_VOTOS_LEG_VALIDOS),
        "vereador_brancos": int(v.QT_VOTOS_BRANCOS), "vereador_nulos": int(v.QT_TOTAL_VOTOS_NULOS),
        "secoes": int(r.QT_TOTAL_SECOES)}
M["comparecimento"]["2022"] = {"aptos": int(d22.QT_APTOS), "compareceram": int(d22.QT_COMPARECIMENTO),
                               "pct_comparecimento": round(100 * d22.QT_COMPARECIMENTO / d22.QT_APTOS, 2)}

# ------------------------------------------------------------------ prefeito / vereador
cand, partidos, cadeiras = {}, {}, {}
for y in (2020, 2024):
    v = rd(f"votacao_candidato_munzona_{y}_CE.csv")
    pref = v[v.DS_CARGO == "Prefeito"].sort_values("QT_VOTOS_NOMINAIS", ascending=False)
    tot = pref.QT_VOTOS_NOMINAIS.sum()
    M[f"prefeito_{y}"] = [{"nome": r.NM_URNA_CANDIDATO, "partido": r.SG_PARTIDO, "coligacao": r.NM_COLIGACAO,
                           "composicao": r.DS_COMPOSICAO_COLIGACAO, "votos": int(r.QT_VOTOS_NOMINAIS),
                           "pct": round(100 * r.QT_VOTOS_NOMINAIS / tot, 2), "situacao": r.DS_SIT_TOT_TURNO}
                          for _, r in pref.iterrows()]
    ver = v[v.DS_CARGO == "Vereador"].copy()
    ver["lista"] = ver.SG_PARTIDO.where(ver.TP_AGREMIACAO != "FEDERAÇÃO", "FE BRASIL") \
        if "TP_AGREMIACAO" in ver else ver.SG_PARTIDO
    p = rd(f"votacao_partido_munzona_{y}_CE.csv"); p = p[p.DS_CARGO == "Vereador"].copy()
    fed = {"PT": "FE BRASIL", "PV": "FE BRASIL", "PC do B": "FE BRASIL"} if y == 2024 else {}
    p["lista"] = p.SG_PARTIDO.replace(fed)
    ver["lista"] = ver.SG_PARTIDO.replace(fed)
    leg = p.groupby("lista").QT_TOTAL_VOTOS_LEG_VALIDOS.sum()
    nom = ver.groupby("lista").QT_VOTOS_NOMINAIS.sum()
    votos = {k: int(nom.get(k, 0) + leg.get(k, 0)) for k in set(nom.index) | set(leg.index)}
    validos = M["comparecimento"][str(y)]["vereador_validos"]
    qe = quociente(validos); qp, cad, rod = distribui(votos, qe)
    eleitos = ver[ver.DS_SIT_TOT_TURNO.str.startswith("ELEITO")]
    nao = ver[~ver.DS_SIT_TOT_TURNO.str.startswith("ELEITO")]
    # margem da última cadeira: quantos votos o 2º colocado na última rodada precisaria
    ult = rod[-1]; med = ult["medias"]; win = ult["vencedor"]
    margem = {}
    cad_antes = dict(cad); cad_antes[win] -= 1
    for k in med:
        if k != win:
            margem[k] = int(math.ceil(med[win] * (cad_antes[k] + 1) - votos[k])) + 1
    M[f"vereador_{y}"] = {
        "validos": validos, "quociente_eleitoral": qe, "qe_exato": round(validos / VAGAS, 2),
        "clausula_10pct_qe": math.ceil(0.10 * qe), "barreira_80pct_qe": math.ceil(0.8 * qe),
        "candidatos_votados": int(len(ver)), "listas": len(votos),
        "votos_por_lista": dict(sorted(votos.items(), key=lambda x: -x[1])),
        "legenda_por_lista": {k: int(x) for k, x in leg.items()},
        "quociente_partidario": qp, "cadeiras": cad, "rodadas_sobras": rod, "margem_ultima_cadeira": margem,
        "eleitos": [{"nome": r.NM_URNA_CANDIDATO, "partido": r.SG_PARTIDO, "votos": int(r.QT_VOTOS_NOMINAIS),
                     "como": r.DS_SIT_TOT_TURNO} for _, r in eleitos.sort_values("QT_VOTOS_NOMINAIS", ascending=False).iterrows()],
        "menos_votado_eleito": int(eleitos.QT_VOTOS_NOMINAIS.min()),
        "mais_votado_nao_eleito": {"nome": nao.sort_values("QT_VOTOS_NOMINAIS").iloc[-1].NM_URNA_CANDIDATO,
                                   "votos": int(nao.QT_VOTOS_NOMINAIS.max())},
        "pct_votos_em_eleitos": round(100 * eleitos.QT_VOTOS_NOMINAIS.sum() / validos, 1),
        "candidatos_abaixo_100_votos": int((ver.QT_VOTOS_NOMINAIS < 100).sum()),
        "top3_lista_concentracao": {k: round(100 * g.nlargest(3, "QT_VOTOS_NOMINAIS").QT_VOTOS_NOMINAIS.sum() / g.QT_VOTOS_NOMINAIS.sum(), 1)
                                    for k, g in ver.groupby("lista")},
    }
    cand[y] = ver

# ------------------------------------------------------------------ perfil dos candidatos
perf = {}
c = {y: rd(f"consulta_cand_{y}_CE.csv") for y in (2020, 2024)}
for y, df in c.items():
    vv = df[df.DS_CARGO == "VEREADOR"]
    el = vv[vv.DS_SIT_TOT_TURNO.str.startswith("ELEITO")]
    idade = lambda s: (pd.Timestamp(f"{y}-10-01") - pd.to_datetime(s, dayfirst=True)).dt.days / 365.25
    perf[str(y)] = {"registrados": int(len(vv)), "mulheres_candidatas": int((vv.DS_GENERO == "FEMININO").sum()),
                    "mulheres_eleitas": int((el.DS_GENERO == "FEMININO").sum()),
                    "idade_media_eleitos": round(idade(el.DT_NASCIMENTO).mean(), 1),
                    "superior_eleitos": int(el.DS_GRAU_INSTRUCAO.str.contains("SUPERIOR COMPLETO").sum()),
                    "candidatos_por_partido": vv.SG_PARTIDO.value_counts().to_dict()}
M["perfil_candidatos"] = perf

m = c[2020].merge(c[2024], on="NR_TITULO_ELEITORAL_CANDIDATO", suffixes=("_20", "_24"))
M["trajetorias"] = [{"nome": r.NM_URNA_CANDIDATO_24, "cargo_20": r.DS_CARGO_20, "partido_20": r.SG_PARTIDO_20,
                     "sit_20": r.DS_SIT_TOT_TURNO_20, "cargo_24": r.DS_CARGO_24, "partido_24": r.SG_PARTIDO_24,
                     "sit_24": r.DS_SIT_TOT_TURNO_24} for _, r in m.iterrows()]
el20 = c[2020][(c[2020].DS_CARGO == "VEREADOR") & c[2020].DS_SIT_TOT_TURNO.str.startswith("ELEITO")]
el24 = c[2024][(c[2024].DS_CARGO == "VEREADOR") & c[2024].DS_SIT_TOT_TURNO.str.startswith("ELEITO")]
tit24 = set(c[2024].NR_TITULO_ELEITORAL_CANDIDATO)
M["renovacao"] = {"eleitos_2020_que_concorreram_2024": int(el20.NR_TITULO_ELEITORAL_CANDIDATO.isin(tit24).sum()),
                  "reeleitos": int(el24.NR_TITULO_ELEITORAL_CANDIDATO.isin(el20.NR_TITULO_ELEITORAL_CANDIDATO).sum()),
                  "novos_na_camara_2024": int((~el24.NR_TITULO_ELEITORAL_CANDIDATO.isin(el20.NR_TITULO_ELEITORAL_CANDIDATO)).sum()),
                  "nao_concorreram": el20[~el20.NR_TITULO_ELEITORAL_CANDIDATO.isin(tit24)].NM_URNA_CANDIDATO.tolist()}

# ------------------------------------------------------------------ bens declarados
bens = {}
for y in (2020, 2024):
    b = rd(f"bem_candidato_{y}_CE.csv")
    b["VR"] = b.VR_BEM_CANDIDATO.astype(str).str.replace(",", ".").astype(float)
    t = b.groupby("SQ_CANDIDATO").VR.sum()
    cc = c[y].set_index("SQ_CANDIDATO")
    bens[str(y)] = {"total": round(t.sum(), 2), "declarantes": int(len(t)),
                    "top5": [{"nome": cc.loc[k].NM_URNA_CANDIDATO, "cargo": cc.loc[k].DS_CARGO, "valor": round(x, 2)}
                             for k, x in t.nlargest(5).items() if k in cc.index]}
M["bens"] = bens

# ------------------------------------------------------------------ geografia (local de votação)
geo = {}
for y in (2020, 2024):
    s = rd(f"secao_prefeito_{y}.csv")
    s = s[~s.NM_VOTAVEL.str.startswith("VOTO")]
    t = s.pivot_table(index=["NR_LOCAL_VOTACAO", "NM_LOCAL_VOTACAO"], columns="NM_VOTAVEL", values="QT_VOTOS", aggfunc="sum", fill_value=0)
    elmo = [k for k in t.columns if "ELMO" in k][0]
    t["total"] = t.sum(axis=1); t["pct_elmo"] = 100 * t[elmo] / t.total
    geo[y] = t.reset_index()
g = geo[2020][["NR_LOCAL_VOTACAO", "NM_LOCAL_VOTACAO", "pct_elmo", "total"]].merge(
    geo[2024][["NR_LOCAL_VOTACAO", "pct_elmo", "total"]], on="NR_LOCAL_VOTACAO", suffixes=("_20", "_24"))
g["swing"] = g.pct_elmo_24 - g.pct_elmo_20
g = g.sort_values("swing")
M["geografia"] = {"locais_2020": int(len(geo[2020])), "locais_2024": int(len(geo[2024])),
                  "locais_oposicao_venceu_2020": geo[2020][geo[2020].pct_elmo < 50].NM_LOCAL_VOTACAO.tolist(),
                  "locais_oposicao_venceu_2024": geo[2024][geo[2024].pct_elmo < 50].NM_LOCAL_VOTACAO.tolist(),
                  "maior_avanco": g.tail(5)[["NM_LOCAL_VOTACAO", "pct_elmo_20", "pct_elmo_24", "swing"]].round(1).to_dict("records"),
                  "menor_avanco": g.head(5)[["NM_LOCAL_VOTACAO", "pct_elmo_20", "pct_elmo_24", "swing"]].round(1).to_dict("records")}

# ------------------------------------------------------------------ 2022
v22 = rd("votacao_candidato_munzona_2022_CE.csv"); v22 = v22[v22.NM_MUNICIPIO == "VARJOTA"]
pr = rd("pres2022.csv"); pr = pr[pr.NM_MUNICIPIO == "VARJOTA"]
def top(df, cargo, turno=1, n=5):
    x = df[(df.DS_CARGO == cargo) & (df.NR_TURNO == turno)].groupby(["NM_URNA_CANDIDATO", "SG_PARTIDO"]).QT_VOTOS_NOMINAIS.sum()
    tot = x.sum(); x = x.nlargest(n)
    return [{"nome": a, "partido": b, "votos": int(v), "pct": round(100 * v / tot, 1)} for (a, b), v in x.items()]
M["eleicao_2022"] = {"presidente_1t": top(pr, "Presidente"), "presidente_2t": top(pr, "Presidente", 2),
                     "governador": top(v22, "Governador"), "senador": top(v22, "Senador", n=3),
                     "dep_federal": top(v22, "Deputado Federal", n=6), "dep_estadual": top(v22, "Deputado Estadual", n=6)}

# ------------------------------------------------------------------ 2026 (eleição geral mais recente)
d26 = rd("26_detalhe_votacao_munzona_2026_CE.csv").iloc[0]
M["eleitorado"]["2026"] = int(d26.QT_APTOS)
M["comparecimento"]["2026"] = {"aptos": int(d26.QT_APTOS), "compareceram": int(d26.QT_COMPARECIMENTO),
                               "pct_comparecimento": round(100 * d26.QT_COMPARECIMENTO / d26.QT_APTOS, 2)}
c26 = rd("26_votacao_candidato_munzona_2026_CE.csv"); c26 = c26[c26.NM_MUNICIPIO == "VARJOTA"]
p26 = rd("26_votacao_candidato_munzona_2026_BR.csv"); p26 = p26[p26.NM_MUNICIPIO == "VARJOTA"]
M["eleicao_2026"] = {"presidente_1t": top(p26, "Presidente"), "presidente_2t": top(p26, "Presidente", 2),
                     "governador": top(c26, "Governador", n=3), "senador": top(c26, "Senador", n=4),
                     "dep_federal": top(c26, "Deputado Federal", n=6), "dep_estadual": top(c26, "Deputado Estadual", n=6)}

# ------------------------------------------------------------------ eleitorado
def perfil(f, col):
    e = rd(f); e = e[e.NM_MUNICIPIO == "VARJOTA"]
    return e, col
e20, k20 = perfil("perfil_eleitorado_2020.csv", "QT_ELEITORES_PERFIL")
e24, k24 = perfil("perfil_eleitorado_2024_CE.csv", "QT_ELEITORES")
def faixas(e, k):
    f = e.groupby("DS_FAIXA_ETARIA")[k].sum(); tot = f.sum()
    def soma(pred): return int(sum(v for i, v in f.items() if pred(i)))
    def ini(i):
        try: return int(str(i).split()[0])
        except: return 999
    return {"16-24": soma(lambda i: ini(i) <= 24), "25-44": soma(lambda i: 25 <= ini(i) <= 44),
            "45-59": soma(lambda i: 45 <= ini(i) <= 59), "60+": soma(lambda i: 60 <= ini(i) < 999), "total": int(tot)}
def escol(e, k):
    f = e.groupby("DS_GRAU_ESCOLARIDADE")[k].sum(); tot = f.sum()
    return {i: round(100 * v / tot, 1) for i, v in f.items()}
M["eleitorado_perfil"] = {"2020": {"faixas": faixas(e20, k20), "escolaridade": escol(e20, k20),
                                   "mulheres_pct": round(100 * e20[e20.DS_GENERO == "FEMININO"][k20].sum() / e20[k20].sum(), 1)},
                          "2024": {"faixas": faixas(e24, k24), "escolaridade": escol(e24, k24),
                                   "mulheres_pct": round(100 * e24[e24.DS_GENERO == "FEMININO"][k24].sum() / e24[k24].sum(), 1)}}

# ------------------------------------------------------------------ projeção 2028
apt = M["eleitorado"]; ap28 = {"baixo": 15600, "central": 15850, "alto": 16100}  # tendência: 16.757 (2022) → 16.213 (2024) → 15.991 (2026)
comp = {"baixo": 0.855, "central": 0.875, "alto": 0.89}
val = 0.958  # válidos/comparecimento para vereador (2020: 96,05%; 2024: 95,78%)
proj = {}
for k in ap28:
    vv = ap28[k] * comp[k] * val
    proj[k] = {"aptos": ap28[k], "comparecimento": round(ap28[k] * comp[k]), "validos_vereador": round(vv),
               "quociente_eleitoral": quociente(vv), "barreira_80pct": math.ceil(0.8 * quociente(vv)),
               "minimo_individual_10pct": math.ceil(0.1 * quociente(vv)), "voto_para_sobra_20pct": math.ceil(0.2 * quociente(vv))}
# simulação de cadeiras em 3 cenários de lista
base24 = M["vereador_2024"]["votos_por_lista"]; vc = proj["central"]["validos_vereador"]; qe = proj["central"]["quociente_eleitoral"]
cen = {
    "A_continuidade": {"PSB": 0.45, "FE BRASIL": 0.25, "MDB": 0.30},
    "B_fragmentacao": {"PSB": 0.33, "FE BRASIL": 0.20, "MDB": 0.25, "REPUBLICANOS/UNIAO": 0.12, "PL/PP": 0.10},
    "C_oposicao_cresce": {"PSB": 0.36, "FE BRASIL": 0.20, "MDB": 0.38, "PP": 0.06},
}
sim = {}
for nome, sh in cen.items():
    votos = {p: int(vc * s) for p, s in sh.items()}
    qp, cad, _ = distribui(votos, qe)
    sim[nome] = {"participacao": sh, "votos": votos, "cadeiras": cad}
M["projecao_2028"] = {"premissas": {"aptos": ap28, "comparecimento": comp, "validos_sobre_comparecimento": val},
                      "cenarios_quociente": proj, "simulacao_cadeiras": sim,
                      "max_candidatos_por_partido": VAGAS + 1}

(BASE / "dados" / "metricas.json").write_text(json.dumps(M, ensure_ascii=False, indent=2, default=str))

# ================================================================== GRÁFICOS (16:9)
def fig(): return plt.subplots(figsize=(12.8, 7.2))
def save(f, n):
    f.tight_layout(); f.savefig(OUT_G / n, dpi=150, facecolor=BG); plt.close(f)

# 1 prefeito
f, ax = fig()
labs = ["2020", "2024"]
gov = [M["prefeito_2020"][0]["pct"], M["prefeito_2024"][0]["pct"]]
opo = [M["prefeito_2020"][1]["pct"], M["prefeito_2024"][1]["pct"]]
ax.barh([1, 0], gov, color=GOV, height=.55); ax.barh([1, 0], opo, left=gov, color=OPO, height=.55)
for i, (a, b, y) in enumerate(zip(gov, opo, [1, 0])):
    pa, pb = M[f"prefeito_{labs[i]}"]
    ax.text(a / 2, y, f"{pa['nome']} ({pa['partido']})\n{pa['votos']:,} votos · {a:.1f}%".replace(",", "."), ha="center", va="center", color="white", fontsize=13, weight="bold")
    ax.text(a + b / 2, y, f"{pb['nome']} ({pb['partido']})\n{pb['votos']:,} votos · {b:.1f}%".replace(",", "."), ha="center", va="center", color="white", fontsize=13, weight="bold")
ax.set_yticks([1, 0], labs, fontsize=16); ax.set_xlim(0, 100); ax.axvline(50, color="white", lw=2, ls=":")
ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
ax.set_title("Prefeito de Varjota: margem saltou de 6,2 para 28,6 pontos")
save(f, "01_prefeito.png")

# 2 comparecimento
f, ax = fig()
anos = ["2020", "2022", "2024", "2026"]
pc = [M["comparecimento"][a]["pct_comparecimento"] for a in anos]
ap = [M["comparecimento"][a]["aptos"] for a in anos]
cp = [M["comparecimento"][a]["compareceram"] for a in anos]
ax.bar(anos, ap, color="#d7dbe3", width=.6, label="Eleitores aptos")
ax.bar(anos, cp, color="#3b5b92", width=.6, label="Compareceram")
for i in range(4):
    ax.text(i, cp[i] + 250, f"{pc[i]:.1f}%", ha="center", fontsize=16, weight="bold", color=INK)
    ax.text(i, 600, f"{cp[i]:,}".replace(",", ".") + f"\nde {ap[i]:,}".replace(",", "."), ha="center", color="white", fontsize=12)
ax.set_ylim(0, 19000); ax.legend(frameon=False, loc="upper left"); ax.set_yticks([])
ax.set_title("Comparecimento: a eleição municipal mobiliza mais que a geral")
save(f, "02_comparecimento.png")

# 3 quociente e cadeiras
for y in (2020, 2024):
    V = M[f"vereador_{y}"]; f, ax = fig()
    items = list(V["votos_por_lista"].items())
    names = [k for k, _ in items]; vals = [v for _, v in items]
    cols = [COR.get(k, COR["OUTROS"]) for k in names]
    ax.bar(names, vals, color=cols, width=.6)
    for qx in range(1, 6):
        ax.axhline(V["quociente_eleitoral"] * qx, color="#9aa1ad", lw=1, ls="--", zorder=0)
        ax.text(-.45, V["quociente_eleitoral"] * qx, f"{qx}× QE", va="bottom", ha="left", fontsize=10, color=MUTED)
    for i, n in enumerate(names):
        ax.text(i, vals[i] + 90, f"{vals[i]:,} votos".replace(",", ".") + f"\n{V['cadeiras'][n]} cadeira(s)", ha="center", fontsize=14, weight="bold")
    ax.set_ylim(0, max(vals) * 1.25); ax.set_yticks([])
    ax.set_title(f"Câmara {y}: quociente eleitoral = {V['quociente_eleitoral']:,} votos".replace(",", "."))
    save(f, f"03_quociente_{y}.png")

# 4 composição câmara (governo x oposição)
f, axs = plt.subplots(1, 2, figsize=(12.8, 7.2))
for ax, y in zip(axs, ("2020", "2024")):
    cadd = M[f"vereador_{y}"]["cadeiras"]; seq = []
    gov_l = ["PDT", "PT"] if y == "2020" else ["PSB", "FE BRASIL"]
    for p in gov_l: seq += [(p, GOV)] * cadd.get(p, 0)
    for p in [k for k in cadd if k not in gov_l]: seq += [(p, OPO)] * cadd[p]
    import numpy as np
    ang = np.linspace(np.pi, 0, len(seq))
    for (p, col), a in zip(seq, ang):
        ax.scatter(np.cos(a), np.sin(a), s=1500, color=col, edgecolor="white", lw=2)
        ax.text(np.cos(a), np.sin(a), p.replace("FE BRASIL", "PT"), ha="center", va="center", color="white", fontsize=8, weight="bold")
    g_ = sum(cadd.get(p, 0) for p in gov_l); o_ = VAGAS - g_
    ax.text(0, .15, f"{g_} × {o_}", ha="center", fontsize=34, weight="bold", color=INK)
    ax.text(0, -.12, "base do prefeito × oposição", ha="center", fontsize=12, color=MUTED)
    ax.set_title(y, loc="center", fontsize=20); ax.set_xlim(-1.3, 1.3); ax.set_ylim(-.3, 1.3); ax.axis("off")
f.suptitle("Câmara Municipal: de minoria a supermaioria governista", x=.03, ha="left", fontsize=17, weight="bold")
save(f, "04_camara.png")

# 5 vereadores 2024 – votos individuais
for y in (2020, 2024):
    vv = cand[y].sort_values("QT_VOTOS_NOMINAIS", ascending=True).tail(20)
    f, ax = fig()
    cols = [COR.get(l, COR["OUTROS"]) if s.startswith("ELEITO") else "#cfd3da" for l, s in zip(vv.lista, vv.DS_SIT_TOT_TURNO)]
    ax.barh(vv.NM_URNA_CANDIDATO + " (" + vv.SG_PARTIDO + ")", vv.QT_VOTOS_NOMINAIS, color=cols)
    for i, (n, s) in enumerate(zip(vv.QT_VOTOS_NOMINAIS, vv.DS_SIT_TOT_TURNO)):
        ax.text(n + 10, i, f"{n}  {'✔ ' + s.replace('ELEITO POR ', '') if s.startswith('ELEITO') else 'suplente'}", va="center", fontsize=10)
    ax.tick_params(axis="y", labelsize=10); ax.set_xticks([])
    ax.set_title(f"Vereadores {y}: os 20 mais votados (cinza = não eleito)")
    save(f, f"05_vereadores_{y}.png")

# 6 swing geográfico
f, ax = fig()
gg = g.copy(); gg["nome"] = gg.NM_LOCAL_VOTACAO.str.slice(0, 38)
ax.scatter(gg.pct_elmo_20, gg.pct_elmo_24, s=gg.total_24 / 2.5, color=GOV, alpha=.65, edgecolor="white")
ax.plot([30, 80], [30, 80], color="#9aa1ad", ls="--"); ax.axhline(50, color="#ccc"); ax.axvline(50, color="#ccc")
for _, r in pd.concat([gg.head(3), gg.tail(3)]).iterrows():
    ax.annotate(r.nome, (r.pct_elmo_20, r.pct_elmo_24), fontsize=9, xytext=(6, -3), textcoords="offset points")
ax.set_xlabel("% de Elmo em 2020 (por local de votação)"); ax.set_ylabel("% de Elmo em 2024")
ax.set_title("Todos os locais acima da diagonal: o avanço foi generalizado")
save(f, "06_geografia.png")

# 7 trajetórias / migração
f, ax = fig(); ax.axis("off")
mig = [t for t in M["trajetorias"] if t["partido_20"] != t["partido_24"]]
ax.set_title("Quem trocou de partido entre 2020 e 2024")
for i, t in enumerate(mig[:14]):
    yy = .92 - i * .065
    ax.text(.02, yy, t["nome"], fontsize=13, weight="bold", transform=ax.transAxes)
    ax.text(.40, yy, f"{t['partido_20']}  →  {t['partido_24']}", fontsize=13, transform=ax.transAxes,
            color=GOV if t["partido_24"] in ("PSB", "PT") else OPO)
    ax.text(.62, yy, f"{t['sit_20'].title()} → {t['sit_24'].title()}  ({t['cargo_24'].title()})", fontsize=11, color=MUTED, transform=ax.transAxes)
save(f, "07_migracoes.png")

# 8 eleitorado
f, ax = fig()
fx = ["16-24", "25-44", "45-59", "60+"]
a20 = [M["eleitorado_perfil"]["2020"]["faixas"][k] for k in fx]; a24 = [M["eleitorado_perfil"]["2024"]["faixas"][k] for k in fx]
import numpy as np
x = np.arange(4); ax.bar(x - .2, a20, .4, color="#9fb3d6", label="2020"); ax.bar(x + .2, a24, .4, color="#3b5b92", label="2024")
for i in range(4):
    ax.text(i - .2, a20[i] + 80, f"{a20[i]:,}".replace(",", "."), ha="center", fontsize=11)
    ax.text(i + .2, a24[i] + 80, f"{a24[i]:,}".replace(",", "."), ha="center", fontsize=11, weight="bold")
ax.set_xticks(x, [f + " anos" for f in fx]); ax.set_yticks([]); ax.legend(frameon=False)
ax.set_title("Menos jovens no cadastro: faixa de 16–24 anos perdeu 256 eleitores")
save(f, "08_eleitorado.png")

# 9 2022
f, axs = plt.subplots(1, 2, figsize=(12.8, 7.2))
for ax, (k, t) in zip(axs, (("governador", "Governador 2022"), ("presidente_2t", "Presidente 2022 – 2º turno"))):
    d = M["eleicao_2022"][k]
    ax.barh([x["nome"] for x in d][::-1], [x["pct"] for x in d][::-1], color=["#8a8f98"] * (len(d) - 1) + [GOV])
    for i, x in enumerate(d[::-1]): ax.text(x["pct"] + 1, i, f"{x['pct']}%", va="center", fontsize=12)
    ax.set_title(t, fontsize=15); ax.set_xticks([]); ax.set_xlim(0, 100)
f.suptitle("2022 em Varjota: voto alinhado ao governo estadual e federal", x=.03, ha="left", fontsize=17, weight="bold")
save(f, "09_2022.png")

# 9b 2026
f, axs = plt.subplots(1, 2, figsize=(12.8, 7.2))
for ax, (k, t) in zip(axs, (("governador", "Governador 2026"), ("senador", "Senador 2026 (2 vagas)"))):
    d = M["eleicao_2026"][k]
    ax.barh([f"{x['nome']} ({x['partido']})" for x in d][::-1], [x["pct"] for x in d][::-1], color=["#8a8f98"] * (len(d) - 1) + [GOV])
    for i, x in enumerate(d[::-1]): ax.text(x["pct"] + 1, i, f"{x['pct']}%", va="center", fontsize=12)
    ax.set_title(t, fontsize=15); ax.set_xticks([]); ax.set_xlim(0, 80); ax.tick_params(axis="y", labelsize=11)
f.suptitle("2026 em Varjota: Ciro vence o governador eleito; Senado pulverizado", x=.03, ha="left", fontsize=17, weight="bold")
save(f, "09b_2026.png")

# 10 projeção
f, ax = fig()
labs = ["2020\n(real)", "2024\n(real)", "2028\nbaixo", "2028\ncentral", "2028\nalto"]
qv = [M["vereador_2020"]["quociente_eleitoral"], M["vereador_2024"]["quociente_eleitoral"],
      proj["baixo"]["quociente_eleitoral"], proj["central"]["quociente_eleitoral"], proj["alto"]["quociente_eleitoral"]]
ax.bar(labs, qv, color=["#3b5b92", "#3b5b92", "#c9d3e6", "#9fb3d6", "#c9d3e6"], width=.6)
for i, q in enumerate(qv): ax.text(i, q + 15, f"{q:,}".replace(",", "."), ha="center", fontsize=16, weight="bold")
ax.set_ylim(1000, 1350); ax.set_yticks([])
ax.set_title("Quociente eleitoral projetado para 2028 (11 cadeiras)")
save(f, "10_projecao_qe.png")

print(json.dumps({k: M[k] for k in ("vereador_2020", "vereador_2024")}, ensure_ascii=False, indent=1, default=str)[:4000])
print(json.dumps({k: M[k] for k in ("renovacao", "perfil_candidatos", "bens", "geografia", "eleitorado_perfil", "projecao_2028")}, ensure_ascii=False, indent=1, default=str))
