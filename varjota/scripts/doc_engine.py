"""Motor gráfico do documentário 'VARJOTA 2028 — O RAIO-X DO PODER'.

Cada cena é desenhada quadro a quadro com PIL (1920x1080, 30 fps):
fundo escuro com vinheta e grão, partículas douradas, gráficos animados
com dados reais, e legendas sincronizadas com a narração.
"""
import math, random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
BG = (11, 13, 18)
GOLD = (201, 162, 74)
GOLD_L = (231, 203, 135)
WHITE = (242, 239, 232)
GREY = (138, 143, 152)
DIM = (70, 74, 84)
SIT = (214, 208, 194)   # situação (marfim neutro)
OPO = (96, 132, 172)    # oposição (azul aço)
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


@lru_cache(None)
def F(w, s):
    return ImageFont.truetype(FONT.format(w), s)


@lru_cache(None)
def FS(s):
    return ImageFont.truetype(SERIF, s)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def fmt(n, dec=0):
    s = f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


# ------------------------------------------------------------------ fundo
@lru_cache(None)
def background():
    im = Image.new("RGB", (W, H), BG)
    # vinheta radial
    v = Image.new("L", (W // 4, H // 4), 0)
    d = ImageDraw.Draw(v)
    for i in range(60):
        r = 1 - i / 60
        d.ellipse([W / 8 - W / 5 * r * 1.3, H / 8 - H / 5 * r * 1.3, W / 8 + W / 5 * r * 1.3, H / 8 + H / 5 * r * 1.3],
                  fill=int(4 + i * 0.55))
    v = v.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    glow = Image.new("RGB", (W, H), (34, 38, 50))
    im = Image.composite(glow, im, v)
    return im


@lru_cache(None)
def grain(k):
    rnd = random.Random(k)
    g = Image.effect_noise((W // 2, H // 2), 22).resize((W, H))
    return g.point(lambda p: int((p - 128) * 0.10 + 128))


@lru_cache(None)
def sprite(r):
    s = r * 6
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(r * 3, 0, -1):
        a = int(255 * (1 - i / (r * 3)) ** 2.4)
        d.ellipse([s / 2 - i, s / 2 - i, s / 2 + i, s / 2 + i], fill=GOLD_L + (a,))
    d.ellipse([s / 2 - r * .5, s / 2 - r * .5, s / 2 + r * .5, s / 2 + r * .5], fill=(255, 240, 200, 255))
    return im


class Particles:
    def __init__(self, n, seed=1):
        rnd = random.Random(seed)
        self.p = [(rnd.random() * W, rnd.random() * H, rnd.uniform(-8, 8), rnd.uniform(-22, -6),
                   rnd.choice([1, 1, 1, 2, 2, 3]), rnd.uniform(0, 6.28), rnd.uniform(.2, .9)) for _ in range(n)]

    def draw(self, im, t, amount=1.0):
        if amount <= 0:
            return
        for x, y, vx, vy, r, ph, a in self.p:
            px = (x + vx * t + 18 * math.sin(t * .4 + ph)) % (W + 60) - 30
            py = (y + vy * t) % (H + 60) - 30
            al = a * amount * (0.55 + 0.45 * math.sin(t * 1.3 + ph))
            if al < 0.05:
                continue
            sp = sprite(r)
            if al < 0.98:
                sp = sp.copy(); sp.putalpha(sp.getchannel("A").point(lambda q, al=al: int(q * al)))
            im.alpha_composite(sp, (int(px - sp.width / 2), int(py - sp.height / 2)))


# ------------------------------------------------------------------ texto
def wrap(d, text, font, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w_ in para.split():
            t = (line + " " + w_).strip()
            if d.textlength(t, font=font) <= maxw:
                line = t
            else:
                if line: out.append(line)
                line = w_
        out.append(line)
    return out


def text_fade(d, xy, txt, font, color, alpha, anchor="la"):
    c = tuple(int(BG[i] + (color[i] - BG[i]) * alpha) for i in range(3))
    d.text(xy, txt, font=font, fill=c, anchor=anchor)


def subtitles(im, txt):
    if not txt:
        return
    d = ImageDraw.Draw(im)
    f = F("SemiBold", 40)
    lines = wrap(d, txt, f, 1500)[:3]
    lh = 52; h = lh * len(lines) + 28
    y0 = H - 70 - h
    wmax = max(d.textlength(l, font=f) for l in lines)
    ov = Image.new("RGBA", (int(wmax + 60), h), (0, 0, 0, 170))
    im.alpha_composite(ov, (int(W / 2 - wmax / 2 - 30), y0))
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + 14 + i * lh), l, font=f, fill=(255, 255, 255), anchor="ma")


def chrome(d, src, chapter):
    if chapter:
        d.text((80, 56), chapter.upper(), font=F("SemiBold", 22), fill=GOLD)
    d.text((W - 80, 56), "VARJOTA 2028 · O RAIO-X DO PODER", font=F("Medium", 20), fill=DIM, anchor="ra")
    if src:
        d.text((80, H - 44), "Fonte: " + src, font=F("Regular", 22), fill=GREY)


def kick_title(d, kicker, title, a, y=120, size=64, maxw=1700):
    if kicker:
        text_fade(d, (80, y), kicker.upper(), F("SemiBold", 28), GOLD, a)
        y += 52
    for ln in wrap(d, title, F("Bold", size), maxw):
        text_fade(d, (80, y), ln, F("Bold", size), WHITE, a)
        y += int(size * 1.18)
    return y + 20


# ------------------------------------------------------------------ cenas
class Scene:
    particles = 0.35
    chapter = ""
    src = "TSE · dados abertos"

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def draw(self, im, d, t, dur):
        pass


class Title(Scene):
    particles = 1.0
    src = ""

    def draw(self, im, d, t, dur):
        a = ease(t / 1.6)
        y = 380
        text_fade(d, (W / 2, y - 70), self.kicker.upper(), F("SemiBold", 30), GOLD, a, "ma")
        for ln in wrap(d, self.title, FS(104), 1700):
            text_fade(d, (W / 2, y), ln, FS(104), WHITE, ease((t - .3) / 1.6), "ma"); y += 124
        lw = 600 * ease((t - .8) / 1.4)
        d.line([(W / 2 - lw / 2, y + 24), (W / 2 + lw / 2, y + 24)], fill=GOLD, width=2)
        for ln in wrap(d, self.sub, F("Light", 40), 1400):
            text_fade(d, (W / 2, y + 60), ln, F("Light", 40), GREY, ease((t - 1.3) / 1.5), "ma"); y += 52


class Chapter(Scene):
    particles = 1.0
    src = ""

    def draw(self, im, d, t, dur):
        a = ease(t / 1.2)
        text_fade(d, (W / 2, 400), self.n.upper(), F("SemiBold", 32), GOLD, a, "ma")
        lw = 300 * ease((t - .3) / 1.0)
        d.line([(W / 2 - lw / 2, 455), (W / 2 + lw / 2, 455)], fill=GOLD, width=2)
        y = 490
        for ln in wrap(d, self.title, FS(88), 1600):
            text_fade(d, (W / 2, y), ln, FS(88), WHITE, ease((t - .5) / 1.3), "ma"); y += 104
        if getattr(self, "q", ""):
            for ln in wrap(d, self.q, F("Light", 38), 1300):
                text_fade(d, (W / 2, y + 30), ln, F("LightItalic", 38), GREY, ease((t - 1.2) / 1.4), "ma"); y += 50


class BigNum(Scene):
    """Números grandes que contam até o valor."""
    def draw(self, im, d, t, dur):
        y = kick_title(d, self.kicker, self.title, ease(t / 1))
        n = len(self.items); cw = (W - 160) / n
        for i, it in enumerate(self.items):
            p = ease((t - .6 - i * .5) / 1.6)
            x = 80 + i * cw
            v = it["v"] * p
            s = it.get("pre", "") + fmt(v, it.get("dec", 0)) + it.get("suf", "")
            text_fade(d, (x, y + 90), s, FS(it.get("size", 120)), it.get("color", GOLD_L), min(1, p * 2))
            for k, ln in enumerate(wrap(d, it["label"], F("Medium", 34), cw - 60)):
                text_fade(d, (x, y + 250 + k * 44), ln, F("Medium", 34), WHITE, min(1, p * 2))
            if it.get("note"):
                for k, ln in enumerate(wrap(d, it["note"], F("Regular", 28), cw - 60)):
                    text_fade(d, (x, y + 350 + k * 38), ln, F("Regular", 28), GREY, min(1, p * 2))


class HBars(Scene):
    """Barras horizontais animadas."""
    def draw(self, im, d, t, dur):
        y0 = kick_title(d, self.kicker, self.title, ease(t / 1), size=56)
        items = self.items; n = len(items)
        avail = H - 170 - y0
        bh = min(64, avail / n * .72); gap = avail / n
        vmax = getattr(self, "vmax", max(it["v"] for it in items))
        lx = getattr(self, "label_w", 520)
        bw = W - 80 - lx - 260
        for i, it in enumerate(items):
            p = ease((t - .5 - i * getattr(self, "stagger", .12)) / 1.2)
            y = y0 + i * gap
            col = it.get("color", GOLD)
            text_fade(d, (80 + lx - 24, y + bh / 2), it["label"], F("SemiBold", min(32, int(bh * .62))), WHITE, min(1, p * 1.5), "rm")
            w_ = bw * it["v"] / vmax * p
            if w_ > 1:
                d.rectangle([80 + lx, y, 80 + lx + w_, y + bh], fill=col)
            lab = it.get("vl", fmt(it["v"] * p, it.get("dec", 0)) + it.get("suf", ""))
            text_fade(d, (80 + lx + w_ + 18, y + bh / 2), lab, F("Bold", min(32, int(bh * .62))), col if col != DIM else GREY, min(1, p * 1.5), "lm")
            if it.get("tag"):
                text_fade(d, (80 + lx + w_ + 18 + d.textlength(lab, font=F("Bold", min(32, int(bh * .62)))) + 16, y + bh / 2),
                          it["tag"], F("Regular", min(26, int(bh * .5))), GREY, min(1, p * 1.5), "lm")
        if getattr(self, "line", None):
            lv, lt = self.line
            x = 80 + lx + bw * lv / vmax
            a = ease((t - 1.5) / 1)
            for yy in range(int(y0 - 10), int(y0 + n * gap), 14):
                d.line([(x, yy), (x, yy + 7)], fill=lerp(BG, GOLD_L, a), width=2)
            text_fade(d, (x, y0 + n * gap + 4), lt, F("SemiBold", 24), GOLD_L, a, "ma")


class VBars(Scene):
    def draw(self, im, d, t, dur):
        y0 = kick_title(d, self.kicker, self.title, ease(t / 1), size=56)
        base = H - 290; top = y0 + 90
        items = self.items; n = len(items)
        vmax = getattr(self, "vmax", max(it["v"] for it in items)) * 1.08
        cw = (W - 160) / n; bw = min(220, cw * .55)
        for qv, ql in getattr(self, "hlines", []):
            yq = base - (base - top) * qv / vmax
            a = ease((t - 1.2) / 1)
            for xx in range(80, W - 80, 18):
                d.line([(xx, yq), (xx + 9, yq)], fill=lerp(BG, DIM, a), width=2)
            text_fade(d, (W - 80, yq - 8), ql, F("Regular", 22), GREY, a, "rb")
        for i, it in enumerate(items):
            p = ease((t - .5 - i * .25) / 1.4)
            cx = 80 + cw * (i + .5)
            h_ = (base - top) * it["v"] / vmax * p
            d.rectangle([cx - bw / 2, base - h_, cx + bw / 2, base], fill=it.get("color", GOLD))
            text_fade(d, (cx, base - h_ - 16), it.get("vl", fmt(it["v"] * p, it.get("dec", 0)) + it.get("suf", "")),
                      F("Bold", 40), WHITE, min(1, p * 1.5), "mb")
            if it.get("sub"):
                text_fade(d, (cx, base - h_ - 66), it["sub"], F("Medium", 26), GOLD_L, min(1, p * 1.5), "mb")
            text_fade(d, (cx, base + 20), it["label"], F("SemiBold", 30), WHITE, min(1, p * 2), "ma")
            if it.get("label2"):
                text_fade(d, (cx, base + 58), it["label2"], F("Regular", 24), GREY, min(1, p * 2), "ma")


class Duel(Scene):
    """Duas barras empilhadas (2020 × 2024) com nomes."""
    def draw(self, im, d, t, dur):
        y0 = kick_title(d, self.kicker, self.title, ease(t / 1), size=56) + 30
        for i, row in enumerate(self.rows):
            p = ease((t - .6 - i * 1.4) / 1.6)
            y = y0 + i * 260
            text_fade(d, (80, y), row["ano"], FS(64), GOLD_L, min(1, p * 2))
            x0, x1 = 300, W - 80; bw = x1 - x0
            a, b = row["a"], row["b"]
            wa = bw * a["pct"] / 100 * p
            d.rectangle([x0, y, x0 + wa, y + 110], fill=SIT)
            wb = bw * b["pct"] / 100 * p
            d.rectangle([x1 - wb, y, x1, y + 110], fill=OPO)
            text_fade(d, (x0 + 24, y + 20), f"{a['nome']}  ·  {a['partido']}", F("Bold", 34), BG, min(1, p * 1.4))
            text_fade(d, (x0 + 24, y + 64), f"{fmt(a['votos'] * p)} votos · {fmt(a['pct'] * p, 1)}%", F("Medium", 30), BG, min(1, p * 1.4))
            text_fade(d, (x1 - 24, y + 20), f"{b['partido']}  ·  {b['nome']}", F("Bold", 34), WHITE, min(1, p * 1.4), "ra")
            text_fade(d, (x1 - 24, y + 64), f"{fmt(b['votos'] * p)} votos · {fmt(b['pct'] * p, 1)}%", F("Medium", 30), WHITE, min(1, p * 1.4), "ra")
            text_fade(d, (x0, y + 130), row.get("nota", ""), F("Regular", 28), GREY, ease((t - 1.8 - i * 1.4) / 1))
        xm = 300 + (W - 380) / 2
        for yy in range(int(y0 - 20), int(y0 + 500), 16):
            d.line([(xm, yy), (xm, yy + 8)], fill=GOLD, width=2)
        text_fade(d, (xm, y0 - 50), "50%", F("SemiBold", 24), GOLD, 1, "ma")


class Parliament(Scene):
    def draw(self, im, d, t, dur):
        y0 = kick_title(d, self.kicker, self.title, ease(t / 1), size=56)
        for k, (ano, seats) in enumerate(self.panels):
            cx = (W / 4 + k * W / 2) if len(self.panels) > 1 else W / 2; cy = y0 + 470; R = 330
            n = len(seats)
            for i, (lab, col) in enumerate(seats):
                ang = math.pi - math.pi * i / (n - 1)
                p = ease((t - .5 - k * 1.2 - i * .1) / .6)
                if p <= 0: continue
                r = 46 * p
                x, y = cx + R * math.cos(ang), cy - R * math.sin(ang)
                d.ellipse([x - r, y - r, x + r, y + r], fill=col)
                if p > .9:
                    d.text((x, y), lab, font=F("Bold", 18), fill=BG if col == SIT else WHITE, anchor="mm")
            g = sum(1 for s in seats if s[1] == SIT); o = n - g
            a = ease((t - 1.6 - k * 1.2) / 1)
            text_fade(d, (cx, cy - 120), f"{g} × {o}", FS(110), WHITE, a, "mm")
            text_fade(d, (cx, cy - 30), "situação × oposição", F("Regular", 28), GREY, a, "mm")
            text_fade(d, (cx, cy + 60), ano, FS(54), GOLD_L, a, "mm")


class Bullets(Scene):
    def draw(self, im, d, t, dur):
        y = kick_title(d, self.kicker, self.title, ease(t / 1), size=60) + 10
        n = len(self.items)
        span = max(1.0, dur * .7 - 1)
        for i, it in enumerate(self.items):
            tag = None
            if isinstance(it, tuple): tag, it = it
            p = ease((t - .8 - i * span / n) / .8)
            f = F("Medium", 40)
            lines = wrap(d, it, f, 1560 if not tag else 1380)
            if p > 0:
                d.rectangle([84, y + 14, 84 + 10 * p, y + 24], fill=GOLD)
                x = 120
                if tag:
                    col = {"FATO": (120, 170, 120), "LEITURA": GOLD, "HIPÓTESE": (190, 120, 110), "NÃO LOCALIZADO": GREY}.get(tag, GREY)
                    tw = d.textlength(tag, font=F("Bold", 22)) + 24
                    d.rounded_rectangle([x, y + 4, x + tw, y + 38], 6, outline=lerp(BG, col, p), width=2)
                    text_fade(d, (x + 12, y + 21), tag, F("Bold", 22), col, p, "lm")
                    x += tw + 18
                for k, ln in enumerate(lines):
                    text_fade(d, (x + 20 * (1 - p), y + k * 52), ln, f, WHITE, p)
            y += 52 * len(lines) + 30


class Table(Scene):
    def draw(self, im, d, t, dur):
        y = kick_title(d, self.kicker, self.title, ease(t / 1), size=54) + 10
        widths = getattr(self, "widths", [1 / len(self.header)] * len(self.header))
        xs = [80 + sum(widths[:i]) * (W - 160) for i in range(len(widths))]
        fs = getattr(self, "fs", 32); rh = int(fs * 1.9)
        a = ease((t - .3) / .8)
        d.line([(80, y + rh), (W - 80, y + rh)], fill=lerp(BG, GOLD, a), width=2)
        for i, h_ in enumerate(self.header):
            text_fade(d, (xs[i] + 10, y + rh / 2), h_, F("SemiBold", fs - 4), GOLD, a, "lm")
        y += rh + 6
        n = len(self.rows); span = max(1.0, dur * .55)
        for r_i, row in enumerate(self.rows):
            p = ease((t - .8 - r_i * span / n) / .6)
            hl = row and isinstance(row[-1], bool)
            cells = row[:-1] if hl else row
            if hl and p > 0:
                ov = Image.new("RGBA", (W - 160, rh), GOLD + (int(38 * p),)); im.alpha_composite(ov, (80, int(y)))
            for i, c in enumerate(cells):
                text_fade(d, (xs[i] + 10, y + rh / 2), str(c), F("Bold" if i == 0 else "Medium", fs), WHITE, p, "lm")
            d.line([(80, y + rh), (W - 80, y + rh)], fill=lerp(BG, (40, 44, 54), p), width=1)
            y += rh
        if getattr(self, "note", ""):
            for k, ln in enumerate(wrap(d, self.note, F("Regular", 28), W - 160)):
                text_fade(d, (80, y + 30 + k * 38), ln, F("Regular", 28), GREY, ease((t - 2) / 1))


class MapScene(Scene):
    """Pontos dos locais de votação em coordenadas reais (lat/long do TSE)."""
    particles = .5

    def draw(self, im, d, t, dur):
        kick_title(d, self.kicker, self.title, ease(t / 1), size=52, maxw=760)
        pts = self.points
        la = [p["lat"] for p in pts]; lo = [p["lon"] for p in pts]
        x0, x1, y0, y1 = 900, W - 120, 150, H - 170
        mnlo, mxlo, mnla, mxla = min(lo) - .01, max(lo) + .01, min(la) - .01, max(la) + .01
        sc = min((x1 - x0) / (mxlo - mnlo), (y1 - y0) / (mxla - mnla))
        def xy(p):
            return (x0 + (p["lon"] - mnlo) * sc, y1 - (p["lat"] - mnla) * sc)
        # grade sutil
        ga = ease(t / 1.5)
        for k in range(9):
            xx = x0 + k * (x1 - x0) / 8; d.line([(xx, y0), (xx, y1)], fill=lerp(BG, (28, 32, 42), ga))
            yy = y0 + k * (y1 - y0) / 8; d.line([(x0, yy), (x1, yy)], fill=lerp(BG, (28, 32, 42), ga))
        order = sorted(range(len(pts)), key=lambda i: -pts[i]["size"])
        for j, i in enumerate(order):
            p = pts[i]; a = ease((t - .6 - j * .05) / .7)
            if a <= 0: continue
            x, y = xy(p); r = (8 + math.sqrt(p["size"]) * 1.1) * a
            col = p["color"]
            glow = Image.new("RGBA", (int(r * 4), int(r * 4)), (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse([r, r, r * 3, r * 3], fill=col + (90,))
            glow = glow.filter(ImageFilter.GaussianBlur(r * .5))
            im.alpha_composite(glow, (int(x - r * 2), int(y - r * 2)))
            d.ellipse([x - r * .6, y - r * .6, x + r * .6, y + r * .6], fill=col)
        for p in pts:
            if p.get("label"):
                a = ease((t - 2) / 1)
                x, y = xy(p)
                text_fade(d, (x + 18, y - 4), p["label"], F("SemiBold", 22), WHITE, a, "lm")
                if p.get("val"):
                    text_fade(d, (x + 18, y + 22), p["val"], F("Regular", 20), GOLD_L, a, "lm")
        yl = 470
        for k, ln in enumerate(getattr(self, "legend", [])):
            text_fade(d, (80, yl + k * 50), ln, F("Medium", 32), WHITE if k == 0 else GREY, ease((t - 1.5 - k * .3) / 1))


class Lines(Scene):
    """Série temporal animada (várias linhas)."""
    def draw(self, im, d, t, dur):
        y0 = kick_title(d, self.kicker, self.title, ease(t / 1), size=54)
        x0, x1, yb, yt = 200, W - 300, H - 290, y0 + 60
        xs = self.x; n = len(xs)
        vmax = self.vmax
        a = ease(t / 1)
        for k in range(5):
            v = vmax * k / 4; yy = yb - (yb - yt) * k / 4
            d.line([(x0, yy), (x1, yy)], fill=lerp(BG, (32, 36, 46), a))
            text_fade(d, (x0 - 20, yy), self.yfmt(v), F("Regular", 24), GREY, a, "rm")
        for i, xv in enumerate(xs):
            text_fade(d, (x0 + (x1 - x0) * i / (n - 1), yb + 26), str(xv), F("SemiBold", 28), WHITE, a, "ma")
        p = ease((t - .6) / 2.6) * (n - 1)
        for s in self.series:
            pts = [(x0 + (x1 - x0) * i / (n - 1), yb - (yb - yt) * v / vmax) for i, v in enumerate(s["v"])]
            k = int(p); fr = p - k
            draw_pts = pts[:k + 1]
            if k + 1 < n:
                draw_pts.append((pts[k][0] + (pts[k + 1][0] - pts[k][0]) * fr, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * fr))
            if len(draw_pts) > 1:
                d.line(draw_pts, fill=s["color"], width=5, joint="curve")
            for (px, py) in draw_pts[:k + 1]:
                d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=s["color"])
            lx, ly = draw_pts[-1]
            text_fade(d, (lx + 18, ly), s["name"], F("SemiBold", 26), s["color"], min(1, p), "lm")
            for i in getattr(self, "labels_at", []):
                if p >= i:
                    text_fade(d, (pts[i][0], pts[i][1] - 22), self.vfmt(s["v"][i]), F("Bold", 24), WHITE, min(1, p - i + .2), "mb")


class Timeline(Scene):
    def draw(self, im, d, t, dur):
        y0 = kick_title(d, self.kicker, self.title, ease(t / 1), size=54) + 20
        n = len(self.events); span = max(1.0, dur * .7)
        x = 120
        d.line([(x, y0), (x, y0 + (H - 260 - y0) * ease(t / 2))], fill=GOLD, width=2)
        gap = (H - 260 - y0) / n
        for i, (data, txt, tag) in enumerate(self.events):
            p = ease((t - .6 - i * span / n) / .7)
            y = y0 + i * gap
            if p > 0:
                d.ellipse([x - 9 * p, y + 10 - 9 * p, x + 9 * p, y + 10 + 9 * p], fill=GOLD)
            text_fade(d, (x + 40, y), data, F("Bold", 30), GOLD_L, p)
            text_fade(d, (x + 280, y), txt, F("Medium", 30), WHITE, p)
            if tag:
                text_fade(d, (x + 280, y + 40), tag, F("Regular", 22), GREY, p)


class Quote(Scene):
    def draw(self, im, d, t, dur):
        a = ease(t / 1)
        text_fade(d, (80, 140), self.kicker.upper(), F("SemiBold", 28), GOLD, a)
        y = 230
        text_fade(d, (80, y - 40), "“", FS(200), GOLD, a)
        for ln in wrap(d, self.text, FS(58), 1600):
            text_fade(d, (200, y + 40), ln, FS(58), WHITE, ease((t - .4) / 1.2)); y += 76
        text_fade(d, (200, y + 80), self.who, F("SemiBold", 32), GOLD_L, ease((t - 1.2) / 1))
        for k, ln in enumerate(wrap(d, getattr(self, "note", ""), F("Regular", 28), 1500)):
            text_fade(d, (200, y + 140 + k * 38), ln, F("Regular", 28), GREY, ease((t - 1.6) / 1))


# ------------------------------------------------------------------ render
def render_scene(scene, dur, subs, out_path, seed=0):
    """subs: lista de (t_ini, t_fim, texto). Grava mp4 sem áudio."""
    import subprocess
    nframes = int(round(dur * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                           str(out_path)], stdin=subprocess.PIPE)
    parts = Particles(int(110 * max(scene.particles, .3)), seed)
    bg = background()
    for fi in range(nframes):
        t = fi / FPS
        zoom = 1 + 0.035 * (t / max(dur, 1))
        base = bg if zoom < 1.001 else bg.resize((int(W * zoom), int(H * zoom))).crop(
            (int((W * zoom - W) / 2), int((H * zoom - H) / 2), int((W * zoom - W) / 2) + W, int((H * zoom - H) / 2) + H))
        im = base.convert("RGBA")
        parts.draw(im, t + seed * 3.1, scene.particles)
        d = ImageDraw.Draw(im)
        scene.draw(im, d, t, dur)
        chrome(d, scene.src, scene.chapter)
        cur = next((s for s in subs if s[0] <= t < s[1]), None)
        subtitles(im, cur[2] if cur else "")
        # fade de entrada/saída
        fade = min(1, t / .5, (dur - t) / .5)
        rgb = im.convert("RGB")
        if fade < 1:
            rgb = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), rgb, max(0, fade))
        rgb = Image.blend(rgb, grain(fi % 6).convert("RGB"), 0.035)
        ff.stdin.write(rgb.tobytes())
    ff.stdin.close(); ff.wait()
