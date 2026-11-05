"""Raio-X de um candidato no estado inteiro, direto do TSE (votacao_candidato_munzona).
Uso: python3 scripts/candidato_tse.py "NOME COMPLETO" UF ANO [ANO...]  -> data/candidatos/<slug>.json"""
import csv, io, json, os, re, sys, unicodedata, urllib.request, zipfile
nome, uf, anos = sys.argv[1].upper(), sys.argv[2].upper(), sys.argv[3:]
slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFD", nome.lower()).encode("ascii", "ignore").decode()).strip("-")
out = {"nome": nome, "uf": uf, "fonte": "TSE, votacao_candidato_munzona", "eleicoes": {}}
for ano in anos:
    url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip"
    print("baixando", url, flush=True)
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url, timeout=600).read()))
    arq = [n for n in z.namelist() if n.upper().endswith(f"_{uf}.CSV")][0]
    rows = csv.DictReader(io.TextIOWrapper(z.open(arq), encoding="latin-1"), delimiter=";")
    cargo = None; meus = {}; todos = {}  # todos[(cargo,turno)][mun][sq] = votos
    for r in rows:
        k = (r["DS_CARGO"], r["NR_TURNO"]); mun = r["NM_MUNICIPIO"]; sq = r["SQ_CANDIDATO"]
        v = int(r.get("QT_VOTOS_NOMINAIS_VALIDOS") or r.get("QT_VOTOS_NOMINAIS") or 0)
        todos.setdefault(k, {}).setdefault(mun, {}); todos[k][mun][sq] = todos[k][mun].get(sq, 0) + v
        if r["NM_CANDIDATO"].upper() == nome:
            meus.setdefault(k, {"sq": sq, "urna": r["NM_URNA_CANDIDATO"], "numero": r["NR_CANDIDATO"], "partido": r["SG_PARTIDO"],
                                "situacao": r["DS_SIT_TOT_TURNO"], "cargo": r["DS_CARGO"], "turno": r["NR_TURNO"]})
    for k, info in meus.items():
        sq = info["sq"]; T = todos[k]; tot = {}
        for mun, d in T.items():
            for s, v in d.items(): tot[s] = tot.get(s, 0) + v
        ordem = sorted(tot, key=lambda s: -tot[s])
        muns = []
        for mun, d in T.items():
            v = d.get(sq, 0)
            if v: muns.append({"municipio": mun, "votos": v, "pos": sorted(d, key=lambda s: -d[s]).index(sq) + 1, "candidatos": len(d), "nominais": sum(d.values())})
        muns.sort(key=lambda m: -m["votos"])
        info.update(total=tot.get(sq, 0), pos_estado=ordem.index(sq) + 1, candidatos_estado=len(ordem), municipios_com_voto=len(muns),
                    municipios_total=len(T), primeiro_lugar_em=[m["municipio"] for m in muns if m["pos"] == 1], municipios=muns)
        out["eleicoes"].setdefault(ano, []).append(info)
        print(ano, info["cargo"], info["urna"], info["total"], "votos, pos", info["pos_estado"], flush=True)
os.makedirs("data/candidatos", exist_ok=True)
json.dump(out, open(f"data/candidatos/{slug}.json", "w"), ensure_ascii=False, indent=1)
