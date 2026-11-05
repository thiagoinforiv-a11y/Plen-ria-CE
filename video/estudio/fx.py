import math, numpy as np
from PIL import Image, ImageFilter, ImageChops, ImageDraw
W, H = 1080, 1920
def _affine(im, scale=1.0, rot=0.0, dx=0.0, dy=0.0):
    a = math.radians(rot); ca, sa = math.cos(a) / scale, math.sin(a) / scale; cx, cy = W / 2, H / 2
    return im.transform((W, H), Image.AFFINE, (ca, sa, cx - ca * (cx + dx) - sa * (cy + dy), -sa, ca, cy + sa * (cx + dx) - ca * (cy + dy)), resample=Image.BILINEAR)
def avg(ims):
    acc = np.zeros((H, W, 3), np.float32)
    for im in ims: acc += np.asarray(im, np.float32)
    return Image.fromarray((acc / len(ims)).clip(0, 255).astype(np.uint8))
def mblur(im, f, n=6): return avg([_affine(im, **f(k / (n - 1))) for k in range(n)])
def ease_in(p): return p ** 2.4
def _roll(im, d0, d1, axis): return avg([Image.fromarray(np.roll(np.asarray(im), int(d0 + (d1 - d0) * k / 7), axis=axis)) for k in range(8)])
def trans_out(kind, im, p):
    if kind == 'zoom': s0 = 1 + 0.9 * ease_in(p); s1 = 1 + 0.9 * ease_in(min(1, p + 0.18)); return mblur(im, lambda k: dict(scale=s0 + (s1 - s0) * k))
    if kind == 'whip': return _roll(im, -W * 0.9 * ease_in(p), -W * 0.9 * ease_in(min(1, p + 0.2)), 1)
    if kind == 'glitch': return glitch(im, p, seed=int(p * 10))
    return im
def trans_in(kind, im, p):
    if kind == 'zoom': s0 = 1 + 0.6 * ease_in(p); s1 = 1 + 0.6 * ease_in(min(1, p + 0.18)); return mblur(im, lambda k: dict(scale=s0 + (s1 - s0) * k))
    if kind == 'whip': return _roll(im, W * 0.9 * ease_in(p), W * 0.9 * ease_in(min(1, p + 0.2)), 1)
    if kind == 'glitch': return glitch(im, p, seed=7 + int(p * 10))
    return im
def glitch(im, amt, seed=0):
    rng = np.random.default_rng(seed); a = np.asarray(im).copy(); o = int(40 * amt) + 4
    a = np.dstack([np.roll(a[..., 0], o, axis=1), a[..., 1], np.roll(a[..., 2], -o, axis=1)])
    for _ in range(int(10 * amt) + 2):
        y = rng.integers(0, H - 60); h = rng.integers(10, 90); a[y:y + h] = np.roll(a[y:y + h], rng.integers(-120, 120), axis=1)
    return Image.fromarray(a)
def shake(im, t, hits, amp=22, decay=0.22, seed=0):
    v = max([math.exp(-(t - h) / decay) for h in hits if t >= h] or [0])
    if v < 0.02: return im
    rng = np.random.default_rng(int(t * 1000) + seed); return _affine(im, scale=1.04, rot=rng.normal(0, 1.2 * v), dx=rng.normal(0, amp * v), dy=rng.normal(0, amp * v))
def bloom(im, thr=190, strength=0.55, rad=10):
    small = im.resize((W // 4, H // 4), Image.BILINEAR)
    m = small.convert('L').point(lambda v: 255 if v > thr else int(v * v / 255 * 0.15))
    glow = Image.composite(small, Image.new('RGB', small.size, (0, 0, 0)), m).filter(ImageFilter.GaussianBlur(rad)).resize((W, H), Image.BILINEAR)
    return ImageChops.screen(im, Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), glow, strength))
def blur_in(im, p, rise=14):
    p = max(0.0, min(1.0, p))
    if p >= 1: return im, 0
    r = 10 * (1 - p); out = im.filter(ImageFilter.GaussianBlur(r)) if r > 0.4 else im.copy()
    out.putalpha(out.getchannel('A').point(lambda v: int(v * p))); return out, int(rise * (1 - p) ** 2)
def light_sweep(im, p, width=0.18, col=(255, 255, 255)):
    if not 0 < p < 1: return im
    w, h = im.size; g = Image.new('L', (w, h), 0); x = int((-width + (1 + 2 * width) * p) * w); bw = int(width * w)
    ImageDraw.Draw(g).polygon([(x, 0), (x + bw, 0), (x + bw - h // 3, h), (x - h // 3, h)], fill=255)
    m = ImageChops.multiply(g.filter(ImageFilter.GaussianBlur(bw // 4 + 1)), im.getchannel('A'))
    lay = Image.new('RGBA', (w, h), col + (0,)); lay.putalpha(m.point(lambda v: int(v * 0.85))); out = im.copy(); out.alpha_composite(lay); return out
