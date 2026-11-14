"""Pontos de atenção em compras públicas: regras automáticas sobre os dados do PNCP/TCE.
Cada alerta traz o fato (números), por que chama atenção, a linha de ataque (a pergunta que um vereador, a imprensa
ou o Ministério Público faria), a defesa provável do gestor, o que pedir pela Lei de Acesso e a base legal.
Alerta é indício para pedir documento, não prova de irregularidade."""
import collections, re

# Limites de dispensa por valor (Lei 14.133, art. 75, I e II), atualizados por decreto a cada ano.
# 2023: Decreto 11.317/2022 · 2024: Decreto 11.871/2023 · 2025: Decreto 12.343/2024. Anos sem valor aqui: conferir o decreto do ano.
LIMITES = {2023: (114416.65, 57208.33), 2024: (119812.02, 59906.02), 2025: (125451.15, 62725.59)}

TEXTOS = {
 "sem_pncp": dict(gravidade="Alta", titulo="Órgão não publica no PNCP",
  por_que="Desde 2024 todo órgão público deve divulgar licitações, dispensas e contratos no Portal Nacional de Contratações Públicas. Sem isso, ninguém de fora consegue conferir preço, quantidade e vencedor.",
  ataque="Por que o órgão contratou quase R$ {valor} sem publicar os processos no portal nacional? O que impede a população de ver o que foi comprado e por quanto?",
  defesa="Problema de sistema ou de integração com o PNCP; publicação feita no portal próprio ou no Diário Oficial; processos em fase de envio.",
  pedir="Cópia integral dos processos de contratação do período (termo de referência, pesquisa de preços, propostas, contrato, notas fiscais) e o motivo da não publicação no PNCP.",
  base="Lei 14.133/2021, arts. 54, 72, parágrafo único, 94 e 174; Lei 12.527/2011 (LAI), art. 8º."),
 "sem_resultado": dict(gravidade="Alta", titulo="Processos sem resultado publicado",
  por_que="{n} de {t} processos ({pct}) estão no PNCP sem o resultado (vencedor e preço final). Sem isso não dá para saber quem ganhou nem quanto vai receber; a lei manda publicar a homologação e o contrato.",
  ataque="Quem ganhou essas {n} licitações e por quanto? Por que o resultado não foi publicado no portal nacional?",
  defesa="Processos em andamento, desertos ou fracassados; resultado publicado no Diário Oficial ou no portal próprio.",
  pedir="Atas de julgamento, termos de homologação e contratos dos processos listados.",
  base="Lei 14.133/2021, arts. 71, 94 e 174."),
 "dispensa_alta": dict(gravidade="Média", titulo="Quase tudo sem licitação",
  por_que="Dispensa é exceção. Quando a grande maioria das compras sai sem disputa, o órgão perde a chance de pagar menos e fica mais fácil direcionar para conhecidos.",
  ataque="{n} de {t} contratações ({pct}) foram feitas sem licitação. Por que não houve disputa, se a lei manda licitar como regra?",
  defesa="Valores pequenos, dentro do limite legal; dispensa eletrônica com cotação aberta; urgência; poucos fornecedores na região.",
  pedir="Para cada dispensa: a justificativa da escolha do fornecedor, as cotações recebidas e se houve aviso público (dispensa eletrônica) com prazo para propostas.",
  base="Lei 14.133/2021, arts. 72 e 75, § 3º (aviso prévio da dispensa)."),
 "teto_dispensa": dict(gravidade="Média", titulo="Valor colado no teto da dispensa",
  por_que="O limite para contratar sem licitação em {ano} era de R$ {limite}. Este processo ficou em {pct_limite} do teto. Valores repetidamente encostados no limite sugerem que o objeto foi dimensionado para caber na dispensa.",
  ataque="Por que este contrato saiu por R$ {valor}, a poucos reais do máximo permitido sem licitação? A necessidade real era essa ou o valor foi ajustado para fugir da disputa?",
  defesa="O valor veio da pesquisa de preços; a necessidade anual é essa mesma; coincidência com o teto.",
  pedir="Estudo técnico preliminar, memória de cálculo das quantidades e a pesquisa de preços (com as cotações completas e datas).",
  base="Lei 14.133/2021, arts. 18, 23 e 75, II e § 1º."),
 "fracionamento": dict(gravidade="Alta", titulo="Possível fracionamento",
  por_que="Várias dispensas do mesmo tipo no mesmo ano somam {soma}, acima do limite de dispensa de {limite}. A lei soma as despesas do mesmo ramo no ano para impedir que uma compra grande seja dividida em pequenas.",
  ataque="Se o órgão sabia que ia gastar {soma} com {categoria} no ano, por que fez {n} dispensas separadas em vez de uma licitação?",
  defesa="Objetos diferentes (não são do mesmo ramo); necessidades surgiram em momentos distintos; dispensas de unidades diferentes.",
  pedir="Os processos das dispensas listadas e o Plano de Contratações Anual (PCA) do ano, para ver se a despesa estava prevista.",
  base="Lei 14.133/2021, art. 75, § 1º (somatório no exercício e no mesmo ramo); art. 12, VII (PCA)."),
 "sem_desconto": dict(gravidade="Média", titulo="Pagou praticamente o preço estimado",
  por_que="Em {n} compras o valor final ficou a menos de 1% do estimado. Quando há disputa real, é comum o preço cair bem abaixo da estimativa. Preço final quase igual ao estimado pode indicar cotações combinadas ou estimativa feita a partir da proposta do próprio vencedor.",
  ataque="Como o vencedor ofereceu exatamente o preço que a Câmara/Prefeitura estimou, centavo por centavo? Quem forneceu as cotações da estimativa?",
  defesa="A pesquisa de preços foi bem feita e refletiu o mercado; o fornecedor aceitou cobrir o valor de referência.",
  pedir="As cotações usadas na estimativa (nome, CNPJ, data e assinatura de cada empresa) e a consulta a painéis de preço (Painel de Preços, PNCP, contratações similares).",
  base="Lei 14.133/2021, art. 23 (pesquisa de preços) e art. 75, § 3º."),
 "acima_estimado": dict(gravidade="Média", titulo="Item pago acima do estimado",
  por_que="O preço unitário homologado ficou {dif} acima do que o próprio órgão estimou. O normal é pagar igual ou menos que o estimado.",
  ataque="Por que se pagou {pago} por {item}, se a própria estimativa era {est}?",
  defesa="Erro de digitação no portal; reequilíbrio de preço; item com especificação diferente.",
  pedir="Nota fiscal do item, a proposta vencedora e a justificativa do preço acima da estimativa.",
  base="Lei 14.133/2021, arts. 23 e 59, III (preço acima do orçamento)."),
 "concentracao": dict(gravidade="Média", titulo="Fornecedor concentra o gasto",
  por_que="{forn} ficou com {pct} de tudo o que foi homologado no período ({valor}). Concentração alta reduz concorrência e merece checar quem são os sócios.",
  ataque="Por que uma única empresa recebe {pct} das compras? Quem são os donos e qual a relação deles com a gestão?",
  defesa="Único fornecedor da região com o produto; venceu as disputas pelo menor preço.",
  pedir="Os processos vencidos por esse fornecedor; consulte também o quadro de sócios na Receita Federal (CNPJ {cnpj}).",
  base="Lei 14.133/2021, arts. 5º (impessoalidade) e 14 (impedimentos)."),
 "assessorias": dict(gravidade="Média", titulo="Muito dinheiro em assessorias e consultorias",
  por_que="{pct} do valor contratado ({valor}) foi para assessorias, consultorias e serviços jurídicos. Muitas dessas tarefas (contabilidade, controle interno, licitação) são rotina que deveria ser feita por servidores efetivos.",
  ataque="O órgão tem servidores de carreira para contabilidade, controle interno e licitação? Se tem, por que paga {valor} a empresas para fazer o mesmo?",
  defesa="Falta de servidores qualificados; serviços técnicos especializados; custo menor que contratar pessoal.",
  pedir="Lista de servidores efetivos e comissionados com cargo e função; relatórios e produtos entregues por cada assessoria (o que foi feito, mês a mês).",
  base="CF, art. 37, II (concurso público); Lei 14.133/2021, art. 74, III (serviço técnico especializado só com notória especialização)."),
 "objeto_repetido": dict(gravidade="Alta", titulo="Mesmo serviço contratado mais de uma vez",
  por_que="O mesmo fornecedor tem {n} contratos de objeto muito parecido no período ({valores}). Pode ser renovação legítima ou pagamento em dobro pelo mesmo trabalho.",
  ataque="O que foi entregue em cada um dos contratos de \"{tema}\"? Por que pagar de novo à mesma empresa pelo mesmo serviço?",
  defesa="São etapas diferentes (elaboração × acompanhamento) ou exercícios diferentes.",
  pedir="Os dois processos, os produtos entregues em cada um (relatórios, documentos) e os atestados de recebimento.",
  base="Lei 14.133/2021, arts. 117 e 140 (fiscalização e recebimento)."),
 "fim_de_ano": dict(gravidade="Baixa", titulo="Contratações concentradas em dezembro",
  por_que="{n} contratações ({valor}) foram feitas na última quinzena de dezembro. Correria de fim de ano costuma vir com planejamento fraco e gasto de sobra de orçamento.",
  ataque="Por que tantas contratações deixadas para o fim do ano? Havia urgência real ou era para gastar o saldo do orçamento?",
  defesa="Contratos para o ano seguinte, assinados antes do início do exercício; planejamento anual.",
  pedir="Os processos de dezembro com as datas de cada etapa (pedido, cotação, parecer, assinatura).",
  base="Lei 14.133/2021, art. 12, VII (Plano de Contratações Anual)."),
 "pessoa_fisica_mei": dict(gravidade="Baixa", titulo="Contrato alto com MEI ou empresa individual",
  por_que="{forn} parece ser microempreendedor individual (nome com CPF ou número no nome) e recebeu {valor}. O MEI tem faturamento máximo de R$ 81 mil por ano; contratos altos merecem conferir capacidade e vínculos.",
  ataque="Uma empresa de uma pessoa só tem estrutura para esse serviço? Ela tem ligação com alguém da gestão?",
  defesa="Profissional autônomo qualificado, formalizado como MEI ou empresa individual.",
  pedir="Comprovação da capacidade técnica e o enquadramento do fornecedor (consulta do CNPJ na Receita).",
  base="LC 123/2006 (limite do MEI); Lei 14.133/2021, arts. 14 e 67."),
 "mesmo_cnpj_outro_lugar": dict(gravidade="Média", titulo="Mesmo fornecedor em outro órgão",
  por_que="O CNPJ {cnpj} também tem contrato em {onde}. Empresas que circulam entre prefeituras e câmaras vizinhas com objetos parecidos podem indicar uma rede de assessorias que se repete.",
  ataque="Por que a mesma empresa vende o mesmo tipo de serviço, pelo mesmo valor, para órgãos diferentes da região? Quem indica?",
  defesa="Empresa especializada no setor público, que atende vários municípios.",
  pedir="Os processos nos dois órgãos e as cotações: confira se as mesmas empresas aparecem cotando nos dois lugares.",
  base="Lei 14.133/2021, arts. 5º e 9º (vedação de favorecimento)."),
 "combustivel": dict(gravidade="Alta", titulo="Combustível: quantidade contratada",
  por_que="Foram contratados {litros} litros de combustível ({valor}). Para checar se é compatível, divida pelos veículos da frota: com um carro rodando 10 km/l, isso daria cerca de {km} km no ano.",
  ataque="Quantos veículos o órgão tem e quantos quilômetros cada um rodou? Os {litros} litros batem com o uso real?",
  defesa="A quantidade é o máximo previsto, não o consumido; frota inclui veículos à disposição de vereadores ou setores.",
  pedir="Notas de abastecimento (data, litros, placa e quilometragem), relação de veículos com placa e o controle de uso (diário de bordo).",
  base="Lei 14.133/2021, art. 140; LAI, art. 8º."),
 "repasse_alto": dict(gravidade="Média", titulo="Repasse à Câmara cresceu muito",
  por_que="O repasse passou de {antes} para {depois} ({pct}). A Constituição limita o total que a Câmara pode receber (art. 29-A).",
  ataque="O que justifica o aumento? O repasse respeitou o teto constitucional calculado sobre a receita do ano anterior?",
  defesa="Aumento da receita do município; recomposição de perdas de anos anteriores; repasse dentro do teto.",
  pedir="O cálculo do limite do art. 29-A feito pela Prefeitura para o ano e a lei orçamentária com a dotação da Câmara.",
  base="CF, art. 29-A (limites de despesa do Legislativo municipal)."),
}

BR = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
PCT = lambda v: f"{v * 100:.0f}%".replace(".", ",")
SERV = re.compile(r"assessor|consult|jur[ií]dic|advoc|contab|auditor|controle intern|controle extern|apoio t[ée]cnico|ouvidoria|implanta[çc][ãa]o e normatiza|governan|balc[ãa]o do cidad|procon|controladoria", re.I)

def _a(tipo, fato, v_env=None, ref="", link="", **fmt):
    t = TEXTOS[tipo]
    f = lambda s: s.format(**fmt) if fmt else s
    return {"gravidade": t["gravidade"], "tipo": t["titulo"], "fato": fato, "valor": v_env, "referencia": ref, "por_que": f(t["por_que"]), "ataque": f(t["ataque"]),
            "defesa": t["defesa"], "pedir": t["pedir"].format(**fmt) if "{" in t["pedir"] else t["pedir"], "base": t["base"], "link": link}

def gerar(comp, itens_rows, contratos_tce=None, repasse=None, outros=None, contratos_pncp=None):
    """comp: processos (dict com org, ano, pub, mod, cat, obj, est, hom, forn_list[(nome, cnpj, valor)], k, link).
    itens_rows: dicts com item, unid, qtd, fornecedor, v_unit, v_total, v_est, ano, k, link.
    repasse: (ano_antes, valor_antes, ano_depois, valor_depois) para Câmara. outros: {cnpj: ["Órgão X: objeto (valor)"]}."""
    A = []
    tot = sum(c["hom"] or 0 for c in comp)
    if not comp and contratos_tce:
        v = sum(c["valor"] or 0 for c in contratos_tce if not c["aditivo"])
        A.append(_a("sem_pncp", f"Nenhuma contratação no PNCP no período, mas {len(contratos_tce)} contratos registrados no TCE-CE ({BR(v)}).", v, valor=BR(v)))
    if not comp and contratos_tce:  # sem PNCP: usa os contratos do TCE-CE (sem modalidade nem itens) nas regras que não dependem disso
        comp = [dict(org="", ano=int(c["data"][:4]), pub=c["data"], mod="Contrato (TCE-CE)", cat="", obj=c["objeto"], est=None, hom=c["valor"], k=c.get("processo") or "",
                     link="", forn_list=[(c["fornecedor"], c["cnpj"], c["valor"])]) for c in contratos_tce if not c["aditivo"]]
        tot = sum(c["hom"] or 0 for c in comp)
        if not itens_rows: itens_rows = [dict(item=c["obj"], unid="", qtd=None, fornecedor=c["forn_list"][0][0], cnpj=c["forn_list"][0][1], v_unit=None, v_total=c["hom"], v_est=None, ano=c["ano"], k=c["k"], link="") for c in comp]
    sem = [c for c in comp if re.search("Dispensa|Inexig", c["mod"])]
    semres = [c for c in comp if not c["hom"] and c["mod"] != "Contrato (TCE-CE)" and not re.search("Credenciamento|Pré-qualifica", c["mod"])]
    if len(semres) >= 5 and len(semres) / len(comp) >= 0.3:
        v = sum(c["est"] or 0 for c in semres)
        A.append(_a("sem_resultado", f"{len(semres)} processos sem vencedor/valor final publicados, somando {BR(v)} estimados. Maiores: " + "; ".join(f"{c['obj'][:60]} ({BR(c['est'] or 0)})" for c in sorted(semres, key=lambda c: -(c['est'] or 0))[:5]), v,
                    n=len(semres), t=len(comp), pct=PCT(len(semres) / len(comp))))
    if comp and len(sem) / len(comp) >= 0.5:
        A.append(_a("dispensa_alta", f"{len(sem)} de {len(comp)} processos sem licitação ({PCT(len(sem) / len(comp))}).", sum(c["hom"] or 0 for c in sem), n=len(sem), t=len(comp), pct=PCT(len(sem) / len(comp))))
    soma = collections.defaultdict(list)
    for c in comp:
        if "Dispensa" not in c["mod"] or not c["hom"]: continue
        eng = bool(re.search(r"engenharia|obra|reforma|constru|manuten[çc][ãa]o predial", c["obj"], re.I))
        lim = LIMITES.get(c["ano"], (None, None))[0 if eng else 1]
        if lim and 0.85 * lim <= c["hom"] <= lim:
            A.append(_a("teto_dispensa", f"{c['pub']}: {c['obj'][:120]} — {BR(c['hom'])} ({PCT(c['hom'] / lim)} do limite de {BR(lim)}).", c["hom"], c["k"], c["link"],
                        ano=c["ano"], limite=BR(lim), pct_limite=PCT(c["hom"] / lim), valor=BR(c["hom"])))
        elif not lim and 52000 <= c["hom"] <= 70000 and not eng:
            A.append(_a("teto_dispensa", f"{c['pub']}: {c['obj'][:120]} — {BR(c['hom'])}. Limite de {c['ano']} a conferir no decreto do ano.", c["hom"], c["k"], c["link"],
                        ano=c["ano"], limite="(conferir decreto)", pct_limite="perto", valor=BR(c["hom"])))
        if not eng: soma[(c["ano"], c["cat"])].append(c)
    for (ano, cat), cs in soma.items():
        lim = LIMITES.get(ano, (None, None))[1]
        s = sum(c["hom"] for c in cs)
        if len(cs) >= 2 and lim and s > lim and cat != "Outros":
            A.append(_a("fracionamento", f"{ano} · {cat}: {len(cs)} dispensas somando {BR(s)} — " + "; ".join(f"{c['pub']} {BR(c['hom'])}" for c in cs), s, ", ".join(c["k"] for c in cs),
                        soma=BR(s), limite=BR(lim), categoria=cat.lower(), n=len(cs)))
    quase = [c for c in comp if c["hom"] and c["est"] and abs(c["hom"] / c["est"] - 1) < 0.01]
    if len(quase) >= 3:
        A.append(_a("sem_desconto", f"{len(quase)} de {len([c for c in comp if c['hom'] and c['est']])} processos fecharam a menos de 1% do estimado: " + "; ".join(f"{c['obj'][:50]} ({BR(c['hom'])} × {BR(c['est'])})" for c in quase[:8]),
                    sum(c["hom"] for c in quase), n=len(quase)))
    for r in itens_rows:
        if r["v_unit"] and r["v_est"] and r["v_unit"] > r["v_est"] * 1.05 and (r["v_total"] or 0) >= 300:
            A.append(_a("acima_estimado", f"{r['item'][:90]}: pago {BR(r['v_unit'])} × estimado {BR(r['v_est'])} ({r['fornecedor']}).", r["v_total"], r["k"], r["link"],
                        dif=PCT(r["v_unit"] / r["v_est"] - 1), pago=BR(r["v_unit"]), item=r["item"][:60].lower(), est=BR(r["v_est"])))
    pf = collections.defaultdict(lambda: [0.0, ""])
    for r in itens_rows:
        if r["v_total"]: pf[r["fornecedor"]][0] += r["v_total"]; pf[r["fornecedor"]][1] = r.get("cnpj", "")
    if contratos_pncp:
        pc_ = collections.defaultdict(lambda: [0.0, ""])
        for x in contratos_pncp: pc_[x["fornecedor"]][0] += x["valor"] or 0; pc_[x["fornecedor"]][1] = x["cnpj"]
        if sum(v[0] for v in pc_.values()) > sum(v[0] for v in pf.values()): pf = pc_
    tit = sum(v[0] for v in pf.values())
    for f, (v, cn) in sorted(pf.items(), key=lambda z: -z[1][0])[:3]:
        if tit and v / tit >= 0.15 and len(pf) >= 4:
            A.append(_a("concentracao", f"{f}: {BR(v)} de {BR(tit)} ({PCT(v / tit)}).", v, cn, forn=f, pct=PCT(v / tit), valor=BR(v), cnpj=cn))
    sv = sum(c["hom"] or 0 for c in comp if SERV.search(c["obj"]))
    if tot and sv / tot >= 0.3:
        A.append(_a("assessorias", f"{BR(sv)} de {BR(tot)} em assessoria, consultoria e jurídico.", sv, pct=PCT(sv / tot), valor=BR(sv)))
    porf = collections.defaultdict(list)
    for c in comp:
        for n, cn, v in c["forn_list"]: porf[cn or n].append(c)
    STOP = {"contratacao", "contratação", "servicos", "serviços", "prestacao", "prestação", "empresa", "especializada", "municipal", "camara", "câmara", "atender", "necessidades", "junto", "conforme", "secretaria", "municipio", "município", "destinados", "destinado", "aquisição", "aquisicao"}
    pal = lambda c: set(w for w in re.findall(r"[a-zçãõáéíóúâê]{5,}", c["obj"].lower()) if w not in STOP)
    for cn, cs in porf.items():
        cs = [c for c in cs if SERV.search(c["obj"]) or re.search(r"plano|pca|sistema|licen", c["obj"], re.I)]
        par = set()
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                a_, b_ = pal(cs[i]), pal(cs[j])
                if cs[i]["k"] != cs[j]["k"] and a_ and b_ and len(a_ & b_) / min(len(a_), len(b_)) >= 0.5: par |= {i, j}
        if len(par) >= 2:
            g = [cs[i] for i in sorted(par)]; nome = next((n for n, c2, v in g[0]["forn_list"] if (c2 or n) == cn), cn)
            A.append(_a("objeto_repetido", f"{nome}: " + "; ".join(f"{c['pub']} {c['obj'][:70]} ({BR(c['hom'] or 0)})" for c in g), sum(c["hom"] or 0 for c in g), ", ".join(c["k"] for c in g),
                        n=len(g), valores=", ".join(BR(c["hom"] or 0) for c in g), tema=g[0]["obj"][:60].lower()))
    dez = collections.defaultdict(list)
    for c in comp:
        if c["pub"][5:7] == "12" and int(c["pub"][8:10]) >= 15: dez[c["pub"][:4]].append(c)
    for y, cs in dez.items():
        if len(cs) >= 3:
            v = sum(c["hom"] or 0 for c in cs)
            A.append(_a("fim_de_ano", f"{y}: {len(cs)} processos entre 15 e 31/12 — " + "; ".join(f"{c['pub']} {c['obj'][:45]}" for c in cs), v, n=len(cs), valor=BR(v)))
    for c in comp:
        for n, cn, v in c["forn_list"]:
            if v and v >= 30000 and re.match(r"^\d{2}\.\d{3}\.\d{3} |\d{11}$| ME$|SOCIEDADE INDIVIDUAL", n or ""):
                A.append(_a("pessoa_fisica_mei", f"{n}: {BR(v)} — {c['obj'][:100]}", v, c["k"], c["link"], forn=n, valor=BR(v)))
    if outros:
        vistos = set()
        for c in comp:
            for n, cn, v in c["forn_list"]:
                if cn and cn in outros and cn not in vistos:
                    vistos.add(cn)
                    A.append(_a("mesmo_cnpj_outro_lugar", f"{n} (CNPJ {cn}) aqui: {c['obj'][:80]} ({BR(v or 0)}). Em outro órgão: " + " | ".join(outros[cn][:3]), v, cn, c["link"], cnpj=cn, onde="; ".join(o.split(":")[0] for o in outros[cn][:3])))
        for c in (contratos_tce or []):
            if c["cnpj"] in outros and c["cnpj"] not in vistos:
                vistos.add(c["cnpj"])
                A.append(_a("mesmo_cnpj_outro_lugar", f"{c['fornecedor']} (CNPJ {c['cnpj']}) aqui: {c['objeto'][:80]} ({BR(c['valor'] or 0)}). Em outro órgão: " + " | ".join(outros[c['cnpj']][:3]), c["valor"], c["cnpj"],
                            cnpj=c["cnpj"], onde="; ".join(o.split(":")[0] for o in outros[c["cnpj"]][:3])))
    lit = [r for r in itens_rows if re.search(r"gasolina|diesel|etanol|combust", r["item"], re.I) and re.match(r"^l", (r["unid"] or "").lower())]
    if lit:
        L = sum(r["qtd"] or 0 for r in lit); v = sum(r["v_total"] or (r["qtd"] or 0) * (r["v_est"] or 0) for r in lit)
        N = lambda q: f"{q:,.0f}".replace(",", ".")
        A.append(_a("combustivel", f"{N(L)} litros contratados ({BR(v)}): " + "; ".join(f"{r['ano']} {r['item'][:30]} {N(r['qtd'] or 0)} L a {BR(r['v_unit'] or r['v_est'] or 0)}" for r in lit[:6]), v,
                    litros=f"{L:,.0f}".replace(",", "."), valor=BR(v), km=f"{L * 10:,.0f}".replace(",", ".")))
    if repasse and repasse[1] and repasse[3] and repasse[3] / repasse[1] - 1 >= 0.15:
        A.append(_a("repasse_alto", f"{repasse[0]}: {BR(repasse[1])} → {repasse[2]}: {BR(repasse[3])}.", repasse[3], antes=BR(repasse[1]), depois=BR(repasse[3]), pct=PCT(repasse[3] / repasse[1] - 1)))
    ordem = {"Alta": 0, "Média": 1, "Baixa": 2}
    return sorted(A, key=lambda a: (ordem[a["gravidade"]], -(a["valor"] or 0)))
