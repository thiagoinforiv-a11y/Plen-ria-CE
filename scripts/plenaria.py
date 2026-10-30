#!/usr/bin/env python3
"""Gera os arquivos de dados da Plenária CE a partir dos dados abertos do TSE.

Uso:
  # 1) Base histórica (totais municipais 2010-2022, via espelho Base dos Dados)
  python3 scripts/plenaria.py seed --municipio Varjota

  # 2) Detalhe por seção/bairro (arquivos oficiais do TSE; baixa se não existirem)
  python3 scripts/plenaria.py tse --municipio Varjota --ano 2022 --ano 2018 --baixar

Os arquivos do TSE ficam em ./tse_raw (ou --pasta). Nada é inventado: tudo o que
vai para data/<uf>/<cidade>.js vem linha a linha desses arquivos.
"""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import urllib.request
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"
BD = ("https://storage.googleapis.com/download/storage/v1/b/basedosdados-public/o/"
      "one-click-download%2Fbr_tse_eleicoes%2F{}?alt=media")

CARGOS = {  # CD_CARGO do TSE -> slug usado na página
    "1": "presidente", "3": "governador", "5": "senador",
    "6": "deputado_federal", "7": "deputado_estadual", "8": "deputado_distrital",
    "11": "prefeito", "13": "vereador",
}
NOME_CARGO = {
    "presidente": "Presidente", "governador": "Governador", "senador": "Senador",
    "deputado_federal": "Deputado Federal", "deputado_estadual": "Deputado Estadual",
    "deputado_distrital": "Deputado Distrital", "prefeito": "Prefeito", "vereador": "Vereador",
}
csv.field_size_limit(1 << 30)


# ---------------------------------------------------------------- utilidades

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s).lower()).strip("-")


def inteiro(v):
    try:
        return int(float(str(v).replace(",", ".")))
    except (TypeError, ValueError):
        return None


def limpo(v):
    v = (v or "").strip()
    return None if v in ("", "#NULO#", "#NULO", "#NE#", "#NE", "-1", "-3", "-4", "NÃO DIVULGÁVEL") else v


def titulo(s):
    s = (s or "").strip()
    if not s:
        return s
    menores = {"da", "de", "do", "das", "dos", "e"}
    return " ".join(p if i and p in menores else p.capitalize()
                    for i, p in enumerate(s.lower().split()))


def hash_id(tipo, valor):
    return hashlib.sha1(f"{tipo}:{valor}".encode()).hexdigest()[:12]


def caminho_dados(uf, cidade_slug):
    return os.path.join(RAIZ, "data", uf.lower(), f"{cidade_slug}.js")


def carregar(uf, cidade_slug):
    p = caminho_dados(uf, cidade_slug)
    if not os.path.exists(p):
        return None
    txt = open(p, encoding="utf-8").read()
    return json.loads(txt[txt.index("] = ") + 4:].rstrip().rstrip(";"))


def salvar(cidade):
    uf, s = cidade["meta"]["uf"], cidade["meta"]["slug"]
    cidade["meta"]["atualizado"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    p = caminho_dados(uf, s)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    corpo = json.dumps(cidade, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write("window.PLENARIA_DATA = window.PLENARIA_DATA || {};\n")
        f.write(f'window.PLENARIA_DATA["{uf.lower()}/{s}"] = {corpo};\n')
    atualizar_registro(cidade)
    print(f"✔ {os.path.relpath(p, RAIZ)} ({os.path.getsize(p) / 1024:.0f} KB)")
    conferir()


def conferir():
    """Roda a conferência automática; avisa alto se os dados contradizem fatos conhecidos."""
    import subprocess
    try:
        r = subprocess.run(["node", os.path.join(RAIZ, "scripts", "verificar.mjs")], capture_output=True, text=True)
    except FileNotFoundError:
        print("(node não encontrado: rode scripts/verificar.mjs manualmente)")
        return
    print(r.stdout.strip())
    if r.returncode:
        print("\n!!! Os dados gerados contradizem fatos conhecidos. NÃO publique antes de corrigir.")


def atualizar_registro(cidade):
    """data/cidades.js lista as cidades com dados (base para o seletor e, depois, o login)."""
    p = os.path.join(RAIZ, "data", "cidades.js")
    lista = []
    if os.path.exists(p):
        txt = open(p, encoding="utf-8").read()
        lista = json.loads(txt[txt.index("= ") + 2:].rstrip().rstrip(";"))
    m = cidade["meta"]
    item = {"id": f"{m['uf'].lower()}/{m['slug']}", "uf": m["uf"], "nome": m["municipio"],
            "arquivo": f"data/{m['uf'].lower()}/{m['slug']}.js",
            "anos": sorted(cidade["eleicoes"].keys(), reverse=True)}
    lista = [c for c in lista if c["id"] != item["id"]] + [item]
    lista.sort(key=lambda c: c["nome"])
    with open(p, "w", encoding="utf-8") as f:
        f.write("window.PLENARIA_CIDADES = " + json.dumps(lista, ensure_ascii=False, indent=1) + ";\n")


def nova_cidade(uf, municipio, cd_tse=None, cd_ibge=None):
    return {"meta": {"uf": uf.upper(), "municipio": municipio, "slug": slug(municipio),
                     "cd_tse": cd_tse, "cd_ibge": cd_ibge},
            "contexto": [], "pessoas": {}, "eleicoes": {}}


class Pessoas:
    """Liga a mesma pessoa entre eleições sem publicar CPF/título (só hashes)."""

    def __init__(self, cidade):
        self.p = cidade["pessoas"]
        self.idx = {k: pid for pid, d in self.p.items() for k in d.get("k", [])}

    def resolver(self, nome, nasc=None, cpf=None, tit=None, extra=None):
        chaves = []
        if cpf and re.fullmatch(r"\d{11}", cpf.zfill(11)) and int(cpf) > 0:
            chaves.append(hash_id("cpf", cpf.zfill(11)))
        if tit and re.fullmatch(r"\d{8,12}", tit) and int(tit) > 0:
            chaves.append(hash_id("tit", tit.zfill(12)))
        if nome and nasc:
            chaves.append(hash_id("nn", f"{norm(nome)}|{nasc}"))
        if extra:
            chaves.append(hash_id("x", extra))
        if not chaves:
            chaves.append(hash_id("nome", norm(nome)))
        pid = next((self.idx[k] for k in chaves if k in self.idx), None)
        if pid is None:
            pid = chaves[0][:10]
            self.p[pid] = {"nome": titulo(nome), "k": []}
        for k in chaves:
            if k not in self.idx:
                self.idx[k] = pid
                self.p[pid]["k"].append(k)
        return pid


# ---------------------------------------------------------------- seed (Base dos Dados)

def baixar(url, destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return destino
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    print(f"↓ {url}")
    tmp = destino + ".part"
    with urllib.request.urlopen(url, timeout=600) as r, open(tmp, "wb") as f:
        while True:
            bloco = r.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)
    os.replace(tmp, destino)
    return destino


def cmd_seed(a):
    pasta = os.path.abspath(a.pasta)
    det = baixar(BD.format("detalhes_votacao_municipio%2Fdetalhes_votacao_municipio_bdpro.csv.gz"),
                 os.path.join(pasta, "bd_detalhes_votacao_municipio.csv.gz"))
    res = baixar(BD.format("resultados_candidato%2Fresultados_candidato_bdpro.csv.gz"),
                 os.path.join(pasta, "bd_resultados_candidato.csv.gz"))
    cand = baixar(BD.format("candidatos%2Fcandidatos_bdpro.csv.gz"),
                  os.path.join(pasta, "bd_candidatos.csv.gz"))
    vagas_f = baixar(BD.format("vagas%2Fvagas_bdpro.csv.gz"), os.path.join(pasta, "bd_vagas.csv.gz"))
    part_f = baixar(BD.format("resultados_partido_municipio%2Fresultados_partido_municipio_bdpro.csv.gz"),
                    os.path.join(pasta, "bd_resultados_partido_municipio.csv.gz"))

    alvo = norm(a.municipio)
    cidade = carregar(a.uf, slug(a.municipio))

    # contexto: comparecimento, abstenção e votos por cargo
    if not a.cd_ibge:
        sys.exit("Informe --cd-ibge (ex.: Varjota = 2313955).")
    contexto = []
    with gzip.open(det, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id_municipio"] == a.cd_ibge and r["ano"] and int(r["ano"]) >= a.desde:
                contexto.append(r)
    cd_tse = contexto[0]["id_municipio_tse"] if contexto else None
    if cidade is None:
        cidade = nova_cidade(a.uf, a.municipio, cd_tse, a.cd_ibge)
    cidade["meta"].update({"cd_tse": cd_tse, "cd_ibge": a.cd_ibge})

    vistos, ctx = set(), []
    for r in sorted(contexto, key=lambda r: (r["ano"], r["turno"], r["cargo"])):
        cargo = r["cargo"].replace(" ", "_")
        chave = (r["ano"], r["turno"], cargo)
        if chave in vistos:
            continue
        vistos.add(chave)
        secoes = inteiro(r["secoes"])
        # Em 2018 o espelho soma as seções em dobro no 1º turno (208 x 104 no 2º); nesse caso omitimos.
        if r["ano"] == "2018" and r["turno"] == "1":
            secoes = None
        ctx.append({"ano": int(r["ano"]), "turno": int(r["turno"]), "cargo": cargo,
                    "aptos": inteiro(r["aptos"]), "secoes": secoes,
                    "comparecimento": inteiro(r["comparecimento"]),
                    "abstencoes": inteiro(r["abstencoes"]), "validos": inteiro(r["votos_validos"]),
                    "brancos": inteiro(r["votos_brancos"]), "nulos": inteiro(r["votos_nulos"]),
                    "nominais": inteiro(r["votos_nominais"]), "legenda": inteiro(r["votos_legenda"]),
                    "fonte": "TSE via Base dos Dados (detalhes_votacao_municipio)"})
    # mantém o que já veio do TSE direto para os mesmos anos
    tse_ctx = {(c["ano"], c["turno"], c["cargo"]) for c in cidade["contexto"] if c.get("fonte", "").startswith("TSE —")}
    cidade["contexto"] = [c for c in cidade["contexto"] if (c["ano"], c["turno"], c["cargo"]) in tse_ctx] + \
                         [c for c in ctx if (c["ano"], c["turno"], c["cargo"]) not in tse_ctx]

    # perfis dos candidatos (para ocupação, idade, etc.)
    perfis = {}
    with gzip.open(cand, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id_municipio"] == a.cd_ibge and r["ano"] and int(r["ano"]) >= a.desde:
                perfis[(r["ano"], r["sequencial"])] = r
    # candidaturas registradas em anos ainda sem resultado no espelho (ex.: 2024): nome, partido e
    # sequencial do TSE — servem para foto oficial e para confirmar quem concorreu
    com_resultado = set()
    with gzip.open(res, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id_municipio"] == a.cd_ibge and r["ano"]:
                com_resultado.add(r["ano"])
    cidade["candidaturas"] = {}
    for (ano_c, sq), r in perfis.items():
        if ano_c in com_resultado or r["cargo"] not in ("prefeito", "vereador", "vice-prefeito"):
            continue
        cidade["candidaturas"].setdefault(ano_c, []).append({
            "sq": sq, "urna": titulo(r["nome_urna"] or r["nome"]), "nome": titulo(r["nome"]), "cargo": r["cargo"],
            "partido": r["sigla_partido"], "nr": r["numero"], "ocupacao": r["ocupacao"] or None})
    for lst in cidade["candidaturas"].values():
        lst.sort(key=lambda c: (c["cargo"] != "prefeito", c["cargo"], c["urna"]))

    pessoas = Pessoas(cidade)
    eleicoes = {}
    with gzip.open(res, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id_municipio"] != a.cd_ibge or not r["ano"] or int(r["ano"]) < a.desde:
                continue
            if r["cargo"] not in ("prefeito", "vereador") or r["turno"] != "1":
                continue
            ano = r["ano"]
            if ano in cidade["eleicoes"] and cidade["eleicoes"][ano].get("nivel") == "secao":
                continue  # já existe detalhe do TSE para esse ano
            p = perfis.get((ano, r["sequencial_candidato"]), {})
            pid = pessoas.resolver(p.get("nome") or r["nome_candidato"], p.get("data_nascimento"),
                                   p.get("cpf"), p.get("titulo_eleitoral"),
                                   extra=f"bd:{r['id_candidato_bd']}" if r["id_candidato_bd"] else None)
            e = eleicoes.setdefault(ano, {"ano": int(ano), "data": r["data_eleicao"], "nivel": "municipio",
                                          "fonte": "TSE via Base dos Dados (resultados_candidato)",
                                          "locais": {}, "secoes": {}, "cargos": {}})
            c = e["cargos"].setdefault(r["cargo"], {"cargo": NOME_CARGO[r["cargo"]], "turno": 1,
                                                     "candidatos": [], "legendas": {}})
            c["candidatos"].append({
                "sq": r["sequencial_candidato"], "pid": pid, "nr": r["numero_candidato"],
                "nome": titulo(p.get("nome") or r["nome_candidato"]),
                "urna": titulo(p.get("nome_urna") or r["nome_candidato"]),
                "partido": r["sigla_partido"], "situacao": r["resultado"].replace("nao ", "não "),
                "ocupacao": p.get("ocupacao") or None, "genero": p.get("genero") or None,
                "idade": inteiro(p.get("idade")), "instrucao": p.get("instrucao") or None,
                "votos": inteiro(r["votos"]) or 0, "foto": None,
            })
    # vagas em disputa e votos por partido (nominais + legenda) — base dos quocientes
    vagas = {}
    with gzip.open(vagas_f, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id_municipio"] == a.cd_ibge and r["cargo"] in ("vereador", "prefeito"):
                vagas[(r["ano"], r["cargo"])] = inteiro(r["vagas"])
    partidos = {}
    with gzip.open(part_f, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id_municipio"] == a.cd_ibge and r["cargo"] == "vereador" and r["turno"] == "1":
                n, l = inteiro(r["votos_nominais"]) or 0, inteiro(r["votos_legenda"]) or 0
                partidos.setdefault(r["ano"], {})[r["sigla_partido"]] = {"nominais": n, "legenda": l, "total": n + l}
    for ano, e in eleicoes.items():
        for slug_c, c in e["cargos"].items():
            if (ano, slug_c) in vagas:
                c["vagas"] = vagas[(ano, slug_c)]
            if slug_c == "vereador" and ano in partidos:
                c["partidos"] = partidos[ano]
    for ano, e in eleicoes.items():
        for slug_c, c in e["cargos"].items():
            c["candidatos"].sort(key=lambda x: -x["votos"])
            t = next((x for x in cidade["contexto"] if x["ano"] == int(ano) and x["turno"] == 1
                      and x["cargo"] == slug_c), None)
            if t:
                c["totais"] = {k: t[k] for k in ("validos", "nominais", "legenda", "brancos", "nulos")}
        cidade["eleicoes"][ano] = e
    salvar(cidade)


# ---------------------------------------------------------------- TSE (dados abertos oficiais)

def arquivo_tse(pasta, nome_zip, url, baixar_flag):
    p = os.path.join(pasta, nome_zip)
    if not os.path.exists(p):
        if not baixar_flag:
            sys.exit(f"Falta {p}. Baixe de {url} ou rode com --baixar.")
        baixar(url, p)
    return p


def ler_csv_zip(caminho, filtro_nome=None):
    """Itera linhas (dict) de um CSV do TSE dentro do zip (latin-1, separador ';')."""
    with zipfile.ZipFile(caminho) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if filtro_nome:
            preferidos = [n for n in nomes if filtro_nome.lower() in n.lower()]
            nomes = preferidos or nomes
        nomes = [n for n in nomes if "brasil" not in n.lower()] or nomes
        for n in nomes:
            with z.open(n) as bruto:
                texto = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
                for linha in csv.DictReader(texto, delimiter=";"):
                    yield linha


def g(r, *nomes):
    for n in nomes:
        if n in r and r[n] is not None:
            return r[n]
    return None


def fotos_divulgacand(ano, uf, cd_mun, sqs, destino, municipal):
    """Baixa a foto oficial de cada candidato pelo DivulgaCand (TSE), um a um."""
    base = "https://divulgacandcontas.tse.jus.br/divulga/rest"
    try:
        with urllib.request.urlopen(f"{base}/v1/eleicao/ordinarias", timeout=60) as r:
            eleicoes = json.load(r)
    except Exception as ex:
        print(f"  (DivulgaCand indisponível: {ex})")
        return {}
    cand = [e for e in eleicoes if str(e.get("ano")) == str(ano) and str(e.get("nomeEleicao", "")).lower().find("turno") == -1 or str(e.get("ano")) == str(ano)]
    cand = [e for e in cand if str(e.get("ano")) == str(ano)]
    tipo = "M" if municipal else "F"
    escolha = [e for e in cand if str(e.get("tipoAbrangencia", "")).upper().startswith(tipo)] or cand
    if not escolha:
        print(f"  (DivulgaCand sem eleição de {ano})")
        return {}
    ue = cd_mun if municipal else uf
    ok = {}
    os.makedirs(destino, exist_ok=True)
    for e in escolha[:2]:
        for sq in sorted(sqs - set(ok)):
            try:
                with urllib.request.urlopen(f"{base}/arquivo/img/{e['id']}/{sq}/{ue}", timeout=30) as r:
                    dados = r.read()
                    if len(dados) > 1500 and r.headers.get_content_type().startswith("image"):
                        alvo = os.path.join(destino, f"{sq}.jpg")
                        open(alvo, "wb").write(dados)
                        ok[sq] = os.path.relpath(alvo, RAIZ).replace(os.sep, "/")
            except Exception:
                pass
    print(f"  {len(ok)} fotos baixadas do DivulgaCand (eleição {[e.get('id') for e in escolha[:2]]})")
    return ok


def cmd_tse(a):
    pasta = os.path.abspath(a.pasta)
    os.makedirs(pasta, exist_ok=True)
    uf = a.uf.upper()
    alvo = norm(a.municipio)
    cidade = carregar(uf, slug(a.municipio)) or nova_cidade(uf, a.municipio)
    pessoas = Pessoas(cidade)

    def _ano(ano):
        print(f"\n== {a.municipio}/{uf} — {ano}")
        f_secao = arquivo_tse(pasta, f"votacao_secao_{ano}_{uf}.zip",
                              f"{CDN}/votacao_secao/votacao_secao_{ano}_{uf}.zip", a.baixar)
        f_local = arquivo_tse(pasta, f"eleitorado_local_votacao_{ano}.zip",
                              f"{CDN}/eleitorado_locais_votacao/eleitorado_local_votacao_{ano}.zip", a.baixar)
        f_cand = arquivo_tse(pasta, f"consulta_cand_{ano}.zip",
                             f"{CDN}/consulta_cand/consulta_cand_{ano}.zip", a.baixar)
        f_munzona = arquivo_tse(pasta, f"votacao_candidato_munzona_{ano}.zip",
                                f"{CDN}/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip", a.baixar)
        f_detalhe = os.path.join(pasta, f"detalhe_votacao_munzona_{ano}.zip")
        if a.baixar and not os.path.exists(f_detalhe):
            try:
                baixar(f"{CDN}/detalhe_votacao_munzona/detalhe_votacao_munzona_{ano}.zip", f_detalhe)
            except Exception as ex:  # opcional
                print(f"  (sem detalhe_votacao_munzona: {ex})")
        f_foto = os.path.join(pasta, f"foto_cand{ano}_{uf}_div.zip")
        if a.fotos and a.baixar and not os.path.exists(f_foto):
            # o TSE já publicou o pacote de fotos em endereços diferentes conforme o ano
            for u in (f"https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes{ano}/fotos/foto_cand{ano}_{uf}_div.zip",
                      f"{CDN}/consulta_cand/foto_cand{ano}_{uf}_div.zip",
                      f"{CDN}/fotos/foto_cand{ano}_{uf}_div.zip"):
                try:
                    baixar(u, f_foto)
                    break
                except Exception as ex:
                    print(f"  (fotos não estão em {u}: {ex})")

        # 1) votos por seção do município (1º turno; 2º turno só p/ cargos majoritários)
        cd_mun = cidade["meta"].get("cd_tse")
        votos = {}      # (turno, cargo) -> {sq|"legenda:XX"|"branco"|"nulo": {sid: votos}}
        secoes, locais, numeros = {}, {}, {}
        data_eleicao = None
        for r in ler_csv_zip(f_secao, f"_{uf}"):
            if cd_mun:
                if r["CD_MUNICIPIO"] != cd_mun:
                    continue
            elif norm(r["NM_MUNICIPIO"]) != alvo:
                continue
            cd_mun = r["CD_MUNICIPIO"]
            cargo = CARGOS.get(r["CD_CARGO"])
            if not cargo:
                continue
            turno = int(r["NR_TURNO"])
            data_eleicao = data_eleicao or g(r, "DT_ELEICAO")
            zona, sec = int(r["NR_ZONA"]), int(r["NR_SECAO"])
            sid = f"{zona}-{sec}"
            lid = f"{zona}-{int(r['NR_LOCAL_VOTACAO'])}"
            secoes.setdefault(sid, {"zona": zona, "secao": sec, "local": lid})
            if lid not in locais:
                locais[lid] = {"zona": zona, "nr": int(r["NR_LOCAL_VOTACAO"]),
                               "nome": titulo(r["NM_LOCAL_VOTACAO"]),
                               "endereco": titulo(g(r, "DS_LOCAL_VOTACAO_ENDERECO") or ""),
                               "bairro": None, "lat": None, "lon": None}
            nr = r["NR_VOTAVEL"]
            sq = limpo(g(r, "SQ_CANDIDATO"))
            if nr == "95":
                chave = "branco"
            elif nr in ("96", "97"):
                chave = "nulo"
            elif sq:
                chave = sq
                numeros[sq] = nr
            elif len(nr) == 2:
                chave = f"legenda:{nr}"
            else:
                chave = "nulo"
            d = votos.setdefault((turno, cargo), {}).setdefault(chave, {})
            d[sid] = d.get(sid, 0) + int(r["QT_VOTOS"])
        if not cd_mun:
            sys.exit(f"Município {a.municipio} não encontrado em {f_secao}.")
        cidade["meta"]["cd_tse"] = cd_mun
        print(f"  {len(secoes)} seções, {len(locais)} locais, cargos: "
              f"{sorted({c for _, c in votos})}")

        # 2) bairro, coordenadas e eleitores aptos por seção
        for r in ler_csv_zip(f_local):
            if r.get("CD_MUNICIPIO") != cd_mun or g(r, "NR_TURNO") not in (None, "1"):
                continue
            zona, sec = int(r["NR_ZONA"]), int(r["NR_SECAO"])
            sid = f"{zona}-{sec}"
            lid = f"{zona}-{int(r['NR_LOCAL_VOTACAO'])}"
            aptos = inteiro(g(r, "QT_ELEITOR_SECAO", "QT_ELEITOR", "QT_APTOS"))
            if sid in secoes:
                secoes[sid]["aptos"] = (secoes[sid].get("aptos") or 0) + (aptos or 0)
            else:
                # seção agregada: os votos aparecem na principal
                principal = inteiro(g(r, "NR_SECAO_PRINCIPAL"))
                psid = f"{zona}-{principal}"
                if principal and psid in secoes:
                    secoes[psid]["aptos"] = (secoes[psid].get("aptos") or 0) + (aptos or 0)
                    secoes[psid].setdefault("agregadas", []).append(sec)
            if lid in locais:
                L = locais[lid]
                L["bairro"] = L["bairro"] or titulo(limpo(g(r, "NM_BAIRRO")) or "") or None
                lat, lon = limpo(g(r, "NR_LATITUDE")), limpo(g(r, "NR_LONGITUDE"))
                if lat and lon and L["lat"] is None:
                    try:
                        la, lo = float(lat.replace(",", ".")), float(lon.replace(",", "."))
                        if la and lo:
                            L["lat"], L["lon"] = round(la, 6), round(lo, 6)
                    except ValueError:
                        pass
                if not L["endereco"]:
                    L["endereco"] = titulo(g(r, "DS_ENDERECO") or "")
        for L in locais.values():
            L["bairro"] = L["bairro"] or "Não informado"

        # 3) perfil dos candidatos
        cargos_mun = {c for _, c in votos}
        perfis, partidos_nr = {}, {}
        for r in ler_csv_zip(f_cand, f"_{uf}"):
            if r.get("SG_UF") != uf:
                continue
            cargo = CARGOS.get(r.get("CD_CARGO"))
            if cargo not in cargos_mun:
                continue
            if cargo in ("prefeito", "vereador") and r.get("SG_UE") != cd_mun:
                continue
            perfis[r["SQ_CANDIDATO"]] = r
            partidos_nr[g(r, "NR_PARTIDO")] = g(r, "SG_PARTIDO")

        # 4) votação estadual de cada candidato (total e posição do município)
        por_mun = {}
        for r in ler_csv_zip(f_munzona, f"_{uf}"):
            if r.get("NR_TURNO") != "1" or CARGOS.get(r.get("CD_CARGO")) not in ("deputado_federal", "deputado_estadual", "senador", "governador"):
                continue
            sq = r["SQ_CANDIDATO"]
            v = inteiro(g(r, "QT_VOTOS_NOMINAIS_VALIDOS", "QT_VOTOS_NOMINAIS")) or 0
            d = por_mun.setdefault(sq, {})
            d[r["CD_MUNICIPIO"]] = d.get(r["CD_MUNICIPIO"], 0) + v
        ranking_uf = {}
        for sq, d in por_mun.items():
            total = sum(d.values())
            ordem = sorted(d.items(), key=lambda kv: -kv[1])
            pos = next((i + 1 for i, (m, _) in enumerate(ordem) if m == cd_mun), None)
            ranking_uf[sq] = {"total": total, "posMun": pos, "nMun": sum(1 for _, v in ordem if v > 0)}
        # posição de cada candidato no estado, dentro do cargo
        for cargo in ("deputado_federal", "deputado_estadual"):
            sqs = [sq for sq, p in perfis.items() if CARGOS.get(p.get("CD_CARGO")) == cargo and sq in ranking_uf]
            for i, sq in enumerate(sorted(sqs, key=lambda s: -ranking_uf[s]["total"])):
                ranking_uf[sq]["rank"] = i + 1

        # 5) fotos (só de quem teve voto no município)
        fotos_ok = {}
        if a.fotos and os.path.exists(f_foto):
            destino = os.path.join(RAIZ, "fotos", uf.lower(), slug(a.municipio), str(ano))
            com_voto = {k for vs in votos.values() for k in vs if k.isdigit()}
            with zipfile.ZipFile(f_foto) as z:
                for n in z.namelist():
                    m = re.search(r"(\d{9,})", os.path.basename(n))
                    if m and m.group(1) in com_voto:
                        os.makedirs(destino, exist_ok=True)
                        ext = os.path.splitext(n)[1].lower() or ".jpg"
                        alvo_foto = os.path.join(destino, m.group(1) + ext)
                        with z.open(n) as src, open(alvo_foto, "wb") as dst:
                            dst.write(src.read())
                        fotos_ok[m.group(1)] = os.path.relpath(alvo_foto, RAIZ).replace(os.sep, "/")
            print(f"  {len(fotos_ok)} fotos extraídas")
        if a.fotos and a.baixar:
            faltam = {k for vs in votos.values() for k in vs if k.isdigit()} - set(fotos_ok)
            if faltam:
                fotos_ok.update(fotos_divulgacand(ano, uf, cd_mun, faltam, os.path.join(RAIZ, "fotos", uf.lower(), slug(a.municipio), str(ano)),
                                                  municipal=bool(votos) and all(c in ("prefeito", "vereador") for _, c in votos)))

        # vagas em disputa (para quociente eleitoral)
        vagas = {}
        f_vagas = os.path.join(pasta, f"consulta_vagas_{ano}.zip")
        if a.baixar and not os.path.exists(f_vagas):
            try:
                baixar(f"{CDN}/consulta_vagas/consulta_vagas_{ano}.zip", f_vagas)
            except Exception as ex:
                print(f"  (sem consulta_vagas: {ex})")
        if os.path.exists(f_vagas):
            for r in ler_csv_zip(f_vagas, f"_{uf}"):
                cg = CARGOS.get(r.get("CD_CARGO"))
                if cg and r.get("SG_UE") in (cd_mun, uf):
                    vagas[cg] = inteiro(g(r, "QT_VAGAS", "QT_VAGA"))

        # 6) monta a eleição
        e = {"ano": int(ano), "data": data_eleicao, "nivel": "secao",
             "fonte": "TSE — Dados Abertos (votacao_secao, eleitorado_local_votacao, consulta_cand, votacao_candidato_munzona)",
             "locais": locais, "secoes": secoes, "cargos": {}}
        for (turno, cargo), dados in sorted(votos.items()):
            chave_cargo = cargo if turno == 1 else f"{cargo}_2t"
            brancos = sum(dados.get("branco", {}).values())
            nulos = sum(dados.get("nulo", {}).values())
            legendas = {}
            for k, d in dados.items():
                if k.startswith("legenda:"):
                    nrp = k.split(":")[1]
                    legendas[partidos_nr.get(nrp, nrp)] = {"total": sum(d.values()), "secoes": d}
            cands = []
            for sq, d in dados.items():
                if not sq.isdigit():
                    continue
                p = perfis.get(sq, {})
                nome = g(p, "NM_CANDIDATO") or f"Candidato {numeros.get(sq, sq)}"
                pid = pessoas.resolver(nome, limpo(g(p, "DT_NASCIMENTO")), limpo(g(p, "NR_CPF_CANDIDATO")),
                                       limpo(g(p, "NR_TITULO_ELEITORAL_CANDIDATO")))
                uf_info = ranking_uf.get(sq)
                cands.append({
                    "sq": sq, "pid": pid, "nr": numeros.get(sq) or g(p, "NR_CANDIDATO"),
                    "nome": titulo(nome), "urna": titulo(g(p, "NM_URNA_CANDIDATO") or nome),
                    "partido": g(p, "SG_PARTIDO"),
                    "federacao": titulo(limpo(g(p, "NM_FEDERACAO")) or "") or None,
                    "situacao": (limpo(g(p, "DS_SIT_TOT_TURNO")) or "").lower() or None,
                    "ocupacao": (limpo(g(p, "DS_OCUPACAO")) or "").lower() or None,
                    "genero": (limpo(g(p, "DS_GENERO")) or "").lower() or None,
                    "idade": inteiro(limpo(g(p, "NR_IDADE_DATA_POSSE"))),
                    "instrucao": (limpo(g(p, "DS_GRAU_INSTRUCAO")) or "").lower() or None,
                    "foto": fotos_ok.get(sq),
                    "votos": sum(d.values()), "secoes": d,
                    "uf": uf_info,
                })
            cands.sort(key=lambda x: -x["votos"])
            nominais = sum(c["votos"] for c in cands)
            leg = sum(v["total"] for v in legendas.values())
            e["cargos"][chave_cargo] = {
                "cargo": NOME_CARGO[cargo] + (" — 2º turno" if turno == 2 else ""), "turno": turno,
                "totais": {"nominais": nominais, "legenda": leg, "validos": nominais + leg,
                           "brancos": brancos, "nulos": nulos},
                "legendas": legendas, "candidatos": cands,
            }
            if cargo in ("vereador", "deputado_federal", "deputado_estadual") and turno == 1:
                partidos = {}
                for c in cands:
                    pp = partidos.setdefault(c["partido"] or "?", {"nominais": 0, "legenda": 0, "total": 0})
                    pp["nominais"] += c["votos"]; pp["total"] += c["votos"]
                for sig, v in legendas.items():
                    pp = partidos.setdefault(sig, {"nominais": 0, "legenda": 0, "total": 0})
                    pp["legenda"] += v["total"]; pp["total"] += v["total"]
                e["cargos"][chave_cargo]["partidos"] = partidos
                if cargo == "vereador" and vagas.get(cargo):
                    e["cargos"][chave_cargo]["vagas"] = vagas[cargo]
            print(f"  {chave_cargo}: {len(cands)} candidatos com voto, {nominais + leg} válidos")
        cidade["eleicoes"][str(ano)] = e

        # 7) contexto oficial (aptos, comparecimento) se o detalhe existir
        if os.path.exists(f_detalhe):
            agg = {}
            for r in ler_csv_zip(f_detalhe, f"_{uf}"):
                if r.get("CD_MUNICIPIO") != cd_mun:
                    continue
                cargo = CARGOS.get(r.get("CD_CARGO"))
                if not cargo:
                    continue
                k = (int(ano), int(r["NR_TURNO"]), cargo)
                t = agg.setdefault(k, {"aptos": 0, "secoes": 0, "comparecimento": 0, "abstencoes": 0,
                                       "brancos": 0, "nulos": 0, "nominais": 0, "legenda": 0})
                t["aptos"] += inteiro(g(r, "QT_APTOS")) or 0
                t["secoes"] += inteiro(g(r, "QT_SECOES_PRINCIPAIS", "QT_SECOES", "QT_TOTAL_SECOES")) or 0
                t["comparecimento"] += inteiro(g(r, "QT_COMPARECIMENTO")) or 0
                t["abstencoes"] += inteiro(g(r, "QT_ABSTENCOES")) or 0
                t["brancos"] += inteiro(g(r, "QT_VOTOS_BRANCOS")) or 0
                t["nulos"] += inteiro(g(r, "QT_TOTAL_VOTOS_NULOS", "QT_VOTOS_NULOS")) or 0
                t["nominais"] += inteiro(g(r, "QT_VOTOS_NOMINAIS_VALIDOS", "QT_VOTOS_NOMINAIS")) or 0
                t["legenda"] += inteiro(g(r, "QT_TOTAL_VOTOS_LEG_VALIDOS", "QT_VOTOS_LEGENDA_VALIDOS", "QT_VOTOS_LEGENDA")) or 0
            novos = {k for k in agg}
            cidade["contexto"] = [c for c in cidade["contexto"] if (c["ano"], c["turno"], c["cargo"]) not in novos]
            for (an, tu, ca), t in agg.items():
                t.update({"ano": an, "turno": tu, "cargo": ca, "validos": t["nominais"] + t["legenda"],
                          "fonte": "TSE — Dados Abertos (detalhe_votacao_munzona)"})
                cidade["contexto"].append(t)
            cidade["contexto"].sort(key=lambda c: (c["ano"], c["turno"], c["cargo"]))
    for ano in sorted(set(a.ano)):
        try:
            _ano(ano)
        except (SystemExit, Exception) as ex:
            if not a.continuar:
                raise
            print(f"  !! {ano} não importado: {ex}")
    salvar(cidade)


def cmd_manual(a):
    """Carrega votação municipal de um arquivo de fonte (data/fontes/*.json), marcada como parcial."""
    f = json.load(open(a.arquivo, encoding="utf-8"))
    cidade = carregar(f["uf"], slug(f["municipio"]))
    if cidade is None:
        sys.exit("Rode o seed antes (a cidade ainda não existe).")
    ano = str(f["ano"])
    if cidade["eleicoes"].get(ano, {}).get("nivel") == "secao" and not a.forcar:
        sys.exit(f"{ano} já tem votação por seção do TSE; não sobrescrevo com dado parcial.")
    pessoas = Pessoas(cidade)
    e = {"ano": int(ano), "data": f.get("data"), "nivel": "municipio", "parcial": True,
         "fonte": f["fonte"], "locais": {}, "secoes": {}, "cargos": {}}
    for cargo, c in f["cargos"].items():
        cands = []
        for i, (nome, partido, votos, situ) in enumerate(c["candidatos"]):
            pid = pessoas.resolver(nome, extra=f"manual:{norm(nome)}")
            cands.append({"sq": f"m{ano}{cargo[:3]}{i:03d}", "pid": pid, "nr": "", "nome": nome, "urna": nome,
                          "partido": partido or None, "situacao": situ or None, "votos": votos, "foto": None})
        cands.sort(key=lambda x: -x["votos"])
        t = dict(c["totais"])
        t["nominais"] = sum(x["votos"] for x in cands)
        e["cargos"][cargo] = {"cargo": NOME_CARGO[cargo], "turno": 1, "parcial": True, "url": c.get("url"),
                              "totais": t, "candidatos": cands, "legendas": {}}
    cidade["eleicoes"][ano] = e
    vistos = {(x["ano"], x["turno"], x["cargo"]) for x in cidade["contexto"]}
    for cargo, c in f["cargos"].items():
        if (int(ano), 1, cargo) not in vistos:
            cidade["contexto"].append({"ano": int(ano), "turno": 1, "cargo": cargo, "aptos": f.get("aptos"), "secoes": None,
                                       "comparecimento": f.get("comparecimento"), "abstencoes": f.get("abstencoes"),
                                       "validos": c["totais"].get("validos"), "brancos": c["totais"].get("brancos"),
                                       "nulos": c["totais"].get("nulos"), "nominais": None, "legenda": None, "fonte": f["fonte"]})
    cidade["contexto"].sort(key=lambda c: (c["ano"], c["turno"], c["cargo"]))
    salvar(cidade)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed", help="totais municipais históricos (Base dos Dados)")
    s.add_argument("--municipio", required=True)
    s.add_argument("--uf", default="CE")
    s.add_argument("--cd-ibge", help="código IBGE do município (Varjota = 2313955)")
    s.add_argument("--desde", type=int, default=2010)
    s.add_argument("--pasta", default=os.path.join(RAIZ, "tse_raw"))
    t = sub.add_parser("tse", help="detalhe por seção/bairro a partir dos dados abertos do TSE")
    t.add_argument("--municipio", required=True)
    t.add_argument("--uf", default="CE")
    t.add_argument("--ano", action="append", required=True)
    t.add_argument("--pasta", default=os.path.join(RAIZ, "tse_raw"))
    t.add_argument("--baixar", action="store_true", help="baixa do cdn.tse.jus.br o que faltar")
    t.add_argument("--sem-fotos", dest="fotos", action="store_false")
    t.add_argument("--continuar", action="store_true", help="se um ano falhar (arquivo ainda não publicado), segue para os outros")
    m = sub.add_parser("manual", help="votação municipal parcial a partir de data/fontes/*.json")
    m.add_argument("arquivo")
    m.add_argument("--forcar", action="store_true")
    a = ap.parse_args()
    {"seed": cmd_seed, "tse": cmd_tse, "manual": cmd_manual}[a.cmd](a)


if __name__ == "__main__":
    main()
