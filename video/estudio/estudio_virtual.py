# Vídeo do carro → estúdio virtual de telejornal (modelo M6 Telejornal + M9 câmera única multiângulo)
import sys, json, math, os, numpy as np
sys.path.insert(0, '/home/claude/re')
from lib2 import *
from fx import _affine, trans_out, trans_in, bloom, light_sweep
from PIL import Image, ImageDraw, ImageFilter, ImageChops
exec(open('/home/claude/kroma/scripts/audio.py').read().split('out = np.zeros')[0])
from scipy.ndimage import median_filter, uniform_filter1d, gaussian_filter

WD = '/home/claude/re/work/carro'; SRC_FPS = 25
AC = (212, 255, 58); NAVY = (6, 10, 20)
WJ_ = json.load(open('/home/claude/re/work/carro/words.json'))
PAL = [(s, e, w.strip()) for seg in WJ_ for (s, e, w) in seg]

# ---------- 1. corte das pausas: trechos de fala (gap > 0,35 s vira 0,12 s)
spans = []; a = PAL[0][0] - 0.12; prev = PAL[0][1]
for s, e, w in PAL[1:]:
    if s - prev > 0.35: spans.append((a, prev + 0.14)); a = s - 0.12
    prev = e
spans.append((a, min(prev + 0.5, 50.4)))
spans = [(max(0, x), y) for x, y in spans]
SEGS = []; t = 0
for x, y in spans: SEGS.append(dict(a=x, b=y, t0=t, t1=t + (y - x))); t += y - x
TV = t; TAIL = 2.6; TOT = TV + TAIL
def src_t(tv):
    for g in SEGS:
        if tv < g['t1']: return g['a'] + (tv - g['t0'])
    return SEGS[-1]['b'] - 0.04
def vid_t(ts):
    for g in SEGS:
        if g['a'] <= ts <= g['b']: return g['t0'] + ts - g['a']
    return None
WV = [(vid_t(s), vid_t(e), w) for s, e, w in PAL if vid_t(s) is not None and vid_t(e) is not None]
print('duração', round(TV, 2), 'trechos', len(SEGS))

# ---------- 2. estúdio (mundo 2400×2800)
WW, WH = 2400, 2800
def studio():
    yy = np.linspace(0, 1, WH)[:, None, None]
    g = np.array([8, 14, 30], np.float32) * (1 - yy) + np.array([16, 28, 52], np.float32) * yy
    im = Image.fromarray(np.repeat(g, WW, 1).clip(0, 255).astype(np.uint8)).convert('RGBA')
    # parede de LED inteira: gradiente azul com faixas de luz e bokeh
    LY0, LY1 = 300, 1720; h_ = LY1 - LY0
    gx = np.linspace(-1, 1, WW)[None, :]; gy = np.linspace(0, 1, h_)[:, None]
    lum = np.exp(-(gx ** 2) * 0.9) * (0.65 + 0.35 * np.exp(-((gy - 0.45) ** 2) * 6))
    led = np.dstack([14 + 40 * lum, 46 + 120 * lum, 110 + 140 * lum])
    band = np.exp(-((gy - 0.30) ** 2) * 900) + 0.6 * np.exp(-((gy - 0.72) ** 2) * 1400)
    led += (band * 70)[..., None] * np.array([0.5, 0.9, 1.0]) * np.ones((1, WW, 1))
    led[::6, :, :] *= 0.93; led[:, ::6, :] *= 0.93
    im.paste(Image.fromarray(led.clip(0, 255).astype(np.uint8)), (0, LY0))
    bok = Image.new('RGBA', (WW, WH), (0, 0, 0, 0)); db = ImageDraw.Draw(bok); rng = np.random.default_rng(5)
    for k in range(70):
        x, y, r = rng.uniform(0, WW), rng.uniform(LY0, LY1), rng.uniform(14, 60); c = (212, 255, 58) if rng.random() < 0.25 else (170, 215, 255)
        db.ellipse([x - r, y - r, x + r, y + r], fill=c + (int(rng.uniform(25, 70)),))
    im.alpha_composite(bok.filter(ImageFilter.GaussianBlur(6))); d = ImageDraw.Draw(im, 'RGBA')
    t = text_img('PLENÁRIA CE', font('Anton', 120), (255, 255, 255, 235)); im.alpha_composite(t, (1200 - t.width // 2, LY0 + 360))
    t = text_img('INTELIGÊNCIA ELEITORAL DO CEARÁ', font('Inter800', 34), (212, 255, 58, 235)); im.alpha_composite(t, (1200 - t.width // 2, LY0 + 515))
    d.rectangle([0, LY0 - 14, WW, LY0], fill=(50, 70, 110, 255)); d.rectangle([0, LY1, WW, LY1 + 14], fill=(50, 70, 110, 255))
    for i in range(10): x = 160 + i * 232; d.ellipse([x - 30, 150, x + 30, 190], fill=(255, 246, 228, 255))
    d.rectangle([0, LY1 + 14, WW, WH], fill=(12, 18, 32, 255))
    return im.convert('RGB')
def monitor_layer():
    m = Image.new('RGBA', (WW, WH), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    X0, Y0, X1, Y1 = 1420, 640, 1880, 1300
    d.rounded_rectangle([X0 - 14, Y0 - 14, X1 + 14, Y1 + 14], 26, fill=(30, 40, 60, 255))
    pan = np.zeros((Y1 - Y0, X1 - X0, 3), np.float32); gy = np.linspace(0, 1, Y1 - Y0)[:, None]
    pan[..., 0] = 10 + 10 * gy; pan[..., 1] = 22 + 20 * gy; pan[..., 2] = 44 + 30 * gy
    m.paste(Image.fromarray(pan.astype(np.uint8)).convert('RGBA'), (X0, Y0)); d = ImageDraw.Draw(m)
    G = json.load(open('/home/user/Plen-ria-CE/video/geo-ce.json')); pts = [p for r in G['mun'] for p in r]
    lons = [p[0] for p in pts]; lats = [p[1] for p in pts]; cx, cy, s = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2, 125
    for r in G['mun']: d.polygon([(X0 + 230 + (lo - cx) * s * 0.78, Y0 + 230 - (la - cy) * s * 0.78) for lo, la in r], fill=(212, 255, 58, 255), outline=(10, 22, 44, 255))
    d.text((X0 + 30, Y0 + 470), 'ESTÚDIO VIRTUAL', font=font('Anton', 60), fill=(255, 255, 255))
    d.text((X0 + 32, Y0 + 565), 'edição com IA · teste', font=font('Inter800', 30), fill=(212, 255, 58))
    return m
def desk_layer():
    m = Image.new('RGBA', (WW, WH), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    top, bot = 1395, 1980
    d.polygon([(220, top), (2180, top), (2280, top + 70), (120, top + 70)], fill=(36, 46, 66, 255))
    d.line([(220, top), (2180, top)], fill=(170, 190, 220, 255), width=4)
    gy = np.linspace(0, 1, bot - top - 70)[:, None]; body = np.dstack([18 + 8 * gy, 24 + 10 * gy, 38 + 14 * gy, np.full_like(gy, 255)]) * np.ones((1, 2160, 1))
    m.alpha_composite(Image.fromarray(body.astype(np.uint8), 'RGBA'), (120, top + 70)); d = ImageDraw.Draw(m)
    d.rectangle([120, top + 70, 2280, top + 80], fill=(212, 255, 58, 255))
    return m
BG = studio(); DESK = desk_layer(); MON = monitor_layer()
BGM = BG.copy().convert('RGBA'); BGM.alpha_composite(MON)

# ---------- 3. câmeras virtuais (centro x,y no mundo, largura vista, desfoque do fundo)
HEAD_W = (1200, 1060)       # onde fica o centro da cabeça no mundo
PS = 0.78                   # escala da pessoa no mundo (fonte 576×1024)
CAM = {
  'aberto':  dict(cx=1200, cy=1104, vw=820, blur=0.8, mon=False),
  'medio':   dict(cx=1200, cy=1093, vw=620, blur=2.5, mon=False),
  'lateral': dict(cx=1430, cy=1111, vw=950, blur=1.2, mon=True),
  'medio2':  dict(cx=1140, cy=1098, vw=700, blur=2.0, mon=False),
}
# plano por frase (tempo do vídeo já sem pausas)
FR = [s for s in [(SEGS[i]['t0']) for i in range(len(SEGS))]]
ORDEM = ['aberto', 'medio', 'lateral', 'medio2', 'aberto', 'medio', 'lateral', 'medio2', 'aberto', 'medio', 'lateral', 'aberto']
def frases():
    out = []
    for seg in WJ_:
        s0 = vid_t(seg[0][0]); e0 = vid_t(seg[-1][1])
        if s0 is None: continue
        if out and s0 - out[-1][0] < 3.0: continue
        out.append([s0, e0])
    res = []
    for i, (s0, e0) in enumerate(out):
        fim = out[i + 1][0] if i + 1 < len(out) else TV
        res.append([s0, fim])
        if fim - s0 > 7.5: res.append([s0 + (fim - s0) / 2, fim])
    return sorted(res)
FRASES = frases(); CORTES = [f[0] for f in FRASES[1:]]
def plano(t):
    k = sum(1 for c in CORTES if t >= c); return ORDEM[k % len(ORDEM)], k
print('cortes', [round(c, 1) for c in CORTES])
_bgcache = {}
def bg_shot(name):
    if name in _bgcache: return _bgcache[name]
    c = CAM[name]; vh = c['vw'] * 1920 / 1080; box = (int(c['cx'] - c['vw'] / 2), int(c['cy'] - vh * 0.45), int(c['cx'] + c['vw'] / 2), int(c['cy'] + vh * 0.55))
    src = BGM if c['mon'] else BG.convert('RGBA')
    b = src.crop(box).resize((W, H), Image.LANCZOS).convert('RGB')
    if c['blur']: b = b.filter(ImageFilter.GaussianBlur(c['blur']))
    b = bloom(b, 200, 0.6, 16)
    dk = DESK.crop(box).resize((W, H), Image.LANCZOS)
    _bgcache[name] = (b, dk, box); return _bgcache[name]

# ---------- 4. pessoa: máscara refinada + ombros sintéticos + estabilização
CAB = np.array(json.load(open(f'{WD}/cabeca.json'))); CAB[:, 1] = median_filter(CAB[:, 1], 9); CAB[:, 0] = median_filter(CAB[:, 0], 5)
SUAVE = np.stack([uniform_filter1d(CAB[:, 0], 41), uniform_filter1d(CAB[:, 1], 41)], 1)
SHIRT = (60, 74, 98)
def mask_at(i):
    ms = [np.asarray(Image.open(f'{WD}/m/{j + 1:05d}.png').split()[0], np.float32) / 255 for j in (max(0, i - 1), i, min(len(CAB) - 1, i + 1))]
    m = (ms[0] + 2 * ms[1] + ms[2]) / 4; m = gaussian_filter(m, 2.6)
    return np.clip((m - 0.5) / 0.2, 0, 1) ** 1.2
def pessoa(i):
    f = np.asarray(Image.open(f'{WD}/f/{i + 1:05d}.jpg').convert('RGB'), np.float32)
    m = mask_at(i)
    # ombros: forma escura atrás, para o corpo não terminar na borda do quadro
    L = Image.new('RGBA', (1100, 1024), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.ellipse([60, 520, 1040, 1500], fill=SHIRT + (255,))
    L = L.filter(ImageFilter.GaussianBlur(3))
    # luz/cor da pessoa: leve contraste e sombras frias
    f = (f - 128) * 1.06 + 126; f[..., 2] += 4; f = f.clip(0, 255)
    rgba = np.dstack([f, m * 255]).astype(np.uint8)
    L.alpha_composite(Image.fromarray(rgba, 'RGBA'), (262, 0))
    # luz de recorte (rim) fria na borda
    e = gaussian_filter(m, 6) - gaussian_filter(m, 1.5); e = np.clip(-e * 3, 0, 1)
    rim = np.zeros((1024, 576, 4), np.uint8); rim[..., 0] = 150; rim[..., 1] = 200; rim[..., 2] = 255; rim[..., 3] = (e * m * 110).astype(np.uint8)
    L.alpha_composite(Image.fromarray(rim, 'RGBA'), (262, 0))
    dx, dy = (SUAVE[i] - CAB[i]) * 0.85
    return L, 262 + CAB[i][0] + dx, CAB[i][1] + 110 + dy   # ponto de ancoragem ≈ centro da cabeça
def compor(t):
    name, k = plano(t); b, dk, box = bg_shot(name)
    i = min(len(CAB) - 1, int(round(src_t(min(t, TV - 0.04)) * SRC_FPS)))
    L, ax, ay = pessoa(i)
    sc = W / (box[2] - box[0])                                        # mundo → tela
    s = PS * sc; Lr = L.resize((int(L.width * s), int(L.height * s)), Image.LANCZOS)
    hx = (HEAD_W[0] - box[0]) * sc; hy = (HEAD_W[1] - box[1]) * sc
    c = b.convert('RGBA'); c.alpha_composite(Lr, (int(hx - ax * s), int(hy - ay * s))); c.alpha_composite(dk)
    # deriva lenta de câmera (operador)
    u = t - (([0] + CORTES)[k]); c = _affine(c.convert('RGB'), scale=1.0 + 0.012 * u, dx=math.sin(t * 0.35) * 6, dy=math.cos(t * 0.27) * 4)
    return c, name

# ---------- 5. legenda (uma linha), tarja, bug
FC = font('Inter800', 50)
def blocos():
    out = []; cur = []
    for s, e, w in WV:
        txt = ' '.join(x[2] for x in cur + [(s, e, w)]).upper()
        if cur and (FC.getlength(txt) > 900 or s - cur[-1][1] > 0.5): out.append(cur); cur = []
        cur.append((s, e, w))
    out.append(cur); return out
BL = blocos()
CHAVE = {'PROFISSIONAL', 'ESTÚDIO', 'AUTORIDADE', 'CLOUD', 'TESTE', 'JORNAL', 'ARTIFICIAL', 'SOCIAL', 'EDIÇÃO'}
def legenda(c, t):
    for b in BL:
        if b[0][0] - 0.05 <= t <= b[-1][1] + 0.25:
            ws = [w.upper().replace('CLOUD', 'CLAUDE') for _, _, w in b]
            tot = FC.getlength(' '.join(ws)); x = 540 - tot / 2; y = 1560
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            d.rounded_rectangle([x - 26, y - 14, x + tot + 26, y + 72], 14, fill=(0, 0, 0, 185))
            for (s, e, _), w in zip(b, ws):
                ativo = s <= t; cor = AC if (ativo and w.strip('.,') in CHAVE) else ((255, 255, 255) if ativo else (150, 150, 150))
                d.text((x, y), w, font=FC, fill=cor); x += FC.getlength(w + ' ')
            c.alpha_composite(lay); return
def tarja(c, t):
    a0, a1 = 0.6, 6.0
    if not a0 <= t <= a1 + 0.4: return
    p = e_out((t - a0) / 0.45); q = 1 - e_out((t - a1) / 0.4) if t > a1 else 1
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); y = 1330; xw = int(60 + (1 - p) * -900)
    d.rectangle([xw, y, xw + 230, y + 50], fill=AC + (255,)); d.text((xw + 18, y + 6), 'BASTIDORES', font=font('Inter800', 30), fill=(10, 10, 10))
    d.rectangle([xw, y + 50, xw + 760, y + 150], fill=(255, 255, 255, 245)); d.text((xw + 22, y + 62), 'THIAGO COSTA', font=font('Anton', 62), fill=(12, 14, 22))
    d.text((xw + 430, y + 82), '@falathiagoo', font=font('Inter800', 34), fill=(70, 80, 100))
    if q < 1: lay.putalpha(lay.getchannel('A').point(lambda v: int(v * q)))
    c.alpha_composite(lay)
BUG = text_img('● PLENÁRIA CE · ESTÚDIO', font('Inter800', 30), (255, 255, 255))
def bug(c, t):
    paste(c, BUG, 70 + BUG.width / 2, 120, alpha=0.75 + 0.25 * (math.sin(t * 3) > 0))

# ---------- 6. áudio: fala limpa + trilha de jornal sintetizada + whoosh nos cortes
import subprocess, soundfile as sf
os.makedirs(WD, exist_ok=True)
sp = f'{WD}/fala.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', '/home/claude/pool/carro.mov', '-vn', '-ac', '2', '-ar', str(SR), '-af', 'highpass=f=110,highpass=f=110,afftdn=nr=10:nf=-45:tn=1,equalizer=f=310:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.4:g=2.5,deesser,acompressor=threshold=0.08:ratio=3:attack=8:release=120:makeup=2', sp], check=True)
voz, _ = sf.read(sp, dtype='float32'); N = int(TOT * SR) + SR; mix = np.zeros((N, 2), np.float32); vmask = np.zeros(N)
for g in SEGS:
    x = cut(voz, g['a'], g['b'], 1.0, fade=0.03); place(mix, x * (0.11 / rms(x)), g['t0']); vmask[int(g['t0'] * SR):int(g['t1'] * SR)] = 1
BPM = 100; BT = 60 / BPM; mus = np.zeros((N, 2), np.float32)
ACORDES = [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64]]  # Dm Bb F C
for k in range(int(TOT / BT) + 2):
    at = k * BT; ac = ACORDES[(k // 8) % 4]
    if k % 8 == 0:
        for m_ in ac: x = note(mfreq(m_), 8 * BT, 0.05, 0.25, 0.4); place(mus, np.repeat(x[:, None], 2, 1), at)
    place(mus, np.repeat(note(mfreq(ac[0] - 12), BT * 0.9, 0.16, 5, 0.3)[:, None], 2, 1), at)
    if k % 2: place(mus, np.repeat(tick()[:, None], 2, 1) * 0.25, at)
    if k % 4 == 0: place(mus, np.repeat(note(mfreq(ac[3] + 12), BT, 0.04, 6, 1.2)[:, None], 2, 1), at + BT / 2)
mus /= np.abs(mus).max() + 1e-9
mv = 0.42 - 0.3 * env_follow(vmask, 0.3); fo = int((TOT - 1.6) * SR); mv[fo:] *= np.linspace(1, 0, N - fo); mv[:int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
mix += mus * mv[:, None] * 0.6
def sfx(x, at, gn): place(mix, np.repeat(x[:, None], 2, 1), at, gn)
sfx(impact(1.0), 0.05, 0.35); sfx(swell(1.6), TV - 0.2, 0.25)
for ct in CORTES: sfx(whoosh(0.35), ct - 0.18, 0.18)
aud = finish_audio(mix[:int(TOT * SR)], WD)

# ---------- 7. quadros
VIG = vignette(120); NF = int(TOT * FPS)
os.makedirs('/home/claude/re/out', exist_ok=True)
saida = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/re/out/falathiagoo_estudio_v1.mp4'
so = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
wr = None if so else Writer(saida, aud)
TRANS = {1: 'zoom', 4: 'whip', 7: 'zoom', 10: 'whip'}
quadros = [int(x * FPS) for x in so] if so else range(NF)
for n in quadros:
    t = n / FPS; tt = min(t, TV - 0.04)
    im, name = compor(tt)
    # transições com motion blur em alguns cortes
    for j, ct in enumerate(CORTES):
        kind = TRANS.get(j)
        if kind and ct - 0.2 <= tt < ct: im = trans_out(kind, im, (tt - (ct - 0.2)) / 0.2)
        elif kind and ct <= tt < ct + 0.2: im = trans_in(kind, im, 1 - (tt - ct) / 0.2)
    c = im.convert('RGBA'); c.alpha_composite(VIG)
    if t < TV: legenda(c, t); tarja(c, t)
    bug(c, t)
    if t >= TV:  # fecho: escurece e assina
        p = clamp((t - TV) / 0.6); c = Image.blend(c, Image.new('RGBA', (W, H), (4, 6, 12, 255)), 0.7 * p)
        a1 = text_img('PLENÁRIA CE', font('Anton', 150), (255, 255, 255)); a2 = text_img('@falathiagoo', font('Inter800', 56), AC)
        im1, dy = (a1, 0); paste(c, light_sweep(a1, clamp((t - TV - 0.6) / 1.2)), 540, 860, alpha=p); paste(c, a2, 540, 1000, alpha=clamp((t - TV - 0.5) / 0.5))
    c = grain(c, n, 0.08)
    if so: c.convert('RGB').save(f'/home/claude/re/out/prova_{t:05.1f}.jpg', quality=88)
    else: wr.write(c)
if wr: wr.close()
print('DONE', round(TOT, 2))
