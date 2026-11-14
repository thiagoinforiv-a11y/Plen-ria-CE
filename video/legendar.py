#!/usr/bin/env python3
"""Legenda dinâmica (estilo Reels/TikTok) queimada no vídeo: 1 a 3 palavras por vez, palavra falada em destaque.
Entrada: o mapa da mixagem (com "palavras", tempo de cada palavra no vídeo) ou um JSON [{t, d, p}].
Uso: python3 video/legendar.py --video raw.mp4 --palavras entregas/X/a.mapa.json --saida final.mp4 [--y 1500] [--tam 64]
Palavras com número, sigla ou nome próprio ganham destaque automático (dourado e maior)."""
import argparse, json, os, re, subprocess, tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))

def tempo(s):
    h = int(s // 3600); m = int(s % 3600 // 60); return f"{h}:{m:02d}:{s % 60:05.2f}"

def grupos(pal, maxp=3, maxc=18):
    """Quebra a fala em blocos curtos: no máximo 3 palavras/18 letras, e corta em pausa ou pontuação."""
    out, cur = [], []
    for i, w in enumerate(pal):
        cur.append(w)
        prox = pal[i + 1] if i + 1 < len(pal) else None
        pausa = prox is None or prox["t"] - (w["t"] + w["d"]) > 0.35 or prox.get("cena") != w.get("cena")
        cheio = len(cur) >= maxp or sum(len(x["p"]) for x in cur) >= maxc
        if pausa or cheio or re.search(r"[.,;:!?]$", w["p"]): out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def destaque(p):
    return bool(re.search(r"\d", p)) or p.isupper() and len(p) > 1 or (p[:1].isupper() and len(p) > 3)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--video", required=True); ap.add_argument("--palavras", required=True); ap.add_argument("--saida", required=True)
    ap.add_argument("--y", type=int, default=1480); ap.add_argument("--tam", type=int, default=66); ap.add_argument("--crf", default="25"); ap.add_argument("--estilo", default="plenaria", choices=["plenaria", "tela"]); ap.add_argument("--titulo", default=""); ap.add_argument("--titulo-dur", type=float, default=4.0)
    a = ap.parse_args()
    d = json.load(open(a.palavras, encoding="utf-8")); pal = d["palavras"] if isinstance(d, dict) else d
    pal = [w for w in pal if w["p"].strip()]
    OURO, BRANCO, SOMBRA = "&H0066D1FF&", "&H00EAF1F3&", "&H80000000&"
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
           "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           f"Style: L,Oswald,{a.tam},{BRANCO},{BRANCO},&H00101010&,{SOMBRA},-1,0,0,0,100,100,1,0,1,5,3,5,60,60,0,1", "",
           "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    if a.estilo == "tela":   # gravação de tela estilo TikTok: frase como foi falada, branca com contorno preto, sem destaque de cor
        ass[ass.index(next(x for x in ass if x.startswith("Style: L,")))] = f"Style: L,Montserrat,{a.tam},&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H00000000&,-1,0,0,0,100,100,0,0,1,7,0,5,60,60,0,1"
        ass.insert(ass.index("[Events]") - 1, f"Style: T,Montserrat,{int(a.tam * 1.15)},&H00111111&,&H00111111&,&H00FFFFFF&,&H00FFFFFF&,-1,0,0,0,100,100,0,0,3,14,0,5,60,60,0,1")
        if a.titulo:
            for k, linha in enumerate(a.titulo.split("|")):
                ass.append(f"Dialogue: 1,{tempo(0)},{tempo(a.titulo_dur)},T,,0,0,0,,{{\\pos(540,{330 + k * int(a.tam * 1.75)})\\fad(150,250)}}{linha}")
        for g in grupos(pal, maxp=3, maxc=22):
            ini, fim = g[0]["t"], g[-1]["t"] + g[-1]["d"] + 0.1
            ass.append(f"Dialogue: 0,{tempo(ini)},{tempo(fim)},L,,0,0,0,,{{\\pos(540,{a.y})\\fad(60,0)}}" + " ".join(w["p"] for w in g))
        g_vazio = []
    for g in ([] if a.estilo == "tela" else grupos(pal)):
        fim_g = g[-1]["t"] + g[-1]["d"] + 0.12
        for i, w in enumerate(g):
            ini = w["t"]; fim = g[i + 1]["t"] if i + 1 < len(g) else fim_g
            partes = []
            for j, x in enumerate(g):
                txt = x["p"].upper().replace("{", "").replace("}", "")
                if j > i: partes.append(r"{\alpha&HFF&}" + txt); continue      # ainda não falada: reserva o espaço
                cor = OURO if destaque(x["p"]) else BRANCO
                if j == i:   # palavra sendo dita: entra maior e assenta (pop)
                    partes.append(r"{\alpha&H00&\c" + cor + r"\fscx128\fscy128\t(0,120,\fscx100\fscy100)}" + txt + r"{\fscx100\fscy100}")
                else:
                    partes.append(r"{\alpha&H00&\c" + cor + "}" + txt)
            intro = r"{\pos(540," + str(a.y) + r")" + (r"\fad(80,0)" if i == 0 else "") + "}"
            ass.append(f"Dialogue: 0,{tempo(ini)},{tempo(fim)},L,,0,0,0,," + intro + " ".join(partes))
    tmp = tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8"); tmp.write("\n".join(ass)); tmp.close()
    fontes = os.path.join(RAIZ, "fontes", "ttf")
    if a.estilo == "tela" and not os.path.exists(os.path.join(fontes, "Montserrat-800.ttf")):
        from fontTools.ttLib import TTFont
        f = TTFont(os.path.join(RAIZ, "fontes", "montserrat-latin-800-normal.woff2")); f.flavor = None; f.save(os.path.join(fontes, "Montserrat-800.ttf"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"ass={tmp.name}:fontsdir={fontes}", "-c:v", "libx264", "-crf", a.crf, "-maxrate", "2200k", "-bufsize", "4400k", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", a.saida], check=True)
    os.remove(tmp.name); print("✔ legenda", a.saida)

if __name__ == "__main__":
    main()
