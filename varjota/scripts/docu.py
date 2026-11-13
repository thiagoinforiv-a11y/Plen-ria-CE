"""Documentário 'VARJOTA 2028 — O RAIO-X DO PODER'.

Uso: python3 docu.py <modelo_piper.onnx> <pasta_trabalho>
Gera: ../video/varjota_2028_raio-x_do_poder.mp4 (+ .srt, roteiro e storyboard)
"""
import json, math, re, subprocess, sys, wave
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from num2words import num2words

sys.path.insert(0, str(Path(__file__).parent))
from doc_engine import *  # noqa

MODEL, WORK = sys.argv[1], Path(sys.argv[2]); WORK.mkdir(parents=True, exist_ok=True)
BASE = Path(__file__).resolve().parent.parent
D = BASE / "dados"
M = json.load(open(D / "metricas.json")); R = json.load(open(D / "raiox.json"))
SR = 22050

# ------------------------------------------------------------------ dados para o mapa
def locais_pct(y):
    s = pd.read_csv(D / f"secao_prefeito_{y}.csv", sep=";")
    s = s[~s.NM_VOTAVEL.str.startswith("VOTO")]
    t = s.pivot_table(index="NR_LOCAL_VOTACAO", columns="NM_VOTAVEL", values="QT_VOTOS", aggfunc="sum", fill_value=0)
    el = [c for c in t.columns if "ELMO" in c][0]
    return (100 * t[el] / t.sum(axis=1)), t.sum(axis=1)
p20, _ = locais_pct(2020); p24, v24 = locais_pct(2024)
LOC = [x for x in R["locais_mapa"]]
def nome_curto(n):
    n = re.sub(r"^(E\.E\.I\.F\.|E\.E\.F\.|E\.E\.I\.|C\.E\.I\.|EEB|EEF)\s*", "", n).title()
    return n[:26]
pts_base, pts_swing = [], []
for l in LOC:
    k = l["NR_LOCAL_VOTACAO"]
    pts_base.append(dict(lat=l["lat"], lon=l["lon"], size=l["eleitores"], color=GOLD_L))
    if k in p20.index and k in p24.index:
        sw = p24[k] - p20[k]
        col = lerp(DIM, GOLD_L, min(1, max(0, sw / 25)))
        lab = l["bairro"].title() if (sw > 20 or sw < 5) else ""
        pts_swing.append(dict(lat=l["lat"], lon=l["lon"], size=v24[k], color=col, label=lab, val=f"{sw:+.1f} pontos" if lab else ""))
for p in pts_base:
    pass
# rótulos de bairro no mapa de abertura (um por bairro, no maior local)
SEDE = {"CENTRO", "EMPRÉSTIMOS", "PEDREIRA", "ACAMPAMENTO DNOCS", "ACAMPAMENTO", "ARARINHA", "BALNEARIO", "BALNEÁRIO"}
seen = set()
for l, p in sorted(zip(LOC, pts_base), key=lambda z: -z[0]["eleitores"]):
    b = "SEDE" if l["bairro"].upper() in SEDE else l["bairro"]
    if b not in seen:
        seen.add(b); p["label"] = "Sede (Centro e bairros)" if b == "SEDE" else b.title()

# líder de votos para vereador por bairro (2024)
lid = R["lider_por_bairro_2024"]
URB = {"CENTRO", "EMPRÉSTIMOS", "PEDREIRA", "ACAMPAMENTO DNOCS", "ARARINHA", "BALNEÁRIO"}
URNA = {"ROSA CANDIDA DE OLIVEIRA XIMENES": ("Rosa Paulino", OPO), "WANDERSON LUCAS RODRIGUES DE SOUSA": ("Lucas da Célia", OPO),
        "GONÇALO FARIAS DE OLIVEIRA": ("Gonçalinho", SIT), "RAIMUNDO WANDSON GOMES FERREIRA": ("Wandson Gomes", OPO),
        "DJANDIRA VERAS CARNEIRO DE OLIVEIRA": ("Djinha", SIT), "ANCHIETA ARAGAO MACEDO": ("Anchieta", SIT),
        "FRANCISCO REGIO NOBRE XIMENES": ("Regio Ximenes", SIT)}
coords = {c["bairro"]: c for c in R["coords_bairros"]}
pts_lider = []
for x in lid:
    b = x["bairro"]
    if b not in coords: continue
    nm, col = URNA.get(x["NM_VOTAVEL"], (x["NM_VOTAVEL"].title()[:18], GREY))
    sede = b in URB
    pts_lider.append(dict(lat=coords[b]["lat"], lon=coords[b]["lon"], size=x["QT_VOTOS"] * 3, color=col,
                          label="" if sede else b.title(), val="" if sede else f"{nm} · {x['QT_VOTOS']} votos"))

fin = pd.DataFrame(R["financas"])
def mi(v): return v / 1e6

# ------------------------------------------------------------------ roteiro
C1, C2, C3, C4, C5, C6, C7 = ("Capítulo 1 · 2020", "Capítulo 2 · 2024", "Capítulo 3 · Destaques", "Capítulo 4 · Governo e oposição",
                              "Capítulo 5 · Vereadores", "Capítulo 6 · Nomes de 2028", "Capítulo 7 · O que decide 2028")
TSE = "TSE · dados abertos"
S = []
def cena(scene, falas, visual=""):
    S.append((scene, falas, visual))

cena(Title(kicker="Documentário · Investigação com dados públicos", title="VARJOTA 2028 — O RAIO-X DO PODER",
           sub="Quem cresceu, quem perdeu espaço e quais forças podem decidir a próxima eleição?"),
     ["Varjota tem uma história política marcada por disputas, alianças e lideranças que influenciam os rumos da cidade.",
      "Mas o que realmente mudou entre 2020 e 2024?",
      "Quem saiu fortalecido? Quem perdeu espaço?",
      "E quais nomes podem entrar no centro da disputa de 2028?"],
     "Abertura. Título em serifa, linha dourada, partículas douradas densas. Sugestão de inserir imagem aérea real da cidade.")
cena(MapScene(kicker="A cidade", title="Varjota, Ceará: 15.991 eleitores em 28 locais de votação", points=pts_base,
              legend=["Cada ponto é um local de votação", "Posição: coordenadas oficiais do TSE", "Tamanho: número de eleitores"],
              src="TSE · locais de votação 2024"),
     ["Varjota fica no noroeste do Ceará, na região de Sobral.",
      "São cerca de 18.700 habitantes, segundo a estimativa oficial usada pelo Tesouro Nacional, e 15.991 eleitores aptos em 2026.",
      "Cada ponto que você vê é um local de votação, posicionado pelas coordenadas oficiais do TSE.",
      "A maior parte do eleitorado está na sede: Centro, Empréstimos, Acampamento do DNOCS, Pedreira e Ararinha.",
      "Mas os distritos e comunidades rurais, como Croatá dos Martins, Olho d'Água dos Trajanos e Vila Naiara, também pesam na conta."],
     "Mapa abstrato com pontos dourados surgindo; rótulos de bairros. Inserir drone sobre a sede, se houver.")
cena(Bullets(kicker="Método", title="Como este documentário foi feito",
             items=[("FATO", "Números oficiais do TSE e do Tesouro Nacional (SICONFI)"),
                    ("LEITURA", "Interpretação dos números, sempre marcada como leitura"),
                    ("HIPÓTESE", "Possibilidades que ainda precisam de confirmação"),
                    ("NÃO LOCALIZADO", "O que não conseguimos verificar, dito com clareza")], src=""),
     ["Antes de começar, uma regra.",
      "Tudo o que for fato vem de dados oficiais: o Tribunal Superior Eleitoral e o Tesouro Nacional.",
      "Quando for interpretação, vamos chamar de leitura. Quando for possibilidade, de hipótese.",
      "E quando uma informação não puder ser confirmada, vamos dizer isso claramente."],
     "Cartão com etiquetas coloridas FATO / LEITURA / HIPÓTESE / NÃO LOCALIZADO.")

# ---------------- capítulo 1
cena(Chapter(n="Capítulo 1", title="A eleição de 2020", q="O fim de um ciclo de doze anos"),
     ["Capítulo um. A eleição de 2020."], "Cartão de capítulo, partículas fortes, som grave.")
cena(Timeline(chapter=C1, kicker="Antes de 2020", title="Doze anos de MDB na prefeitura",
              events=[("2009–2016", "Rosa Paulino (MDB) governa por dois mandatos", "Fonte: O Povo, 19/11/2020 · confiança média"),
                      ("2017–2020", "Célia Rodrigues (MDB) governa o município", "Fonte: O Povo, 19/11/2020 · confiança média"),
                      ("15/11/2020", "Elmo Monte (PDT) vence e encerra o ciclo do MDB", "Fonte: TSE")], src="O Povo; TSE"),
     ["Para entender 2020, é preciso olhar para trás.",
      "Segundo o jornal O Povo, o MDB comandou Varjota por doze anos.",
      "Rosa Paulino governou por dois mandatos, e depois veio Célia Rodrigues, também do MDB.",
      "Em 2020, Rosa Paulino tentou voltar à prefeitura.",
      "Do outro lado estava Elmo Monte, empresário, pelo PDT."],
     "Linha do tempo vertical dourada, eventos surgindo em sequência.")
cena(BigNum(chapter=C1, kicker="Comparecimento 2020", title="Quem foi às urnas",
            items=[dict(v=16437, label="eleitores aptos"), dict(v=13726, label="compareceram", note="83,5% do eleitorado"),
                   dict(v=2711, label="abstenções", color=GREY), dict(v=420, label="brancos e nulos para prefeito", color=GREY)], src=TSE),
     ["Em 2020, Varjota tinha 16.437 eleitores aptos.",
      "13.726 foram votar. O comparecimento foi de 83,5%.",
      "2.711 eleitores se abstiveram, e houve 420 votos brancos e nulos para prefeito."],
     "Contadores numéricos subindo até o valor.")
cena(Duel(chapter=C1, kicker="Prefeito 2020", title="Uma disputa de dois grupos",
          rows=[dict(ano="2020", a=dict(nome="ELMO MONTE", partido="PDT", votos=7068, pct=53.1),
                     b=dict(nome="ROSA PAULINO", partido="MDB", votos=6238, pct=46.9),
                     nota="Coligações: PSB/PDT/PT/PTB × PL/MDB/PSL · margem de 830 votos")], src=TSE),
     ["O resultado foi apertado.",
      "Elmo Monte, com a coligação de PSB, PDT, PT e PTB, fez 7.068 votos: 53,1% dos válidos.",
      "Rosa Paulino, com PL, MDB e PSL, fez 6.238 votos: 46,9%.",
      "A diferença foi de apenas 830 votos.",
      "A vice eleita foi Alessandra Araújo Pinheiro, conhecida como Loura do Povo. Guarde esse nome."],
     "Barra dividida marfim (situação) × azul aço (oposição), linha de 50%.")
cena(VBars(chapter=C1, kicker="Câmara 2020 · quociente eleitoral = 1.199 votos", title="Como as 11 cadeiras foram divididas",
           items=[dict(label="MDB", v=5348, sub="5 cadeiras", color=OPO), dict(label="PDT", v=4066, sub="4 cadeiras", color=SIT),
                  dict(label="PT", v=1944, sub="1 cadeira", color=SIT), dict(label="PL", v=1826, sub="1 cadeira", color=OPO)],
           hlines=[(1199 * k, f"{k}× QE") for k in range(1, 5)], src=TSE),
     ["Na Câmara, a conta é outra.",
      "O quociente eleitoral, que é o total de votos válidos dividido por onze cadeiras, ficou em 1.199 votos.",
      "O MDB fez 5.348 votos e cinco cadeiras. O PDT, 4.066 e quatro. PT e PL fizeram uma cada.",
      "Um detalhe: o PT ficou a apenas 90 votos de tirar a última cadeira do PDT."],
     "Barras verticais crescendo; linhas tracejadas a cada múltiplo do quociente.")
cena(Parliament(chapter=C1, kicker="O equilíbrio de 2020", title="O prefeito eleito começou em minoria na Câmara",
                panels=[("2020", [("PDT", SIT)] * 4 + [("PT", SIT)] + [("MDB", OPO)] * 5 + [("PL", OPO)])], src=TSE),
     ["O resultado político foi curioso.",
      "O prefeito eleito começou o mandato com cinco vereadores aliados.",
      "A oposição, com MDB e PL, tinha seis. Era maioria, ao menos no papel."],
     "Hemiciclo de 11 cadeiras surgindo uma a uma.")
cena(HBars(chapter=C1, kicker="Os mais votados de 2020", title="Vereadores eleitos",
           items=[dict(label=n, v=v, color=c, tag=t) for n, v, c, t in [
               ("Roberto do Garrone · PT", 835, SIT, ""), ("Antunino Martins · MDB", 818, OPO, ""), ("Gonçalinho · PDT", 784, SIT, ""),
               ("Molim · MDB", 769, OPO, ""), ("Jô do Silvino · MDB", 737, OPO, ""), ("Regio Ximenes · PDT", 726, SIT, ""),
               ("Anchieta · MDB", 575, OPO, ""), ("Aristeu Linhares · PDT", 562, SIT, ""), ("Djinha · PDT", 539, SIT, "média"),
               ("Edgar Procópio · PL", 522, OPO, ""), ("Marcos Cesar · MDB", 465, OPO, "média")]], label_w=560, src=TSE),
     ["Estes foram os onze eleitos em 2020.",
      "O mais votado foi Roberto do Garrone, do PT, com 835 votos.",
      "Logo atrás, três nomes do MDB: Antunino Martins, Molim e Jô do Silvino.",
      "Repare nesses nomes da oposição. Quatro anos depois, nenhum deles estaria na urna."],
     "Ranking horizontal animado; marfim = base do prefeito, azul = oposição.")
cena(Bullets(chapter=C1, kicker="2020 · o que veio depois", title="Questionamentos documentados",
             items=[("FATO", "MP Eleitoral pediu a cassação de Elmo e da vice por abuso de poder econômico e compra de votos"),
                    ("NÃO LOCALIZADO", "Desfecho do processo. Elmo concluiu o mandato e foi reeleito"),
                    ("FATO", "TRE-CE manteve multa a Rosa Paulino por aglomeração na campanha de 2020 (set/2021)"),
                    ("FATO", "fev/2021: MPCE deflagra operação sobre contratos de coleta de lixo de 2016 a 2020"),
                    ("NÃO LOCALIZADO", "Resultado da operação; não há condenação localizada")], src="MPCE; O Povo (16/09/2021)"),
     ["A eleição de 2020 também deixou processos.",
      "O Ministério Público Eleitoral pediu a cassação do prefeito e da vice eleitos, por abuso de poder econômico e compra de votos.",
      "Não localizamos o desfecho desse processo. O fato verificável é que Elmo concluiu o mandato e se reelegeu.",
      "Do outro lado, o TRE do Ceará manteve uma multa a Rosa Paulino por aglomeração durante a campanha.",
      "E em fevereiro de 2021, o Ministério Público do Ceará deflagrou uma operação sobre contratos de coleta de lixo firmados entre 2016 e 2020.",
      "Pedido, denúncia e investigação não são condenação. Não localizamos decisão final em nenhum desses casos."],
     "Cartão com etiquetas; tom sóbrio, sem música de tensão exagerada.")

# ---------------- capítulo 2
cena(Chapter(n="Capítulo 2", title="A mudança de 2024", q="O que o resultado revelou sobre o eleitor de Varjota?"),
     ["Capítulo dois. A mudança de 2024."], "Transição com explosão suave de partículas.")
cena(Duel(chapter=C2, kicker="Prefeito · 2020 × 2024", title="De vitória apertada a vitória larga",
          rows=[dict(ano="2020", a=dict(nome="ELMO MONTE", partido="PDT", votos=7068, pct=53.1),
                     b=dict(nome="ROSA PAULINO", partido="MDB", votos=6238, pct=46.9), nota="Margem: 830 votos"),
                dict(ano="2024", a=dict(nome="ELMO MONTE", partido="PSB", votos=8914, pct=64.3),
                     b=dict(nome="SILVINO OLIVEIRA", partido="MDB", votos=4955, pct=35.7), nota="Margem: 3.959 votos")], src=TSE),
     ["Em 2024, Elmo Monte disputou a reeleição, agora pelo PSB.",
      "Fez 8.914 votos, 64,3% dos válidos.",
      "O adversário, Silvino Oliveira, do MDB, fez 4.955 votos, 35,7%.",
      "A margem saltou de 830 para 3.959 votos.",
      "Elmo ganhou 1.846 votos novos. A oposição perdeu 1.283."],
     "As duas eleições lado a lado; a barra de 2024 cresce depois da de 2020.")
cena(Bullets(chapter=C2, kicker="Entrelinhas", title="Trocou de partido, trocou de vice — e cresceu",
             items=[("FATO", "2020: Elmo (PDT) e vice Loura do Povo (PDT)"),
                    ("FATO", "2024: Loura do Povo é candidata a vice na chapa adversária, pelo PP"),
                    ("FATO", "2024: novo vice, Dr. Erivaldo Mororó (Republicanos); entram Republicanos e União"),
                    ("FATO", "A oposição perde o PL e fica com PP e MDB"),
                    ("LEITURA", "A troca PDT → PSB acompanha o movimento estadual do grupo de Cid Gomes")], src="TSE; Diário do Nordeste"),
     ["Aqui está a primeira entrelinha.",
      "A vice eleita em 2020, Loura do Povo, rompeu com o grupo e foi candidata a vice na chapa adversária, pelo PP.",
      "Normalmente, isso enfraquece um prefeito. Aconteceu o contrário.",
      "Elmo trocou o PDT pelo PSB, acompanhando o movimento estadual do grupo de Cid Gomes, e ampliou a coligação com Republicanos e União.",
      "O novo vice foi o médico Erivaldo Mororó, do Republicanos."],
     "Cartão com etiquetas; destaque visual na palavra 'cresceu'.")
cena(VBars(chapter=C2, kicker="Comparecimento", title="A eleição municipal mobiliza mais",
           items=[dict(label="2020", label2="municipal", v=83.51, dec=1, suf="%", color=SIT),
                  dict(label="2022", label2="geral", v=76.71, dec=1, suf="%", color=DIM),
                  dict(label="2024", label2="municipal", v=88.66, dec=1, suf="%", color=GOLD),
                  dict(label="2026", label2="geral", v=84.12, dec=1, suf="%", color=DIM)], vmax=100, src=TSE),
     ["Outro sinal: o comparecimento.",
      "Na eleição municipal de 2024, 88,7% dos eleitores foram votar, contra 83,5% em 2020.",
      "A abstenção caiu em 872 pessoas, mesmo com 224 eleitores a menos no cadastro.",
      "Leitura: uma eleição desequilibrada não costuma atrair mais eleitores. Isso sugere mobilização organizada, e não apenas entusiasmo espontâneo."],
     "Barras verticais; 2024 em dourado.")
cena(MapScene(chapter=C2, kicker="Geografia do voto", title="Onde Elmo mais cresceu entre 2020 e 2024", points=pts_swing,
              legend=["Cor: variação do % de Elmo por local", "Dourado forte = maior avanço", "Cinza = menor avanço",
                      "2020: oposição venceu em 7 de 30 locais", "2024: em nenhum dos 28"], src="TSE · votação por seção e locais"),
     ["Para onde foram esses votos? O mapa responde.",
      "Elmo cresceu em todos os locais de votação comparáveis.",
      "Em 2020, a oposição venceu em sete locais. Em 2024, em nenhum.",
      "As maiores viradas aconteceram na zona rural: no Jatobá, quase 30 pontos; no Angelim, 24 pontos.",
      "Os menores avanços também foram rurais: Transval, Olho d'Água dos Trajanos e Várzea da Palha, com menos de seis pontos.",
      "Leitura: é nesses lugares que a oposição ainda resiste, e é por eles que qualquer estratégia para 2028 deve começar."],
     "Mapa: pontos com intensidade dourada pela variação; rótulos nos extremos.")
cena(HBars(chapter=C2, kicker="Sede × zona rural · % de Elmo", title="O avanço foi parecido na cidade e no campo",
           items=[dict(label="Sede urbana · 2020", v=53.8, dec=1, suf="%", color=DIM), dict(label="Sede urbana · 2024", v=65.1, dec=1, suf="%", color=GOLD),
                  dict(label="Rural e distritos · 2020", v=50.9, dec=1, suf="%", color=DIM), dict(label="Rural e distritos · 2024", v=61.3, dec=1, suf="%", color=GOLD)],
           vmax=100, line=(50, "50%"), label_w=520, src="TSE · classificação de bairros pelo cadastro de locais"),
     ["Separando a sede da zona rural, o avanço foi parecido.",
      "Na sede, Elmo foi de 53,8 para 65,1%. Na zona rural e nos distritos, de 50,9 para 61,3%.",
      "Ou seja: o crescimento não foi localizado. Foi generalizado."],
     "Barras horizontais pareadas.")
cena(VBars(chapter=C2, kicker="Câmara 2024 · quociente eleitoral = 1.252 votos", title="Três listas, onze cadeiras",
           items=[dict(label="PSB", v=6403, sub="5 cadeiras", color=SIT), dict(label="Fed. PT/PCdoB/PV", v=3386, sub="3 cadeiras", color=SIT),
                  dict(label="MDB", v=3979, sub="3 cadeiras", color=OPO)],
           hlines=[(1252 * k, f"{k}× QE") for k in range(1, 6)], src=TSE),
     ["Na Câmara, o quociente subiu para 1.252 votos.",
      "Só três listas disputaram, contra quatro em 2020.",
      "O PSB fez 6.403 votos e cinco cadeiras. A federação do PT, 3.386 votos e três. O MDB, 3.979 votos e três.",
      "A última cadeira foi para a federação do PT, por maior média. Faltaram 371 votos para o PSB fazer a sexta."],
     "Barras verticais com múltiplos do quociente.")
cena(Parliament(chapter=C2, kicker="O novo equilíbrio", title="De minoria a supermaioria",
                panels=[("2020", [("PDT", SIT)] * 4 + [("PT", SIT)] + [("MDB", OPO)] * 5 + [("PL", OPO)]),
                        ("2024", [("PSB", SIT)] * 5 + [("PT", SIT)] * 3 + [("MDB", OPO)] * 3)], src=TSE),
     ["O equilíbrio mudou completamente.",
      "De cinco contra seis em 2020, a base do prefeito passou a oito contra três.",
      "A oposição, que tinha maioria, ficou com três vereadores, todos do MDB."],
     "Dois hemiciclos, 2020 e 2024.")
cena(Bullets(chapter=C2, kicker="Entrelinhas", title="Por que a oposição encolheu na Câmara?",
             items=[("FATO", "Os 5 eleitos de 2020 que não concorreram em 2024 eram todos da oposição"),
                    ("FATO", "Antunino, Molim, Jô do Silvino, Marcos Cesar e Edgar Procópio somavam 3.311 votos"),
                    ("FATO", "Anchieta deixou o MDB, foi para o PSB e não se reelegeu"),
                    ("FATO", "O PL se desfez: Adriano Paiva e Irmã Moça foram para o MDB; Irmã Fábia, para o PT"),
                    ("LEITURA", "A oposição perdeu seus puxadores de voto antes mesmo da campanha")], src=TSE),
     ["Por que a oposição encolheu tanto?",
      "Os cinco vereadores eleitos em 2020 que não concorreram em 2024 eram todos da oposição.",
      "Juntos, eles tinham feito 3.311 votos.",
      "Anchieta saiu do MDB, foi para o PSB e não se reelegeu.",
      "E o PL deixou de existir como lista local: seus candidatos foram para o MDB e para o PT.",
      "Leitura: a oposição perdeu os seus puxadores de voto antes mesmo de a campanha começar."],
     "Cartão com etiquetas.")

# ---------------- capítulo 3
cena(Chapter(n="Capítulo 3", title="Quem são os destaques?", q="Votos são um critério. Não o único."),
     ["Capítulo três. Quem são os destaques?"], "Cartão de capítulo.")
cena(HBars(chapter=C3, kicker="Destaque eleitoral · maior votação para vereador em 2024", title="O maior voto pessoal da cidade está na oposição",
           items=[dict(label=n, v=v, color=c) for n, v, c in [
               ("Rosa Paulino · MDB", 1774, OPO), ("Eudes Mesquita · PSB", 992, SIT), ("Gonçalinho · PSB", 915, SIT), ("Regio Ximenes · PSB", 884, SIT),
               ("Patrícia Ximenes · PT", 847, SIT), ("Lucas da Célia · MDB", 834, OPO), ("Roberto do Garrone · PT", 783, SIT),
               ("Fransquinha do Edvard · PSB", 682, SIT), ("Djinha · PSB", 672, SIT), ("Professora Inara · PT", 599, SIT),
               ("Eudes do Croatá · MDB", 280, OPO)]], label_w=560, src=TSE),
     ["Primeiro critério: votos.",
      "A vereadora mais votada de 2024 foi Rosa Paulino, do MDB, com 1.774 votos.",
      "É quase o dobro do segundo colocado, Eudes Mesquita, do PSB, com 992.",
      "Rosa sozinha fez 45% de todos os votos do MDB para vereador.",
      "Leitura: o maior capital eleitoral individual da cidade está na oposição. E isso também revela uma dependência."],
     "Ranking com Rosa Paulino em destaque.")
cena(HBars(chapter=C3, kicker="Destaque de crescimento · candidatos que disputaram 2020 e 2024", title="Quem cresceu e quem perdeu votos",
           items=[dict(label=n, v=abs(v), vl=f"{v:+d}%", color=GOLD if v > 0 else GREY, tag=t) for n, v, t in [
               ("Patrícia Ximenes · PT", 110, "403 → 847"), ("Fransquinha do Edvard · PDT→PSB", 65, "414 → 682"),
               ("Djinha · PDT→PSB", 25, "539 → 672"), ("Regio Ximenes · PDT→PSB", 22, "726 → 884"), ("Gonçalinho · PDT→PSB", 17, "784 → 915"),
               ("Roberto do Garrone · PT", -6, "835 → 783"), ("Anchieta · MDB→PSB", -16, "575 → 485"), ("Carlim do Tatá · MDB→PT", -22, "433 → 339"),
               ("Prof. Lyderson · MDB→PSB", -25, "226 → 169"), ("Irmã Fábia · PL→PT", -30, "208 → 146")]], vmax=120, label_w=640, src=TSE),
     ["Segundo critério: crescimento entre uma eleição e outra.",
      "O maior crescimento foi de Patrícia Ximenes, do PT: de 403 para 847 votos, mais do que o dobro. Saiu da suplência para a Câmara.",
      "Fransquinha do Edvard cresceu 65%. Djinha, Regio e Gonçalinho cresceram entre 17 e 25%.",
      "Agora repare no fim da lista. Anchieta, Carlim, Lyderson e Irmã Fábia trocaram a oposição pela base do governo.",
      "Os quatro perderam votos, entre 16 e 30%.",
      "Leitura: aderir ao grupo vencedor não garantiu voto individual."],
     "Barras douradas (crescimento) e cinzas (queda), com antes → depois.")
cena(Bullets(chapter=C3, kicker="Destaques políticos e novas lideranças", title="Outros critérios além do voto",
             items=[("FATO", "Elmo Monte: prefeito, +1.846 votos; levou o grupo inteiro do PDT ao PSB sem perder ninguém na Câmara"),
                    ("FATO", "Estreantes eleitos em 2024: Eudes Mesquita (992), Lucas da Célia (834), Professora Inara (599)"),
                    ("FATO", "Lucas da Célia, 24 anos na eleição, fez 51% dos seus votos no bairro Empréstimos"),
                    ("NÃO LOCALIZADO", "Produção legislativa (projetos, requerimentos, presença): portal da Câmara não acessível nesta pesquisa"),
                    ("NÃO LOCALIZADO", "Indicadores por secretaria e gestor")], src="TSE"),
     ["Terceiro critério: influência e capacidade de articulação.",
      "O dado mais forte é o do prefeito: além de crescer 1.846 votos, Elmo levou toda a bancada do PDT para o PSB sem perder nenhum vereador.",
      "Entre as novas lideranças, três estreantes chegaram à Câmara: Eudes Mesquita, Lucas da Célia e Professora Inara.",
      "Lucas da Célia, o mais jovem dos eleitos, concentrou mais da metade dos seus votos em um único bairro, o Empréstimos.",
      "E um aviso importante: não conseguimos acessar os registros da Câmara Municipal.",
      "Por isso, este documentário não ranqueia a atuação legislativa dos vereadores. Essa informação não foi localizada."],
     "Cartão com etiquetas; deixar explícito o que falta.")

# ---------------- capítulo 4
cena(Chapter(n="Capítulo 4", title="O governo e a oposição", q="O que os números da prefeitura mostram?"),
     ["Capítulo quatro. O governo e a oposição."], "Cartão de capítulo.")
cena(Lines(chapter=C4, kicker="Finanças · valores nominais em R$ milhões (empenhados)", title="O orçamento mais que dobrou entre 2020 e 2024",
           x=list(fin.ano), vmax=160, yfmt=lambda v: f"{v:.0f} mi", vfmt=lambda v: f"{v:.0f}", labels_at=[1, 5],
           series=[dict(name="Receita", v=[mi(x) for x in fin.receita_liquida], color=GOLD_L),
                   dict(name="Pessoal", v=[mi(x) for x in fin.pessoal], color=SIT),
                   dict(name="Investimentos", v=[mi(x) for x in fin.investimentos], color=OPO)],
           src="Tesouro Nacional · SICONFI · Balanço Anual (DCA)"),
     ["Agora, a administração. E aqui os números vêm do Tesouro Nacional.",
      "A receita do município foi de 61 milhões de reais em 2020 para 142 milhões em 2024.",
      "Mesmo descontando a inflação do período, de cerca de 28% pelo IPCA, a receita cresceu cerca de 80% em termos reais.",
      "Mas atenção: Varjota arrecada por conta própria apenas cerca de 3,5% da sua receita. O resto são transferências do estado e da União.",
      "Leitura: boa parte do crescimento veio de fora, e não depende só da gestão local."],
     "Gráfico de linhas desenhando-se ano a ano.")
cena(VBars(chapter=C4, kicker="Investimentos · R$ milhões empenhados por ano", title="O investimento disparou no ano da eleição",
           items=[dict(label=str(int(a)), v=mi(v), dec=1, suf=" mi", color=GOLD if int(a) == 2024 else (SIT if int(a) >= 2021 else DIM))
                  for a, v in zip(fin.ano, fin.investimentos)], src="Tesouro Nacional · SICONFI · DCA"),
     ["Um gráfico chama atenção: o investimento.",
      "Em 2021, primeiro ano do mandato, foram 2,7 milhões de reais. Em 2024, ano eleitoral, 24,5 milhões, 17,6% de toda a despesa.",
      "Em 2025, o investimento recuou para 17,7 milhões.",
      "É um padrão comum na política brasileira: obras se concentram no ano da eleição.",
      "Leitura: isso ajuda a explicar a mobilização de 2024. Mas obra entregue também é resultado, e o eleitor pode ter reconhecido isso."],
     "Barras verticais; 2024 em dourado.")
cena(Table(chapter=C4, kicker="Despesa por área · R$ milhões empenhados", title="Para onde foi o dinheiro",
           header=["Área", "2020", "2022", "2024", "2025"],
           rows=[[n] + [fmt(mi(fin.loc[fin.ano == a, k].iloc[0]), 1) for a in (2020, 2022, 2024, 2025)] for n, k in
                 [("Educação", "educacao"), ("Saúde", "saude"), ("Urbanismo", "urbanismo"), ("Administração", "administracao"),
                  ("Assistência social", "assistencia_social"), ("Pessoal (todas as áreas)", "pessoal")]] +
                [["Pessoal / despesa total"] + [fmt(fin.loc[fin.ano == a, 'pct_pessoal'].iloc[0], 1) + "%" for a in (2020, 2022, 2024, 2025)] + [True]],
           widths=[.36, .16, .16, .16, .16], note="Em 2025, a despesa com pessoal foi 44,3% da receita corrente líquida ajustada, abaixo do limite de 54% da LRF (RGF, 3º quadrimestre).",
           src="Tesouro Nacional · SICONFI · DCA e RGF"),
     ["Para onde foi o dinheiro?",
      "Educação é a maior área: de 19 milhões em 2020 para 58 milhões em 2024 e 67 milhões em 2025.",
      "Saúde foi de 17 para 37 milhões.",
      "O gasto com pessoal cresceu em reais, mas caiu como proporção da despesa: de quase 50% para cerca de 40%.",
      "Em 2025, a despesa com pessoal ficou em 44,3% da receita corrente líquida, abaixo do limite de 54% da Lei de Responsabilidade Fiscal."],
     "Tabela com linhas surgindo; última linha destacada.")
cena(Bullets(chapter=C4, kicker="Críticas e questionamentos documentados", title="O que está registrado em órgãos oficiais",
             items=[("FATO", "19/08/2025: TAC entre MPCE e Prefeitura para melhorar a infraestrutura das UBS"),
                    ("FATO", "Justiça, a pedido do MP, determinou que Prefeitura e Cagece aprovem e executem o Plano Municipal de Saneamento"),
                    ("NÃO LOCALIZADO", "Data da decisão sobre saneamento e cumprimento do TAC das UBS"),
                    ("NÃO LOCALIZADO", "Inclusão de Varjota no alerta do TCE-CE a 84 prefeituras (set/2025)"),
                    ("NÃO LOCALIZADO", "IDEB municipal recente, cobertura da atenção básica, obras atrasadas")], src="MPCE; O Povo"),
     ["E as críticas? Aqui, só o que está documentado.",
      "Em agosto de 2025, o Ministério Público e a prefeitura assinaram um termo de ajustamento de conduta para melhorar a estrutura das unidades básicas de saúde.",
      "Também há uma decisão judicial, a pedido do Ministério Público, para que a prefeitura e a Cagece aprovem e executem o plano municipal de saneamento.",
      "Um termo de ajustamento é um acordo para corrigir problemas. Não é condenação.",
      "Não conseguimos confirmar outros pontos, como o IDEB recente do município ou a situação das obras. Essas são as principais lacunas desta investigação."],
     "Cartão sóbrio com etiquetas; nada de música dramática.")
cena(Quote(chapter=C4, kicker="A ruptura de 2026 · fonte única: blog local (set/2026)",
           text="O vice-prefeito Erivaldo Mororó anunciou o rompimento com Elmo Monte. Disse que não vai para a oposição.",
           who="Segundo o Blog do Amaury Alencar",
           note="Motivos relatados: apoio de Mororó a Ciro Gomes em 2026, dificuldade de acesso ao prefeito e omissão do seu nome em placas de inauguração. Não localizamos resposta oficial da prefeitura. Confiança média.",
           src="Blog do Amaury Alencar (set/2026)"),
     ["Agora, um fato novo, de setembro de 2026.",
      "Segundo um blog local, o vice-prefeito Erivaldo Mororó anunciou o rompimento político com o prefeito Elmo Monte.",
      "Entre os motivos relatados estão o apoio de Mororó a Ciro Gomes na eleição para governador, a dificuldade de acesso ao prefeito e a ausência do seu nome em placas de inauguração.",
      "Ele teria dito que não vai para a oposição.",
      "É uma fonte única, e não localizamos resposta da prefeitura. Mas, se confirmado, é o segundo vice consecutivo a se afastar de Elmo."],
     "Citação em serifa; etiqueta de confiança média.")
cena(HBars(chapter=C4, kicker="Eleições gerais de 2026 em Varjota", title="Para governador, Varjota votou contra o eleito",
           items=[dict(label="Ciro Gomes · PSDB", v=58.1, dec=1, suf="%", color=GOLD_L), dict(label="Elmano de Freitas · PT", v=41.6, dec=1, suf="%", color=SIT),
                  dict(label="Senado · Capitão Wagner", v=26.6, dec=1, suf="%", color=DIM), dict(label="Senado · Cid Gomes", v=25.3, dec=1, suf="%", color=DIM),
                  dict(label="Senado · Alcides Fernandes", v=24.6, dec=1, suf="%", color=DIM), dict(label="Senado · Luizianne", v=23.2, dec=1, suf="%", color=DIM),
                  dict(label="Presidente 2º t. · Lula", v=66.5, dec=1, suf="%", color=SIT), dict(label="Presidente 2º t. · Flávio Bolsonaro", v=33.5, dec=1, suf="%", color=DIM)],
           vmax=100, label_w=600, src="TSE · eleições 2026"),
     ["E isso conversa com o resultado de 2026.",
      "Para governador, Ciro Gomes, pelo PSDB, venceu em Varjota com 58,1%. Elmano de Freitas, do PT, reeleito no estado, teve 41,6%.",
      "Para o Senado, o voto se dividiu quase igualmente entre quatro nomes. Cid Gomes, referência estadual do PSB, ficou em segundo no município.",
      "Para presidente, Lula venceu com 66,5%, seis pontos a menos que em 2022.",
      "Leitura: o voto local não se transfere automaticamente para as disputas estaduais. E a divisão entre Ciro e o PT pode chegar à eleição municipal."],
     "Barras horizontais; Ciro em destaque dourado.")
cena(Table(chapter=C4, kicker="Deputados mais votados em Varjota", title="Os dois blocos locais aparecem no voto para deputado",
           header=["Cargo", "2022", "2026"],
           rows=[["Dep. estadual · 1º", "Lia Gomes (PDT) · 34,3%", "Lia Gomes (PSB) · 30,1%"],
                 ["Dep. estadual · 2º", "Danniel Oliveira (MDB) · 22,2%", "Danniel Oliveira (MDB) · 22,1%"],
                 ["Dep. federal · 1º", "Leônidas Cristino (PDT) · 33,8%", "Yury do Paredão (MDB) · 19,0%"],
                 ["Dep. federal · 2º", "Eunício (MDB) · 26,6%", "Denis Bezerra (PSB) · 16,7%"]],
           widths=[.26, .37, .37], fs=30, note="Em 2026, a base pulverizou o voto federal entre vários nomes do PSB (≈33% somados), enquanto o MDB concentrou em um.",
           src="TSE · eleições 2022 e 2026"),
     ["No voto para deputado, os dois blocos locais aparecem com clareza.",
      "Lia Gomes, ligada ao grupo do prefeito, e Danniel Oliveira, do MDB, repetiram praticamente os mesmos percentuais em 2022 e 2026.",
      "Para deputado federal, o MDB concentrou o voto em um nome, Yury do Paredão, o mais votado em 2026.",
      "Já a base dividiu o voto entre vários candidatos do PSB.",
      "Leitura: a oposição age concentrada. A base tem muitos aliados para atender."],
     "Tabela comparativa.")

# ---------------- capítulo 5
cena(Chapter(n="Capítulo 5", title="Os vereadores", q="De onde vem o voto de cada um?"),
     ["Capítulo cinco. Os vereadores."], "Cartão de capítulo.")
cena(MapScene(chapter=C5, kicker="Quem lidera o voto para vereador em cada bairro · 2024", title="O mapa dos redutos", points=pts_lider,
              legend=["Ponto: candidato mais votado no bairro", "Marfim = base do prefeito · Azul = oposição",
                      "Sede: Rosa Paulino lidera em Centro,", "Pedreira, Acampamento DNOCS, Ararinha", "e Balneário; Lucas da Célia, no Empréstimos",
                      "Rosa lidera em 6 dos 13 bairros"], src="TSE · votação por seção, agregada por bairro"),
     ["Cruzando o voto de cada seção com o bairro do local de votação, dá para ver os redutos.",
      "Rosa Paulino lidera o voto para vereador em seis dos treze bairros, incluindo o Centro, a Pedreira e o Acampamento do DNOCS.",
      "Lucas da Célia lidera no Empréstimos. Wandson Gomes, também do MDB, na Vila Naiara.",
      "Já o Croatá dos Martins é um caso à parte: ali, Gonçalinho, Eudes Mesquita e Eudes do Croatá somam cerca de 80% dos votos para vereador.",
      "Leitura: o Croatá funciona como um distrito que elege três vereadores."],
     "Mapa: líder por bairro, cor pela posição política.")
cena(Bullets(chapter=C5, kicker="O efeito lista", title="Por que 280 votos elegeram e 553 não",
             items=[("FATO", "Eudes do Croatá (MDB) foi eleito com 280 votos"),
                    ("FATO", "Aristeu Linhares (PSB) ficou de fora com 553; Anchieta, com 485"),
                    ("FATO", "Cadeira mais barata: Federação do PT, 1.129 votos; mais cara: MDB, 1.326"),
                    ("FATO", "Em 2020 a última cadeira foi decidida por 90 votos; em 2024, por 371"),
                    ("LEITURA", "Para 2028, distribuir bem os candidatos entre as listas vale uma cadeira")], src=TSE),
     ["Um dado que confunde muita gente.",
      "Eudes do Croatá, do MDB, se elegeu com 280 votos. Aristeu Linhares, do PSB, ficou de fora com 553.",
      "Isso acontece porque, no sistema proporcional, o voto do partido decide quantas cadeiras cada lista tem.",
      "Dentro de uma lista forte, como a do PSB, a disputa individual é mais dura.",
      "Leitura: em 2028, quem organizar melhor as listas pode ganhar uma cadeira sem ganhar um único voto a mais."],
     "Cartão com etiquetas.")
cena(Table(chapter=C5, kicker="Quem pode buscar a reeleição · base: dados de 2024", title="Os 11 vereadores em exercício",
           header=["Vereador(a)", "Partido", "Votos 2024", "Histórico"],
           rows=[["Rosa Paulino", "MDB", "1.774", "Ex-prefeita · 46,9% para prefeita em 2020"],
                 ["Eudes Mesquita", "PSB", "992", "Estreante"], ["Gonçalinho", "PSB", "915", "Reeleito · +17%"],
                 ["Regio Ximenes", "PSB", "884", "Reeleito · +22%"], ["Patrícia Ximenes", "PT", "847", "Suplente em 2020 · +110%"],
                 ["Lucas da Célia", "MDB", "834", "Estreante"], ["Roberto do Garrone", "PT", "783", "Reeleito · −6%"],
                 ["Fransquinha do Edvard", "PSB", "682", "Suplente em 2020 · +65%"], ["Djinha", "PSB", "672", "Reeleita · +25%"],
                 ["Professora Inara", "PT", "599", "Estreante · eleita por média"], ["Eudes do Croatá", "MDB", "280", "Suplente em 2020 · −4%"]],
           widths=[.27, .12, .15, .46], fs=28, note="Atuação legislativa (projetos, requerimentos, presença): INFORMAÇÃO NÃO LOCALIZADA.",
           src=TSE),
     ["Estes são os onze vereadores em exercício, segundo o resultado oficial de 2024.",
      "Quatro foram reeleitos. Três eram suplentes em 2020. Três são estreantes. E uma é ex-prefeita.",
      "Todos, em princípio, podem buscar a reeleição em 2028.",
      "Quem chega mais forte? Pelos números, Rosa Paulino, Eudes Mesquita e os vereadores que cresceram entre as eleições.",
      "Quem pode ter mais dificuldade? Pelos números, quem depende de uma lista muito disputada, como a do PSB, ou quem foi eleito com votação baixa, como Eudes do Croatá."],
     "Tabela com linhas surgindo uma a uma.")

# ---------------- capítulo 6
cena(Chapter(n="Capítulo 6", title="Os possíveis nomes de 2028", q="Nenhuma candidatura a prefeito foi declarada publicamente até aqui"),
     ["Capítulo seis. Os possíveis nomes de 2028."], "Cartão de capítulo.")
cena(Bullets(chapter=C6, kicker="Regra do jogo", title="Elmo Monte não pode disputar a prefeitura em 2028",
             items=[("FATO", "Eleito em 2020 e reeleito em 2024: dois mandatos consecutivos"),
                    ("FATO", "A sucessão em 2028 é obrigatoriamente aberta"),
                    ("NÃO LOCALIZADO", "Candidatura declarada a prefeito de qualquer nome (Grupo 1)"),
                    ("LEITURA", "Os nomes a seguir aparecem por histórico eleitoral, não por anúncio")], src="TSE; Constituição Federal, art. 14, §5º"),
     ["Começando pelo mais importante: Elmo Monte não pode disputar a prefeitura em 2028.",
      "Ele foi eleito em 2020 e reeleito em 2024. A sucessão será aberta.",
      "E é preciso dizer com clareza: até a data desta pesquisa, não localizamos nenhuma candidatura a prefeito declarada publicamente.",
      "Os nomes que vamos mostrar aparecem por histórico eleitoral e posição política. Não por anúncio."],
     "Cartão; destaque para 'NÃO LOCALIZADO'.")
cena(Table(chapter=C6, kicker="Mapa de possibilidades · classificação por nível de evidência", title="Quem entra naturalmente na conversa",
           header=["Nome", "Posição", "Evidência eleitoral", "Grupo"],
           rows=[["Rosa Paulino", "Oposição (MDB)", "Ex-prefeita; 46,9% em 2020; maior voto de 2024", "3 · especulado"],
                 ["Silvino Oliveira", "Oposição (MDB)", "35,7% para prefeito em 2024", "3 · especulado"],
                 ["Erivaldo Mororó", "Vice; rompeu com Elmo (set/2026)", "Sem voto próprio testado", "3 · especulado"],
                 ["Loura do Povo", "Ex-vice; PP em 2024", "Vice em duas chapas opostas", "3 · especulado"],
                 ["Eudes Mesquita", "Base (PSB)", "992 votos; vereador mais votado da base", "3 · especulado"],
                 ["Patrícia Ximenes", "Base (PT)", "+110% entre 2020 e 2024", "3 · especulado"],
                 ["Nome indicado por Elmo", "Base", "A definir", "—"]],
           widths=[.21, .25, .40, .14], fs=26,
           note="Grupo 1 = candidatura declarada · Grupo 2 = sinais públicos concretos · Grupo 3 = nome especulado. Nenhum nome atingiu os Grupos 1 ou 2 nesta pesquisa.",
           src="TSE; Blog do Amaury Alencar"),
     ["Quem entra naturalmente na conversa?",
      "Na oposição, Rosa Paulino: ex-prefeita, 46,9% em 2020 e o maior voto de 2024. E Silvino Oliveira, candidato de 2024.",
      "No campo que se afastou do prefeito, dois vices: Erivaldo Mororó, que anunciou o rompimento em 2026, e Loura do Povo, que já foi vice dos dois lados.",
      "Na base, vereadores que cresceram, como Eudes Mesquita e Patrícia Ximenes, além de quem o prefeito vier a indicar.",
      "Todos estão no grupo três: nomes especulados. Nenhum tem candidatura declarada ou sinais públicos concretos, segundo o que localizamos."],
     "Tabela com classificação por grupo de evidência.")
cena(Table(chapter=C6, kicker="Projeção para a Câmara em 2028", title="O quociente deve ficar perto de 1.200 votos",
           header=["Cenário", "Eleitores aptos", "Votos válidos", "Quociente", "80% do QE"],
           rows=[["Baixo", "15.600", "12.778", "1.162", "930"], ["Central", "15.850", "13.286", "1.208", "967", True],
                 ["Alto", "16.100", "13.727", "1.248", "999"]],
           widths=[.2, .2, .2, .2, .2], note="Premissas: eleitorado em queda (16.757 em 2022 → 15.991 em 2026); comparecimento de 85,5% a 89%; válidos = 95,8% do comparecimento. Até 12 candidatos por partido.",
           src="Projeção própria a partir de dados do TSE"),
     ["E a Câmara?",
      "O eleitorado vem caindo: 16.757 em 2022, 15.991 em 2026.",
      "Projetamos entre 15.600 e 16.100 eleitores em 2028, e um quociente eleitoral entre 1.162 e 1.248 votos.",
      "No cenário central, cerca de 1.208 votos por cadeira.",
      "Para disputar as sobras, um partido vai precisar de algo perto de 970 votos. E cada partido pode lançar até doze candidatos."],
     "Tabela; linha central destacada.")

# ---------------- capítulo 7
cena(Chapter(n="Capítulo 7", title="O que pode decidir 2028?", q="Cinco cenários, nenhum vencedor escolhido"),
     ["Capítulo sete. O que pode decidir 2028?"], "Cartão de capítulo.")
cena(Bullets(chapter=C7, kicker="Cinco cenários", title="Os caminhos possíveis para a sucessão",
             items=[("HIPÓTESE", "1 · Continuidade: a base se une em torno de um sucessor e mantém a coligação de 2024"),
                    ("HIPÓTESE", "2 · Disputa interna: PT, Republicanos ou aliados lançam nomes próprios"),
                    ("HIPÓTESE", "3 · Oposição fortalecida: MDB unifica com PP e PL e aproveita o desgaste de 8 anos"),
                    ("HIPÓTESE", "4 · Terceira força: um nome fora dos grupos tradicionais, possivelmente ligado ao campo de Ciro"),
                    ("HIPÓTESE", "5 · Mudança de alianças: o rearranjo estadual pós-2026 redesenha os grupos locais")], src=""),
     ["Com esses dados, desenhamos cinco cenários. Nenhum deles escolhe vencedor.",
      "Primeiro: continuidade. A base se une em torno de um sucessor e mantém a coligação ampla de 2024.",
      "Segundo: disputa interna. Partidos da base, como PT ou Republicanos, lançam nomes próprios.",
      "Terceiro: oposição fortalecida. O MDB se une a PP e PL e aproveita o desgaste natural de oito anos de governo.",
      "Quarto: uma terceira força, fora dos grupos tradicionais. O voto em Ciro em 2026 mostra que existe eleitor disponível para isso.",
      "E quinto: mudança de alianças. O rearranjo estadual depois de 2026 pode redesenhar os grupos de Varjota."],
     "Cartão com cinco hipóteses.")
cena(Table(chapter=C7, kicker="Câmara 2028 · simulação com quociente central de 1.208", title="Como a Câmara pode ficar",
           header=["Cenário", "Divisão dos votos (%)", "Cadeiras"],
           rows=[["Continuidade", "PSB 45 · PT 25 · MDB 30", "5 · 3 · 3"],
                 ["Fragmentação", "PSB 33 · PT 20 · MDB 25 · Rep 12 · PL 10", "4 · 2 · 3 · 1 · 1"],
                 ["Oposição cresce", "PSB 36 · PT 20 · MDB 38 · PP 6", "4 · 2 · 5 · 0"]],
           widths=[.24, .52, .24], note="Simulações ilustrativas com a regra real do quociente e das sobras; não são pesquisa eleitoral.",
           src="Simulação própria"),
     ["Na Câmara, simulamos três divisões de votos, aplicando a regra real do quociente e das sobras.",
      "Se tudo continuar como em 2024, o placar se repete: oito a três.",
      "Se os aliados lançarem listas próprias, a Câmara fica com cinco partidos, e a base mantém a maioria.",
      "Se a oposição crescer e o MDB chegar a 38% dos votos, ele faz cinco cadeiras e o placar fica seis a cinco.",
      "Estas são simulações, não pesquisa eleitoral."],
     "Tabela.")
cena(Bullets(chapter=C7, kicker="O que observar até 2028", title="As variáveis que podem mudar tudo",
             items=["Quem o prefeito vai apontar como sucessor, e se a base aceita",
                    "Rosa Paulino: prefeitura ou Câmara? A lista do MDB depende dela",
                    "O rompimento do vice Erivaldo Mororó: isolado ou o começo de um grupo?",
                    "Ciro, o PSB de Cid e o PT de Elmano: como o rearranjo estadual chega a Varjota",
                    "As comunidades de menor avanço governista: Transval, Olho d'Água, Várzea da Palha",
                    "Investimento e serviços: saúde (TAC das UBS), saneamento e educação"], src=""),
     ["O que observar daqui até 2028?",
      "Quem o prefeito vai indicar como sucessor, e se a base aceita esse nome.",
      "Se Rosa Paulino disputa a prefeitura ou fica na Câmara.",
      "Se o rompimento do vice fica isolado ou vira o começo de um novo grupo.",
      "Como o rearranjo estadual entre Ciro, o PSB e o PT chega a Varjota.",
      "O comportamento das comunidades onde o governo menos cresceu.",
      "E a entrega de serviços, especialmente saúde, saneamento e educação."],
     "Cartão; itens surgindo um a um.")
cena(Title(kicker="Encerramento", title="A disputa ainda não está definida",
           sub="Fontes: TSE (eleições 2020, 2022, 2024 e 2026) · Tesouro Nacional/SICONFI · MPCE · imprensa regional. Relatório completo e dados na pasta varjota/."),
     ["2028 ainda está em construção.",
      "Os números mostram de onde a política de Varjota veio, mas o próximo capítulo dependerá das alianças, das decisões administrativas, das lideranças e do comportamento do eleitorado.",
      "A disputa ainda não está definida."],
     "Encerramento com partículas densas e fade para preto.")


# ------------------------------------------------------------------ fala (TTS)
SIGLAS = {"PSB": "pê-ésse-bê", "MDB": "ême-dê-bê", "PDT": "pê-dê-tê", "PT": "pê-tê", "PL": "pê-éle", "PP": "pê-pê",
          "PCdoB": "pê-cê do bê", "PV": "pê-vê", "PSDB": "pê-ésse-dê-bê", "PTB": "pê-tê-bê", "PSL": "pê-ésse-éle",
          "TSE": "tê-ésse-é", "TRE": "tê-érre-é", "MPCE": "Ministério Público do Ceará", "UBS": "u-bê-ésse", "IPCA": "i-pê-cê-á",
          "IDEB": "idéb", "DNOCS": "dênócs", "LRF": "Lei de Responsabilidade Fiscal", "TAC": "tác", "QE": "quociente eleitoral"}


def falar(t):
    for k, v in SIGLAS.items():
        t = re.sub(rf"\b{k}\b", v, t)
    n2 = lambda x: num2words(int(x), lang="pt_BR")
    t = re.sub(r"(\d+),(\d+)\s?%", lambda m: f"{n2(m[1])} vírgula {n2(m[2])} por cento", t)
    t = re.sub(r"(\d+)\s?%", lambda m: f"{n2(m[1])} por cento", t)
    t = re.sub(r"\d{1,3}(?:\.\d{3})+", lambda m: n2(m[0].replace(".", "")), t)
    t = re.sub(r"(\d+),(\d+)", lambda m: f"{n2(m[1])} vírgula {n2(m[2])}", t)
    t = re.sub(r"\d+", lambda m: n2(m[0]), t)
    return t.replace("×", " a ").replace("→", " para ").replace("—", ",")


def tts(text, path):
    if not path.exists():
        subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", str(path), "--length-scale", "1.04"],
                       input=falar(text).encode(), check=True, capture_output=True)
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def chunks(sentence, maxc=90):
    """Divide uma frase longa em pedaços de legenda (por vírgula/dois-pontos)."""
    if len(sentence) <= maxc:
        return [sentence]
    parts = re.split(r"(?<=[,:;])\s+", sentence)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= maxc or not cur:
            cur = (cur + " " + p).strip()
        else:
            out.append(cur); cur = p
    out.append(cur)
    return out


LEAD, GAP, TAIL = 0.9, 0.32, 1.3
plan = []; audio_all = []; srt = []; t_global = 0.0
for i, (scene, falas, visual) in enumerate(S):
    t = LEAD; subs = []; aud = [np.zeros(int(LEAD * SR), np.float32)]
    for j, f in enumerate(falas):
        a = tts(f, WORK / f"s{i:02d}_{j:02d}.wav")
        ln = len(a) / SR
        cs = chunks(f); tot = sum(len(c) for c in cs); tt = t
        for c in cs:
            dd = ln * len(c) / tot
            subs.append((tt, tt + dd, c)); tt += dd
        aud += [a, np.zeros(int(GAP * SR), np.float32)]
        t += ln + GAP
    dur = t + TAIL
    a = np.concatenate(aud); a = np.pad(a, (0, max(0, int(dur * SR) - len(a))))[:int(dur * SR)]
    audio_all.append(a)
    for s0, s1, c in subs:
        srt.append((t_global + s0, t_global + s1, c))
    plan.append((i, dur, subs, visual))
    t_global += dur
narr = np.concatenate(audio_all)
TOTAL = len(narr) / SR
print(f"duração total: {TOTAL/60:.1f} min, {len(S)} cenas", flush=True)

# ------------------------------------------------------------------ trilha (sintetizada, original)
def music(total, sr=SR):
    t = np.arange(int(total * sr)) / sr
    out = np.zeros_like(t)
    chords = [[55, 110, 164.81, 220, 261.63], [43.65, 87.31, 130.81, 174.61, 220], [49, 98, 146.83, 196, 246.94], [41.2, 82.41, 123.47, 164.81, 207.65]]
    seg = 16.0
    for k, ch in enumerate(chords * int(total / seg / 4 + 2)):
        s0 = k * seg
        if s0 > total: break
        idx = (t >= s0 - 2) & (t < s0 + seg + 2)
        tt = t[idx] - s0
        env = np.clip(np.minimum((tt + 2) / 4, (seg + 2 - tt) / 4), 0, 1)
        for j, f in enumerate(ch):
            out[idx] += env * (0.5 / (j + 1)) * np.sin(2 * np.pi * f * tt + j) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * tt + j))
    rng = np.random.default_rng(3); n = rng.standard_normal(len(t))
    n = np.convolve(n, np.ones(400) / 400, mode="same") * 0.6
    out += n * (0.5 + 0.5 * np.sin(2 * np.pi * 0.03 * t))
    out /= np.abs(out).max()
    return out * 0.16


bgm = music(TOTAL)
# impacto grave na entrada de cada capítulo
t0 = 0
for i, dur, subs, _ in plan:
    if isinstance(S[i][0], (Chapter, Title)):
        n = int(2.5 * SR); tt = np.arange(n) / SR
        boom = 0.35 * np.sin(2 * np.pi * (48 - 10 * tt) * tt) * np.exp(-tt * 1.8)
        st = int(t0 * SR); bgm[st:st + n] += boom[:len(bgm[st:st + n])]
    t0 += dur
# ducking: música abaixa quando há voz
env = np.abs(narr); k = int(0.4 * SR)
env = np.convolve(env, np.ones(k) / k, mode="same")
duck = 1 - 0.55 * np.clip(env / 0.02, 0, 1)
mix = narr * 0.95 + bgm * duck
mix /= max(1, np.abs(mix).max() / 0.97)
with wave.open(str(WORK / "trilha_final.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ render paralelo
def job(args):
    i, dur, subs, _ = args
    out = WORK / f"v{i:02d}.mp4"
    if not out.exists():
        render_scene(S[i][0], dur, subs, out, seed=i)
    return str(out)


if __name__ == "__main__":
    with Pool(4) as p:
        outs = p.map(job, plan, chunksize=1)
    (WORK / "lista.txt").write_text("".join(f"file '{o}'\n" for o in outs))
    VD = BASE / "video"; VD.mkdir(exist_ok=True)
    final = VD / "varjota_2028_raio-x_do_poder.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(WORK / "lista.txt"),
                    "-i", str(WORK / "trilha_final.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)
    def ts(s): return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int((s%1)*1000):03d}"
    (VD / "varjota_2028_raio-x_do_poder.srt").write_text("\n".join(f"{k+1}\n{ts(a)} --> {ts(b)}\n{c}\n" for k, (a, b, c) in enumerate(srt)))
    # roteiro + storyboard
    rows = ["# VARJOTA 2028 — O RAIO-X DO PODER · Roteiro e storyboard\n",
            "| # | Início | Duração | Capítulo | Tipo de cena | Texto na tela | Visual / movimento / efeito | Narração |", "|---|---|---|---|---|---|---|---|"]
    t0 = 0
    for i, dur, subs, visual in plan:
        sc = S[i][0]
        tela = getattr(sc, "title", "")
        rows.append(f"| {i+1} | {int(t0//60):02d}:{int(t0%60):02d} | {dur:.0f}s | {sc.chapter or '—'} | {type(sc).__name__} | {tela} | "
                    f"{visual} Fundo escuro com vinheta, push-in lento (3,5%), partículas douradas ({int(sc.particles*100)}%), fade 0,5s. | {' '.join(S[i][1])} |")
        t0 += dur
    (VD / "roteiro_storyboard_raio-x.md").write_text("\n".join(rows) + f"\n\nDuração total: {TOTAL/60:.1f} min\n")
    print("OK", final, f"{TOTAL/60:.1f} min")
