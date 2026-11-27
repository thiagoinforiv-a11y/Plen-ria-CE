#!/usr/bin/env python3
"""Limpa o bruto falado antes de editar (ideia dos agentes "cut-silences" e "cut-mistakes" do herk-edit-kit, MIT; código nosso).
1) Corta silêncios: mantém só a fala (com folga), juntando pausas curtas.
2) Aponta tropeços para revisão: palavra repetida colada ("a a"), frase recomeçada (mesmas 2–4 palavras de novo em até 4 s).
   Tropeço NÃO é cortado sozinho: repetição pode ser ênfase. Revise o .md e passe os aprovados em --cortes.
Uso: python3 video/cortar.py --video bruto.mp4 --palavras palavras.json --saida limpo.mp4 [--pausa 0.35] [--cortes aprovados.json]
Saídas: limpo.mp4, limpo.palavras.json (tempos já no vídeo novo) e limpo.tropecos.md."""
import argparse, json, re, subprocess, unicodedata

def norm(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())

def tropecos(P):
    out = []
    for i in range(1, len(P)):
        if norm(P[i]["p"]) and norm(P[i]["p"]) == norm(P[i - 1]["p"]) and P[i]["t"] - P[i - 1]["t"] < 1.2:
            out.append({"tipo": "repetição", "ini": P[i - 1]["t"], "fim": P[i]["t"], "remove": P[i - 1]["p"], "contexto": " ".join(w["p"] for w in P[max(0, i - 4): i + 5])})
    for n in (4, 3):
        for i in range(len(P) - n):
            a = [norm(w["p"]) for w in P[i:i + n]]
            for j in range(i + n, min(len(P) - n + 1, i + n + 12)):
                if P[j]["t"] - P[i]["t"] > 2.5: break
                if [norm(w["p"]) for w in P[j:j + n]] == a and all(a):
                    if not any(c["ini"] - 0.05 <= P[i]["t"] <= c["fim"] for c in out):
                        out.append({"tipo": "recomeço", "ini": P[i]["t"], "fim": P[j]["t"], "remove": " ".join(w["p"] for w in P[i:j]), "contexto": " ".join(w["p"] for w in P[max(0, i - 3): j + n + 3])})
                    break
    return sorted(out, key=lambda c: c["ini"])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--video", required=True); ap.add_argument("--palavras", required=True); ap.add_argument("--saida", required=True)
    ap.add_argument("--pausa", type=float, default=0.35); ap.add_argument("--antes", type=float, default=0.10); ap.add_argument("--depois", type=float, default=0.15); ap.add_argument("--cortes")
    a = ap.parse_args(); P = [w for w in json.load(open(a.palavras, encoding="utf-8")) if w["p"].strip()]
    corte = [(c["ini"], c["fim"]) for c in json.load(open(a.cortes))["cortes"]] if a.cortes else []
    P = [w for w in P if not any(s <= w["t"] < e for s, e in corte)]
    seg = []
    for w in P:
        s, e = max(0, w["t"] - a.antes), w["t"] + w["d"] + a.depois
        if seg and s - seg[-1][1] < a.pausa: seg[-1][1] = max(seg[-1][1], e)
        else: seg.append([s, e])
    expr = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in seg)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"select='{expr}',setpts=N/FRAME_RATE/TB", "-af", f"aselect='{expr}',asetpts=N/SR/TB",
                    "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", a.saida], check=True)
    # tempos novos das palavras
    novo, acc = [], 0.0
    for s, e in seg:
        for w in P:
            if s <= w["t"] < e: novo.append({**w, "t": round(acc + w["t"] - s, 3)})
        acc += e - s
    base = a.saida.rsplit(".", 1)[0]
    json.dump(novo, open(base + ".palavras.json", "w", encoding="utf-8"), ensure_ascii=False)
    T = tropecos(novo)
    with open(base + ".tropecos.md", "w", encoding="utf-8") as f:
        f.write(f"# Tropeços para revisar ({len(T)})\n\nTempos no vídeo limpo. Repetição pode ser ênfase: confira antes de cortar.\n\n")
        for c in T: f.write(f"- **{c['tipo']}** {c['ini']:.2f}–{c['fim']:.2f} s · tira: \"{c['remove']}\" · contexto: …{c['contexto']}…\n")
    dur0 = P[-1]["t"] + P[-1]["d"] if P else 0
    print(f"✔ {a.saida}: {len(seg)} trechos, {acc:.1f} s de fala (silêncio cortado); {len(T)} tropeço(s) em {base}.tropecos.md")

if __name__ == "__main__":
    main()
