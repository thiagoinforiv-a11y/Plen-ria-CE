"""VARJOTA 2028 — O RAIO-X DO PODER · versão em PARTÍCULAS (voz 1,4×).

Cada frase da narração ganha uma ilustração formada por partículas:
ícones desenhados (urna, Câmara, prefeitura, cifrão, balança...), números
gigantes e os próprios infográficos, que se montam a partir das partículas
e depois "cristalizam" em versão nítida.

Uso: python3 particulas.py <modelo_piper.onnx> <pasta_trabalho>
"""
import math, re, subprocess, sys, wave
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ARGV = list(sys.argv)
MODEL, WORK = sys.argv[1], Path(sys.argv[2]); WORK.mkdir(parents=True, exist_ok=True)
# reaproveita roteiro, dados e cenas do documentário (sem executar TTS/render)
src = (HERE / "docu.py").read_text().split("# ------------------------------------------------------------------ fala (TTS)")[0]
G = {"__file__": str(HERE / "docu.py"), "__name__": "roteiro"}
sys.argv = [sys.argv[0], MODEL, str(WORK / "_docu")]
exec(compile(src, "docu.py", "exec"), G)
S = G["S"]
from doc_engine import (W, H, FPS, F, FS, GOLD, GOLD_L, WHITE, GREY, SIT, OPO, BG, background, wrap, subtitles,
                        chrome, Title, Chapter, BigNum, HBars, VBars, Duel, Parliament, Bullets, Table, MapScene, Lines,
                        Timeline, Quote, ease)
docu_falar = None

N_SHAPE, N_DUST = 9000, 1400
SR = 22050
BASE = HERE.parent


# ================================================================= ícones (desenhados em máscara colorida)
def canvas():
    return Image.new("RGB", (W, H), (0, 0, 0))


def box_center(region):
    x0, y0, x1, y1 = region
    return (x0 + x1) / 2, (y0 + y1) / 2, min(x1 - x0, y1 - y0)


def ic_urna(d, cx, cy, s, c):
    u = s / 10
    d.rounded_rectangle([cx - 4 * u, cy - 1 * u, cx + 4 * u, cy + 4 * u], u * .4, fill=c)
    d.rectangle([cx - 2.6 * u, cy - .3 * u, cx + 2.6 * u, cy + .2 * u], fill=(0, 0, 0))
    d.polygon([(cx - 1.6 * u, cy - 4 * u), (cx + 1.4 * u, cy - 4.4 * u), (cx + 1.7 * u, cy - .2 * u), (cx - 1.3 * u, cy + .1 * u)], fill=WHITE)
    d.line([(cx - .9 * u, cy - 3 * u), (cx + .9 * u, cy - 3.2 * u)], fill=(0, 0, 0), width=int(u * .25))
    d.line([(cx - .8 * u, cy - 2.2 * u), (cx + .6 * u, cy - 2.4 * u)], fill=(0, 0, 0), width=int(u * .25))
    d.text((cx, cy + 2 * u), "VOTO", font=F("Bold", int(u * 1.1)), fill=(0, 0, 0), anchor="mm")


def ic_camara(d, cx, cy, s, c):
    u = s / 10
    d.polygon([(cx - 4.6 * u, cy - 1.6 * u), (cx, cy - 4.4 * u), (cx + 4.6 * u, cy - 1.6 * u)], fill=c)
    d.rectangle([cx - 4.4 * u, cy - 1.3 * u, cx + 4.4 * u, cy - .8 * u], fill=c)
    for k in range(6):
        x = cx - 3.6 * u + k * 1.44 * u
        d.rectangle([x - .32 * u, cy - .6 * u, x + .32 * u, cy + 3.2 * u], fill=WHITE)
    d.rectangle([cx - 4.8 * u, cy + 3.4 * u, cx + 4.8 * u, cy + 4.1 * u], fill=c)


def ic_prefeitura(d, cx, cy, s, c):
    u = s / 10
    d.rectangle([cx - 4 * u, cy - 1 * u, cx + 4 * u, cy + 4 * u], fill=c)
    d.rectangle([cx - 1.2 * u, cy - 2.8 * u, cx + 1.2 * u, cy - 1 * u], fill=c)
    d.line([(cx, cy - 2.8 * u), (cx, cy - 5 * u)], fill=WHITE, width=int(u * .25))
    d.polygon([(cx, cy - 5 * u), (cx + 1.6 * u, cy - 4.5 * u), (cx, cy - 4 * u)], fill=GOLD_L)
    for r in range(2):
        for k in range(4):
            x = cx - 3 * u + k * 2 * u
            d.rectangle([x - .45 * u, cy - .2 * u + r * 1.8 * u, x + .45 * u, cy + .9 * u + r * 1.8 * u], fill=(0, 0, 0))
    d.rectangle([cx - .7 * u, cy + 2.4 * u, cx + .7 * u, cy + 4 * u], fill=(0, 0, 0))


def ic_cifrao(d, cx, cy, s, c):
    d.text((cx, cy), "R$", font=FS(int(s * .62)), fill=c, anchor="mm")
    u = s / 10
    for k in range(3):
        d.ellipse([cx + 3.2 * u, cy + 1.8 * u - k * .9 * u, cx + 5.4 * u, cy + 2.6 * u - k * .9 * u], fill=GOLD_L, outline=(0, 0, 0))


def ic_cruz(d, cx, cy, s, c):
    u = s / 10
    d.rounded_rectangle([cx - 1.4 * u, cy - 4 * u, cx + 1.4 * u, cy + 4 * u], u * .4, fill=c)
    d.rounded_rectangle([cx - 4 * u, cy - 1.4 * u, cx + 4 * u, cy + 1.4 * u], u * .4, fill=c)
    d.ellipse([cx - 4.8 * u, cy - 4.8 * u, cx + 4.8 * u, cy + 4.8 * u], outline=WHITE, width=int(u * .3))


def ic_livro(d, cx, cy, s, c):
    u = s / 10
    d.polygon([(cx, cy - 2 * u), (cx - 4.4 * u, cy - 3 * u), (cx - 4.4 * u, cy + 3 * u), (cx, cy + 4 * u)], fill=c)
    d.polygon([(cx, cy - 2 * u), (cx + 4.4 * u, cy - 3 * u), (cx + 4.4 * u, cy + 3 * u), (cx, cy + 4 * u)], fill=WHITE)
    for k in range(4):
        d.line([(cx + .8 * u, cy - 1 * u + k * 1.1 * u), (cx + 3.6 * u, cy - 1.5 * u + k * 1.1 * u)], fill=(0, 0, 0), width=int(u * .2))


def ic_balanca(d, cx, cy, s, c):
    u = s / 10
    d.rectangle([cx - .25 * u, cy - 3.6 * u, cx + .25 * u, cy + 3.4 * u], fill=c)
    d.rectangle([cx - 2 * u, cy + 3.2 * u, cx + 2 * u, cy + 3.9 * u], fill=c)
    d.line([(cx - 4 * u, cy - 3 * u), (cx + 4 * u, cy - 3 * u)], fill=c, width=int(u * .4))
    for sx in (-1, 1):
        x = cx + sx * 4 * u
        d.line([(x, cy - 3 * u), (x - 1.4 * u, cy + .6 * u)], fill=WHITE, width=int(u * .12))
        d.line([(x, cy - 3 * u), (x + 1.4 * u, cy + .6 * u)], fill=WHITE, width=int(u * .12))
        d.chord([x - 1.8 * u, cy - .6 * u, x + 1.8 * u, cy + 1.8 * u], 0, 180, fill=c)
    d.ellipse([cx - .7 * u, cy - 4.3 * u, cx + .7 * u, cy - 2.9 * u], fill=GOLD_L)


def ic_pin(d, cx, cy, s, c):
    u = s / 10
    d.ellipse([cx - 2.6 * u, cy - 4.6 * u, cx + 2.6 * u, cy + .6 * u], fill=c)
    d.polygon([(cx - 2.3 * u, cy - .6 * u), (cx + 2.3 * u, cy - .6 * u), (cx, cy + 3.6 * u)], fill=c)
    d.ellipse([cx - 1 * u, cy - 3 * u, cx + 1 * u, cy - 1 * u], fill=(0, 0, 0))
    d.ellipse([cx - 4.5 * u, cy + 3 * u, cx + 4.5 * u, cy + 4.4 * u], outline=WHITE, width=int(u * .2))


def ic_pessoas(d, cx, cy, s, c):
    u = s / 10
    for k, (dx, sc, col) in enumerate([(-3, .8, SIT), (3, .8, OPO), (0, 1, c)]):
        x = cx + dx * u; r = 1.2 * u * sc
        d.ellipse([x - r, cy - 2.6 * u * sc - r, x + r, cy - 2.6 * u * sc + r], fill=col)
        d.chord([x - 2.4 * u * sc, cy - .9 * u * sc, x + 2.4 * u * sc, cy + 3.9 * u * sc], 180, 360, fill=col)
        d.rectangle([x - 2.4 * u * sc, cy + 1.5 * u * sc, x + 2.4 * u * sc, cy + 2.4 * u * sc], fill=col)


def ic_ruptura(d, cx, cy, s, c):
    u = s / 10
    for sx, col in ((-1, SIT), (1, OPO)):
        x = cx + sx * 2.4 * u
        d.rounded_rectangle([x - 1.6 * u, cy - 1 * u, x + 1.6 * u, cy + 1 * u], u, outline=col, width=int(u * .5))
    d.line([(cx - .3 * u, cy - 3 * u), (cx + .5 * u, cy - 1.6 * u), (cx - .5 * u, cy - .6 * u), (cx + .3 * u, cy + .6 * u)], fill=GOLD_L, width=int(u * .3))
    d.line([(cx - .3 * u, cy + 3 * u), (cx + .3 * u, cy + 1.6 * u)], fill=GOLD_L, width=int(u * .3))


def ic_grafico(d, cx, cy, s, c):
    u = s / 10
    for k, h in enumerate([2, 3.2, 2.6, 4.4, 6]):
        x = cx - 4 * u + k * 2 * u
        d.rectangle([x - .7 * u, cy + 3.5 * u - h * u, x + .7 * u, cy + 3.5 * u], fill=c if k < 4 else GOLD_L)
    d.line([(cx - 4.6 * u, cy + 3.8 * u), (cx + 4.6 * u, cy + 3.8 * u)], fill=WHITE, width=int(u * .25))
    d.line([(cx - 4 * u, cy - .5 * u), (cx - 2 * u, cy - 1.2 * u), (cx, cy - .4 * u), (cx + 2 * u, cy - 2.4 * u), (cx + 4 * u, cy - 4 * u)], fill=WHITE, width=int(u * .3))


def ic_microfone(d, cx, cy, s, c):
    u = s / 10
    d.rounded_rectangle([cx - 1.5 * u, cy - 4.4 * u, cx + 1.5 * u, cy + .6 * u], 1.5 * u, fill=c)
    d.arc([cx - 2.8 * u, cy - 2 * u, cx + 2.8 * u, cy + 2.2 * u], 0, 180, fill=WHITE, width=int(u * .35))
    d.rectangle([cx - .2 * u, cy + 2.2 * u, cx + .2 * u, cy + 3.6 * u], fill=WHITE)
    d.rectangle([cx - 1.8 * u, cy + 3.5 * u, cx + 1.8 * u, cy + 4 * u], fill=WHITE)
    for k in range(3):
        d.arc([cx - (3.8 + k) * u, cy - (4.2 + k) * u, cx + (3.8 + k) * u, cy + (1.6 + k) * u], 300, 340, fill=GOLD_L, width=int(u * .25))
        d.arc([cx - (3.8 + k) * u, cy - (4.2 + k) * u, cx + (3.8 + k) * u, cy + (1.6 + k) * u], 200, 240, fill=GOLD_L, width=int(u * .25))


def ic_lupa(d, cx, cy, s, c):
    u = s / 10
    d.ellipse([cx - 3.6 * u, cy - 3.6 * u, cx + 1.6 * u, cy + 1.6 * u], outline=c, width=int(u * .7))
    d.line([(cx + 1 * u, cy + 1 * u), (cx + 4 * u, cy + 4 * u)], fill=c, width=int(u * 1.1))
    for k, h in enumerate([1, 1.8, 2.6]):
        x = cx - 2.4 * u + k * 1.1 * u
        d.rectangle([x - .3 * u, cy + .6 * u - h * u, x + .3 * u, cy + .6 * u], fill=WHITE)


def ic_gota(d, cx, cy, s, c):
    u = s / 10
    d.ellipse([cx - 3 * u, cy - 1 * u, cx + 3 * u, cy + 5 * u], fill=OPO)
    d.polygon([(cx - 2.7 * u, cy + 1 * u), (cx + 2.7 * u, cy + 1 * u), (cx, cy - 5 * u)], fill=OPO)
    d.arc([cx - 1.8 * u, cy + .2 * u, cx + 1.8 * u, cy + 3.8 * u], 100, 170, fill=WHITE, width=int(u * .35))


def ic_casa_rural(d, cx, cy, s, c):
    u = s / 10
    d.ellipse([cx + 1.5 * u, cy - 4.5 * u, cx + 4 * u, cy - 2 * u], fill=GOLD_L)
    d.chord([cx - 6 * u, cy + .5 * u, cx + 2 * u, cy + 6 * u], 180, 360, fill=c)
    d.chord([cx - 2 * u, cy + 1 * u, cx + 6 * u, cy + 6.5 * u], 180, 360, fill=SIT)
    d.rectangle([cx - 2.6 * u, cy - .8 * u, cx - .2 * u, cy + 1.6 * u], fill=WHITE)
    d.polygon([(cx - 3 * u, cy - .8 * u), (cx - 1.4 * u, cy - 2.2 * u), (cx + .2 * u, cy - .8 * u)], fill=OPO)


def ic_estrela(d, cx, cy, s, c):
    u = s / 10
    pts = []
    for k in range(10):
        r = 4.6 * u if k % 2 == 0 else 1.9 * u
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=c)


def ic_interrog(d, cx, cy, s, c):
    d.text((cx, cy), "?", font=FS(int(s * .95)), fill=c, anchor="mm")


def ic_calendario(d, cx, cy, s, c):
    u = s / 10
    d.rounded_rectangle([cx - 4.4 * u, cy - 3.6 * u, cx + 4.4 * u, cy + 4 * u], u * .5, outline=c, width=int(u * .4))
    d.rectangle([cx - 4.4 * u, cy - 3.6 * u, cx + 4.4 * u, cy - 1.8 * u], fill=c)
    for sx in (-2.4, 2.4):
        d.rectangle([cx + sx * u - .3 * u, cy - 4.6 * u, cx + sx * u + .3 * u, cy - 2.8 * u], fill=WHITE)
    d.text((cx, cy + 1.2 * u), "2028", font=F("Bold", int(u * 2.5)), fill=GOLD_L, anchor="mm")


ICONS = dict(urna=(ic_urna, "Voto e eleitorado"), camara=(ic_camara, "Câmara Municipal"), prefeitura=(ic_prefeitura, "Prefeitura"),
             cifrao=(ic_cifrao, "Dinheiro público"), cruz=(ic_cruz, "Saúde"), livro=(ic_livro, "Educação"),
             balanca=(ic_balanca, "Justiça e controle"), pin=(ic_pin, "Território"), pessoas=(ic_pessoas, "Lideranças"),
             ruptura=(ic_ruptura, "Rompimento"), grafico=(ic_grafico, "Crescimento"), microfone=(ic_microfone, "Eleição estadual e federal"),
             lupa=(ic_lupa, "Investigação"), gota=(ic_gota, "Saneamento"), rural=(ic_casa_rural, "Zona rural"),
             estrela=(ic_estrela, "Destaque"), interrog=(ic_interrog, "A pergunta"), calendario=(ic_calendario, "2028"))

KEYS = [(r"ministério público|\bmp\b|processo|cassação|justiça|\btac\b|\btre\b|multa|operação|condenação|denúncia|ajustamento", "balanca"),
        (r"saneamento|cagece", "gota"), (r"saúde|\bubs\b", "cruz"), (r"educação|ideb|escola", "livro"),
        (r"rompi|rompeu|afast|ruptura", "ruptura"),
        (r"receita|milh|investimento|dinheiro|orçamento|gasto|despesa|arrecada|tesouro|reais", "cifrao"),
        (r"governador|senado|presidente|deputad|estadual|ciro|lula|elmano|camilo|cid gomes", "microfone"),
        (r"rural|campo|jatobá|angelim|transval|distrito|comunidade", "rural"),
        (r"bairro|mapa|local de votação|locais|sede|território|ponto", "pin"),
        (r"câmara|vereador|cadeira|bancada|quociente|lista", "camara"),
        (r"prefeit|vice|gestão|administração|governo", "prefeitura"),
        (r"eleitor|voto|urna|compareci|absten|votar", "urna"),
        (r"cresceu|crescimento|cresceram|subiu|saltou|dobrou|disparou", "grafico"),
        (r"2028|sucess|cenário|futuro", "calendario"),
        (r"lideran|nomes|candidat|estreante", "pessoas"), (r"destaque|mais votad", "estrela"),
        (r"método|regra|fonte|dados oficiais|confirm", "lupa")]


def icon_for(sentence):
    s = sentence.lower()
    if s.strip().endswith("?"):
        return "interrog"
    for pat, ic in KEYS:
        if re.search(pat, s):
            return ic
    return None


NUM_RE = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+,\d+\s?%|\d+\s?%|\d+,\d+|\b\d{3,}\b)")


def number_in(sentence):
    for m in NUM_RE.finditer(sentence):
        v = m.group(1).replace(" ", "")
        if re.fullmatch(r"(19|20)\d\d", v):  # ano
            continue
        if v in ("2028",):
            continue
        cap = sentence[m.end():].strip(" :,.;")
        cap = " ".join(cap.split()[:7])
        return v, cap
    return None


# ================================================================= construção de formas
def sample(img, n, seed):
    a = np.asarray(img)
    lum = a.max(axis=2)
    ys, xs = np.nonzero(lum > 30)
    rng = np.random.default_rng(seed)
    if len(xs) == 0:
        xs, ys = np.array([W // 2]), np.array([H // 2])
    idx = rng.choice(len(xs), n, replace=len(xs) < n)
    pos = np.stack([xs[idx], ys[idx]], 1).astype(np.float32) + rng.uniform(-.5, .5, (n, 2))
    col = a[ys[idx], xs[idx]].astype(np.float32) / 255
    # brilho normalizado pela densidade (texto pequeno não estoura)
    dens = np.clip((len(xs) / n) / 16, 0.10, 1.0)
    return pos, col * dens


def shape_icon(name, region, seed):
    im = canvas(); d = ImageDraw.Draw(im)
    cx, cy, s = box_center(region)
    ICONS[name][0](d, cx, cy, s * .92, GOLD)
    return sample(im, N_SHAPE, seed)


def shape_number(txt, region, seed):
    im = canvas(); d = ImageDraw.Draw(im)
    cx, cy, s = box_center(region)
    size = 300 if len(txt) <= 5 else (240 if len(txt) <= 7 else 190)
    d.text((cx, cy), txt, font=FS(size), fill=GOLD_L, anchor="mm")
    return sample(im, N_SHAPE, seed)


def shape_frame(scene, dur, seed):
    """Infográfico final da cena (doc_engine) desenhado sobre fundo preto."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    import doc_engine
    old = doc_engine.BG; doc_engine.BG = (0, 0, 0)
    scene.draw(im, d, 60, 60)
    doc_engine.BG = old
    rgb = im.convert("RGB")
    return sample(rgb, N_SHAPE, seed), rgb


def scatter(seed, spread=1.0):
    rng = np.random.default_rng(seed)
    ang = rng.uniform(0, 2 * np.pi, N_SHAPE); r = rng.uniform(200, 1400, N_SHAPE) * spread
    pos = np.stack([W / 2 + r * np.cos(ang), H / 2 + r * np.sin(ang) * .7], 1).astype(np.float32)
    col = np.tile(np.array(GOLD_L, np.float32) / 255, (N_SHAPE, 1))
    return pos, col


# ================================================================= plano de beats por cena
CHAP_ICON = {"Capítulo 1": "urna", "Capítulo 2": "grafico", "Capítulo 3": "estrela", "Capítulo 4": "prefeitura",
             "Capítulo 5": "camara", "Capítulo 6": "pessoas", "Capítulo 7": "calendario"}
CHART = (BigNum, HBars, VBars, Duel, Parliament, MapScene, Lines)
CRISP = (Table, Timeline, Quote)
LEFT = (130, 250, 900, 860)       # área da ilustração quando há painel à direita
FULL = (300, 200, 1620, 880)


def plan_beats(i, scene, falas, starts, dur):
    """Retorna lista de beats: (t_ini, tipo, payload)."""
    beats = []
    if isinstance(scene, (Title, Chapter)):
        beats.append((starts[0] - .4, "frame", None))
        for k, f in enumerate(falas[1:], 1):
            ic = icon_for(f) or CHAP_ICON.get(getattr(scene, "n", ""), "lupa")
            beats.append((starts[k], "icon_full", ic))
        if isinstance(scene, Chapter):
            beats.append((max(1.6, dur * .45), "icon_full", CHAP_ICON.get(scene.n, "lupa")))
    elif isinstance(scene, CHART):
        beats.append((0.2, "frame", None))
        used = 0
        for k, f in enumerate(falas):
            if k == 0: continue
            nb = number_in(f)
            if nb and used < 2 and k < len(falas) - 1:
                beats.append((starts[k], "number", nb)); used += 1
                beats.append((starts[k + 1] - .1, "frame", None))
    elif isinstance(scene, Bullets):
        for k, f in enumerate(falas):
            nb = number_in(f)
            ic = icon_for(f)
            if nb and (k % 2 == 1 or not ic):
                beats.append((starts[k] - (.3 if k == 0 else 0), "number_left", nb))
            else:
                beats.append((starts[k] - (.3 if k == 0 else 0), "icon_left", ic or "lupa"))
    else:  # Table, Timeline, Quote: infográfico nítido; partículas viram ícone ao fundo
        beats.append((0.2, "frame", None))
        ic = icon_for(" ".join(falas)) or "lupa"
        beats.append((max(2.5, starts[min(1, len(starts) - 1)]), "icon_bg", ic))
    beats.sort(key=lambda b: b[0])
    return beats


# ================================================================= render
def glow_layer(pos, col, inten, scale):
    h, w = H // scale, W // scale
    buf = np.zeros((h, w, 3), np.float32)
    x = (pos[:, 0] / scale).astype(np.int32); y = (pos[:, 1] / scale).astype(np.int32)
    ok = (x >= 0) & (x < w) & (y >= 0) & (y < h)
    np.add.at(buf, (y[ok], x[ok]), col[ok] * inten[ok, None])
    return buf


def draw_list(d, items, active, a, x0=1000, y0=260, wmax=820, ymax=815):
    # escolhe o maior tamanho de fonte que cabe acima da área de legenda
    for fs in (34, 31, 28, 25, 22):
        lh = int(fs * 1.3); tagh = int(fs * 1.2); y = y0
        for it in items:
            tag = None
            if isinstance(it, tuple): tag, it = it
            if tag: y += tagh
            y += lh * len(wrap(d, it, F("SemiBold", fs), wmax)) + int(fs * .55)
        if y <= ymax: break
    y = y0
    for k, it in enumerate(items):
        tag = None
        if isinstance(it, tuple): tag, it = it
        on = k <= active
        col = WHITE if k == active else (GREY if on else (60, 64, 74))
        fnt = F("SemiBold" if k == active else "Medium", fs)
        if tag:
            tc = {"FATO": (120, 170, 120), "LEITURA": GOLD, "HIPÓTESE": (190, 120, 110), "NÃO LOCALIZADO": GREY}.get(tag, GREY)
            tf = F("Bold", max(16, int(fs * .58)))
            tw = d.textlength(tag, font=tf) + 18
            d.rounded_rectangle([x0, y + 2, x0 + tw, y + tagh - 6], 6, outline=tc if on else (60, 64, 74), width=2)
            d.text((x0 + 9, y + (tagh - 4) / 2), tag, font=tf, fill=tc if on else (60, 64, 74), anchor="lm")
            y += tagh
        for ln in wrap(d, it, F("SemiBold", fs), wmax):
            d.text((x0, y), ln, font=fnt, fill=col); y += lh
        y += int(fs * .55)


def render(i, scene, falas, subs, starts, dur, out):
    rng = np.random.default_rng(i)
    beats = plan_beats(i, scene, falas, starts, dur)
    frame_cache = {}
    shapes = []
    for k, (t0, kind, pay) in enumerate(beats):
        seed = i * 100 + k
        if kind == "frame":
            if "f" not in frame_cache:
                frame_cache["f"] = shape_frame(scene, dur, seed)
            (p, c), _ = frame_cache["f"]
        elif kind == "icon_full":
            p, c = shape_icon(pay, (560, 250, 1360, 850), seed)
        elif kind == "icon_left":
            p, c = shape_icon(pay, LEFT, seed)
        elif kind == "icon_bg":
            p, c = shape_icon(pay, (1300, 600, 1820, 1000), seed); c = c * .9
        elif kind == "number":
            p, c = shape_number(pay[0], (200, 300, 1720, 760), seed)
        elif kind == "number_left":
            p, c = shape_number(pay[0], LEFT, seed)
        shapes.append((t0, kind, pay, p, c))
    crisp = frame_cache.get("f", (None, None))[1]
    crisp_rgba = None
    if crisp is not None:
        a = np.asarray(crisp).astype(np.float32)
        alpha = (a.max(axis=2) > 25).astype(np.float32)
        crisp_rgba = (a, alpha)

    p_start, c_start = scatter(i + 999)
    phase = rng.uniform(0, 2 * np.pi, N_SHAPE).astype(np.float32)
    swirl = rng.uniform(60, 260, N_SHAPE).astype(np.float32)
    inten = rng.uniform(.55, 1.0, N_SHAPE).astype(np.float32)
    dust = np.stack([rng.uniform(0, W, N_DUST), rng.uniform(0, H, N_DUST)], 1).astype(np.float32)
    dvel = np.stack([rng.uniform(-6, 6, N_DUST), rng.uniform(-24, -6, N_DUST)], 1).astype(np.float32)
    dph = rng.uniform(0, 6.28, N_DUST).astype(np.float32)
    dcol = np.tile(np.array(GOLD_L, np.float32) / 255, (N_DUST, 1))

    bg = np.asarray(background()).astype(np.float32)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
                          stdin=subprocess.PIPE)
    nfr = int(round(dur * FPS))
    MORPH = 1.15
    prev_p, prev_c = p_start, c_start
    cur_idx = -1
    for fi in range(nfr):
        t = fi / FPS
        # beat atual
        k = max([j for j, b in enumerate(shapes) if b[0] <= t] or [0])
        if k != cur_idx:
            if cur_idx >= 0:
                prev_p, prev_c = cur_pos.copy(), cur_col.copy()
            cur_idx = k
        t0, kind, pay, tp, tc = shapes[k]
        e = ease((t - t0) / MORPH) if t >= t0 else 0
        sw = np.sin(e * np.pi)
        ang = phase + t * .9
        cur_pos = prev_p + (tp - prev_p) * e
        cur_pos[:, 0] += swirl * sw * np.cos(ang)
        cur_pos[:, 1] += swirl * sw * np.sin(ang) * .6
        cur_pos += 1.4 * np.stack([np.sin(t * 2 + phase), np.cos(t * 1.7 + phase)], 1)
        cur_col = prev_c + (tc - prev_c) * e
        # dispersão no fim da cena
        out_e = ease((t - (dur - .9)) / .9)
        if out_e > 0:
            dirv = cur_pos - np.array([W / 2, H / 2], np.float32)
            cur_pos_r = cur_pos + dirv * out_e * 1.6
        else:
            cur_pos_r = cur_pos
        dim = 0.35 if kind == "icon_bg" else 1.0
        it = inten * dim * (1 - .6 * out_e)
        dp = dust + dvel * t
        dp[:, 0] = (dp[:, 0] + 18 * np.sin(t * .4 + dph)) % W; dp[:, 1] = dp[:, 1] % H
        di = (.25 + .2 * np.sin(t * 1.3 + dph)).astype(np.float32)

        allp = np.concatenate([cur_pos_r, dp]); allc = np.concatenate([cur_col, dcol]); alli = np.concatenate([it, di])
        core = glow_layer(allp, allc, alli, 1)
        g2 = cv2.GaussianBlur(glow_layer(allp, allc, alli, 2), (0, 0), 3)
        g4 = cv2.GaussianBlur(glow_layer(allp, allc, alli, 4), (0, 0), 4)
        light = core * 1.15 + cv2.resize(g2, (W, H)) * .75 + cv2.resize(g4, (W, H)) * .9
        img = bg + light * 255
        # cristalização do infográfico
        if crisp_rgba is not None and kind in ("frame", "icon_bg"):
            cr = ease((t - t0 - MORPH * .75) / .6) if kind == "frame" else 1.0
            if kind == "icon_bg" or (kind == "frame" and k > 0 and shapes[k - 1][1] == "frame"):
                cr = 1.0
            cr *= (1 - out_e)
            if cr > 0:
                a, al = crisp_rgba
                al3 = (al * cr * .92)[..., None]
                img = img * (1 - al3) + a * al3 + light * 255 * .25 * al3
        img = np.clip(img, 0, 255).astype(np.uint8)
        pil = Image.fromarray(img).convert("RGBA")
        d = ImageDraw.Draw(pil)
        # textos nítidos por tipo de beat
        la = ease((t - t0 - .7) / .6) * (1 - out_e)
        if kind in ("number", "number_left", "icon_full", "icon_left") and la > 0:
            if kind == "number":
                cap, cx, cy = pay[1], W / 2, 820
            elif kind == "number_left":
                cap, cx, cy = pay[1], (LEFT[0] + LEFT[2]) / 2, LEFT[3] + 20
            elif kind == "icon_full":
                cap, cx, cy = ICONS[pay][1], W / 2, 900
            else:
                cap, cx, cy = ICONS[pay][1], (LEFT[0] + LEFT[2]) / 2, LEFT[3] + 20
            c = tuple(int(v * la) for v in (GOLD_L if kind.startswith("icon") else WHITE))
            for kk, ln in enumerate(wrap(d, cap, F("SemiBold", 36), 760)[:2]):
                d.text((cx, cy + kk * 46), ln, font=F("SemiBold", 36), fill=c, anchor="ma")
        if isinstance(scene, Bullets):
            ta = ease(t / .8) * (1 - out_e)
            d.text((1000, 130), scene.kicker.upper(), font=F("SemiBold", 26), fill=tuple(int(v * ta) for v in GOLD))
            for kk, ln in enumerate(wrap(d, scene.title, F("Bold", 46), 840)[:2]):
                d.text((1000, 170 + kk * 54), ln, font=F("Bold", 46), fill=tuple(int(v * ta) for v in WHITE))
            act = int(len(scene.items) * min(.999, max(0, t - .5) / max(1, dur * .8)))
            draw_list(d, scene.items, act, ta, y0=300)
        if kind in ("number", "icon_full") and not isinstance(scene, (Title, Chapter)):
            ta = 1 - out_e
            d.text((80, 120), getattr(scene, "kicker", "").upper(), font=F("SemiBold", 26), fill=tuple(int(v * ta) for v in GOLD))
        chrome(d, getattr(scene, "src", ""), getattr(scene, "chapter", ""))
        cur = next((s for s in subs if s[0] <= t < s[1]), None)
        subtitles(pil, cur[2] if cur else "")
        fr = np.asarray(pil.convert("RGB"))
        fade = min(1, t / .35, (dur - t) / .35)
        if fade < 1:
            fr = (fr * max(0, fade)).astype(np.uint8)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait()


# ================================================================= narração 1,4×
falar = None
exec(compile((HERE / "docu.py").read_text().split("# ------------------------------------------------------------------ fala (TTS)")[1]
             .split("def tts(")[0], "docu_falar", "exec"), G)
falar = G["falar"]; chunks_src = (HERE / "docu.py").read_text()
exec(compile("def chunks" + chunks_src.split("def chunks")[1].split("LEAD, GAP")[0], "docu_chunks", "exec"), G)
chunks = G["chunks"]
LENGTH = 1.04 / 1.4


def tts(text, path):
    if not path.exists():
        subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", str(path), "--length-scale", f"{LENGTH:.3f}"],
                       input=falar(text).encode(), check=True, capture_output=True)
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


LEAD, GAP, TAIL = .7, .22, 1.0
plan = []; audio = []; srt = []; tg = 0.0
for i, (scene, falas, visual) in enumerate(S):
    t = LEAD; subs = []; starts = []; aud = [np.zeros(int(LEAD * SR), np.float32)]
    for j, f in enumerate(falas):
        a = tts(f, WORK / f"s{i:02d}_{j:02d}.wav"); ln = len(a) / SR
        starts.append(t)
        cs = chunks(f, 80); tot = sum(len(c) for c in cs); tt = t
        for c in cs:
            dd = ln * len(c) / tot; subs.append((tt, tt + dd, c)); tt += dd
        aud += [a, np.zeros(int(GAP * SR), np.float32)]; t += ln + GAP
    dur = t + TAIL
    a = np.concatenate(aud); a = np.pad(a, (0, max(0, int(dur * SR) - len(a))))[:int(dur * SR)]
    audio.append(a)
    srt += [(tg + s0, tg + s1, c) for s0, s1, c in subs]
    plan.append((i, dur, subs, starts)); tg += dur
narr = np.concatenate(audio); TOTAL = len(narr) / SR
print(f"duração: {TOTAL/60:.1f} min · {len(S)} cenas", flush=True)

# trilha: mesma síntese do documentário, com pulsação suave e "whoosh" nas trocas
music = G.get("music")
exec(compile("def music" + (HERE / "docu.py").read_text().split("def music")[1].split("bgm = music")[0], "docu_music", "exec"), G)
bgm = G["music"](TOTAL)
tt = np.arange(len(bgm)) / SR
bgm += 0.03 * np.sin(2 * np.pi * 55 * tt) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 1.0 * tt))) * np.exp(-((tt * 1.0) % 1.0) * 6)
rng = np.random.default_rng(7)
t0 = 0
for i, dur, subs, starts in plan:
    n = int(1.1 * SR); x = np.arange(n) / SR
    wh = rng.standard_normal(n) * np.sin(np.pi * x / 1.1) ** 2 * 0.05
    wh = np.convolve(wh, np.ones(30) / 30, mode="same")
    st = max(0, int((t0 + dur - .8) * SR)); bgm[st:st + n] += wh[:len(bgm[st:st + n])]
    t0 += dur
env = np.convolve(np.abs(narr), np.ones(int(.4 * SR)) / int(.4 * SR), mode="same")
mix = narr * .95 + bgm * (1 - .55 * np.clip(env / .02, 0, 1))
mix /= max(1, np.abs(mix).max() / .97)
with wave.open(str(WORK / "trilha.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())


def job(args):
    i, dur, subs, starts = args
    out = WORK / f"p{i:02d}.mp4"
    if not out.exists():
        render(i, S[i][0], S[i][1], subs, starts, dur, out)
    return str(out)


if __name__ == "__main__":
    only = [int(x) for x in ARGV[3:]] if len(ARGV) > 3 else None
    todo = [p for p in plan if only is None or p[0] in only]
    with Pool(4) as pool:
        pool.map(job, todo, chunksize=1)
    if only is None:
        (WORK / "lista.txt").write_text("".join(f"file '{WORK / f'p{i:02d}.mp4'}'\n" for i, *_ in plan))
        VD = BASE / "video"
        final = VD / "varjota_2028_particulas.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(WORK / "lista.txt"), "-i", str(WORK / "trilha.wav"),
                        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-c:a", "aac", "-b:a", "160k",
                        "-shortest", "-movflags", "+faststart", str(final)], check=True)
        def ts(s): return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int((s%1)*1000):03d}"
        (VD / "varjota_2028_particulas.srt").write_text("\n".join(f"{k+1}\n{ts(a)} --> {ts(b)}\n{c}\n" for k, (a, b, c) in enumerate(srt)))
        print("OK", final, f"{TOTAL/60:.1f} min")
