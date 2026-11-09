"""Coleta de dados públicos de compras: PNCP (contratações, contratos, itens e vencedores) e TCE-CE (órgãos, contratos, empenhos).
Tudo é público e não precisa de senha. Hosts: pncp.gov.br e api-dados-abertos.tce.ce.gov.br."""
import calendar, json, time, unicodedata, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

PNCP, TCE = "https://pncp.gov.br/api", "https://api-dados-abertos.tce.ce.gov.br/api"

def _get(u, tent=5):
    for t in range(tent):
        try:
            r = urllib.request.urlopen(u, timeout=180).read()
            return json.loads(r) if r.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (204, 404, 422): return {}
            time.sleep(3 * (t + 1))
        except Exception:
            time.sleep(3 * (t + 1))
    print("  ! falhou:", u, flush=True); return {}

def slug(s): return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower().replace(" ", "-")

def municipio_tce(nome):
    """Código do município no TCE-CE e no IBGE, pelo nome (sem acento, maiúsculas)."""
    alvo = slug(nome).replace("-", " ").upper()
    for m in _get(f"{TCE}/municipios").get("elements", []):
        if slug(m["nome_municipio"]).replace("-", " ").upper() == alvo: return m["codigo_municipio"], m["codigo_municipio_ibge"]
    raise SystemExit(f"Município não encontrado no TCE-CE: {nome}")

def orgaos(cod, ano):
    """CNPJs da Câmara e da Prefeitura (com fundos/secretarias que têm CNPJ próprio)."""
    el = _get(f"{TCE}/orgaos?codigo_municipio={cod}&exercicio_orcamento={ano}00").get("elements", [])
    cam = {x["cgc_orgao"]: "Câmara" for x in el if "CAMARA" in x["nome_orgao"].upper()}
    pref = {}
    for x in el:
        if x["cgc_orgao"] in cam: continue
        pref.setdefault(x["cgc_orgao"], x["nome_orgao"].title())
    principal = max(pref, key=lambda c: sum(1 for x in el if x["cgc_orgao"] == c)) if pref else None
    if principal: pref[principal] = "Prefeitura"
    return cam, pref

def _paginar(base):
    pg, out = 1, []
    while True:
        d = _get(f"{base}&pagina={pg}&tamanhoPagina=50")
        if not isinstance(d, dict) or not d: return out
        out += d.get("data", [])
        if pg >= (d.get("totalPaginas") or 1): return out
        pg += 1

def pncp(cnpjs, anos, workers=8):
    """cnpjs: {cnpj: rótulo}. Devolve {orgaos, contratacoes, contratos, itens{numeroControle: [...]}}."""
    tarefas = [(c, y, m) for c in cnpjs for y in anos for m in range(1, 14)]
    def f_comp(t):
        c, y, m = t
        return [dict(x, _org=cnpjs[c]) for x in _paginar(f"{PNCP}/consulta/v1/contratacoes/publicacao?dataInicial={y}0101&dataFinal={y}1231&codigoModalidadeContratacao={m}&cnpj={c}")]
    def f_ctr(t):
        c, y = t
        return [dict(x, _org=cnpjs[c]) for x in _paginar(f"{PNCP}/consulta/v1/contratos?dataInicial={y}0101&dataFinal={y}1231&cnpjOrgao={c}")]
    with ThreadPoolExecutor(workers) as ex:
        comp = [x for l in ex.map(f_comp, tarefas) for x in l]
        ctr = [x for l in ex.map(f_ctr, [(c, y) for c in cnpjs for y in anos]) for x in l]
    uniq = {x["numeroControlePNCP"]: x for x in comp}
    print(f"  PNCP: {len(uniq)} contratações, {len(ctr)} contratos; baixando itens...", flush=True)
    def f_itens(x):
        c, a, s = x["orgaoEntidade"]["cnpj"], x["anoCompra"], x["sequencialCompra"]
        it = _get(f"{PNCP}/pncp/v1/orgaos/{c}/compras/{a}/{s}/itens?pagina=1&tamanhoPagina=1000") or []
        out = []
        for i in (it if isinstance(it, list) else []):
            r = _get(f"{PNCP}/pncp/v1/orgaos/{c}/compras/{a}/{s}/itens/{i['numeroItem']}/resultados") if i.get("temResultado") else []
            out.append({"item": i["numeroItem"], "descricao": i.get("descricao"), "qtd": i.get("quantidade"), "unid": i.get("unidadeMedida"), "v_unit_est": i.get("valorUnitarioEstimado"),
                        "resultados": [{"fornecedor": z.get("nomeRazaoSocialFornecedor"), "ni": z.get("niFornecedor"), "v_unit": z.get("valorUnitarioHomologado"), "v_total": z.get("valorTotalHomologado"),
                                        "qtd": z.get("quantidadeHomologada")} for z in (r if isinstance(r, list) else [])]})
        return x["numeroControlePNCP"], out
    with ThreadPoolExecutor(workers) as ex: itens = dict(ex.map(f_itens, uniq.values()))
    return {"orgaos": cnpjs, "contratacoes": list(uniq.values()), "contratos": ctr, "itens": itens}

def tce_contratos(cod, anos, filtro_camara=None):
    """Contratos do município no TCE-CE com o nome do contratado. filtro_camara: True só os da Câmara, False exclui os da Câmara."""
    ctd, ctr = [], []
    meses = [(y, m) for y in anos for m in range(1, 13)]
    def f(t):
        y, m = t; u = calendar.monthrange(y, m)[1]; q = f"codigo_municipio={cod}&data_inicio={y}{m:02d}01&data_fim={y}{m:02d}{u}"
        return _get(f"{TCE}/contratados?{q}").get("elements", []), _get(f"{TCE}/contratos?{q}").get("elements", [])
    with ThreadPoolExecutor(6) as ex:
        for a, b in ex.map(f, meses): ctd += a; ctr += b
    idx = {(x["numero_contrato"], x["data_contrato"][:10]): x for x in ctr}
    out, vistos = [], set()
    for x in ctd:
        c = idx.get((x["numero_contrato"], x["data_contrato"][:10]))
        if not c: continue
        o = (c.get("descricao_objeto_contrato") or "").strip(); O = slug(o).upper().replace("-", " ")
        cam = ("CAMARA MUNICIPAL" in O or "PODER LEGISLATIVO" in O) and "CAMARA DE AR" not in O
        if filtro_camara is True and not cam: continue
        if filtro_camara is False and cam: continue
        k = (c["data_contrato"][:10], x["numero_documento_negociante"].lstrip("0"), c.get("valor_total_contrato"), c.get("modalide_contrato"))
        if k in vistos: continue
        vistos.add(k)
        out.append({"data": k[0], "fornecedor": x["nome_negociante"], "cnpj": k[1], "valor": c.get("valor_total_contrato"), "aditivo": c.get("modalide_contrato") != "OR",
                    "objeto": o, "fim": (c.get("data_fim_vigencia_contrato") or "")[:10], "processo": c.get("numero_processo_adm")})
    return out
