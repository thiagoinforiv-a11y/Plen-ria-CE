import os, json, math, subprocess, hashlib, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import butter, sosfilt, fftconvolve
W, H, FPS, SR = 1080, 1920, 30, 48000
POOL = '/home/claude/pool'
TM = 'zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p'
WJ = json.load(open(f'{POOL}/words.json')) if os.path.exists(f'{POOL}/words.json') else {}
FD = '/home/claude/fonts/'
def font(name, size): return ImageFont.truetype(FD + name + '.ttf', size)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def e_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def e_io(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def e_back(x, s=1.7): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def is_hlg(p):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=color_transfer', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout
    return 'arib' in o
def plan(segs):
    t = 0.0; out = []
    for g in segs:
        g = dict(g); g.setdefault('speed', 1.0); g.setdefault('zoom', 1.0); g.setdefault('cx', 0.5); g.setdefault('cy', 0.5)
        g['dur'] = (g['b'] - g['a']) / g['speed']; g['t0'] = t; g['t1'] = t + g['dur']; t += g['dur']; out.append(g)
    return out, t
def render_base(segs, wd, grade, force=False):
    os.makedirs(wd, exist_ok=True); lst = open(f'{wd}/list.txt', 'w')
    for g in segs:
        p = f'{POOL}/{g["clip"]}.mov'; nf = round(g['t1'] * FPS) - round(g['t0'] * FPS)
        key = hashlib.md5(repr((g['clip'], g['a'], g['b'], g['speed'], g['zoom'], g['cx'], g['cy'], g.get('freeze'), g.get('grade'), grade, nf)).encode()).hexdigest()[:10]
        out = f'{wd}/p_{key}.mp4'; z = g['zoom']; sp = g['speed']
        tim = f'setpts=PTS/{sp},' + (f'minterpolate=fps={FPS}:mi_mode=blend,' if sp < 0.99 else f'fps={FPS},')
        if g.get('freeze'): tim = f'fps={FPS},trim=end_frame=1,setpts=PTS-STARTPTS,'
        vf = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,'
        if z > 1.001: vf = f'scale={int(1080*z)//2*2}:{int(1920*z)//2*2}:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920:(iw-1080)*{g["cx"]}:(ih-1920)*{g["cy"]},'
        vf += (TM + ',' if is_hlg(p) else '') + tim + (g.get('grade') or grade)
        if force or not os.path.exists(out):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(g['a']), '-i', p, '-vf', vf + f',tpad=stop_mode=clone:stop_duration={g["dur"] + 2 if g.get("freeze") else 2}',
                            '-frames:v', str(nf), '-an', '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-pix_fmt', 'yuv420p', out], check=True)
        lst.write(f"file '{out}'\n")
    lst.close()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt', '-c', 'copy', f'{wd}/base.mp4'], check=True)
    return f'{wd}/base.mp4'
class Reader:
    def __init__(self, path): self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE); self.last = None
    def next(self):
        raw = self.p.stdout.read(W * H * 3)
        if len(raw) == W * H * 3: self.last = Image.frombuffer('RGB', (W, H), raw).copy()
        return self.last
class Writer:
    def __init__(self, out, audio, crf=20):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', audio, '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    def write(self, im): self.p.stdin.write(im.convert('RGB').tobytes())
    def close(self): self.p.stdin.close(); self.p.wait()
_ac = {}
def clip_audio(c, wd):
    if c not in _ac:
        fn = f'{wd}/_a_{c}.wav'
        if not os.path.exists(fn): subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{POOL}/{c}.mov', '-vn', '-ac', '2', '-ar', str(SR), fn], check=True)
        _ac[c] = sf.read(fn, dtype='float32')[0]
    return _ac[c]
def speech_clean(c, wd):
    k = c + '_sp'
    if k not in _ac:
        fn = f'{wd}/_s_{c}.wav'
        if not os.path.exists(fn): subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{POOL}/{c}.mov', '-vn', '-ac', '2', '-ar', str(SR), '-af', 'highpass=f=110,highpass=f=110,afftdn=nr=10:nf=-45:tn=1,equalizer=f=310:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.4:g=2.5,deesser,acompressor=threshold=0.08:ratio=3:attack=8:release=120:makeup=2', fn], check=True)
        _ac[k] = sf.read(fn, dtype='float32')[0]
    return _ac[k]
def cut(x, a, b, speed=1.0, fade=0.02):
    y = x[int(a * SR):int(b * SR)].copy()
    if speed != 1.0: y = y[(np.arange(int(len(y) / speed)) * speed).astype(int)]
    f = min(int(fade * SR), len(y) // 2)
    if f > 0: y[:f] *= np.linspace(0, 1, f)[:, None]; y[-f:] *= np.linspace(1, 0, f)[:, None]
    return y
def rms(x): return float(np.sqrt(np.mean(x ** 2)) + 1e-9)
def place(buf, x, at, g=1.0):
    i = int(at * SR); n = min(len(x), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += x[:n] * g
def env_follow(mask, win=0.25): k = int(win * SR); return np.convolve(mask, np.ones(k) / k, mode='same')
def reverb(x, sec=2.2, wet=0.3, seed=1):
    n = int(sec * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    ir = sosfilt(butter(2, 5000, fs=SR, output='sos'), np.stack([rng.standard_normal(n) * np.exp(-t * 3.0) for _ in range(2)], 1), axis=0)
    w = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1); w /= np.abs(w).max() + 1e-9
    return x / (np.abs(x).max() + 1e-9) * (1 - wet) + w * wet
def finish_audio(mix, wd, name='mix'):
    sf.write(f'{wd}/{name}_raw.wav', mix.astype(np.float32), SR)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{wd}/{name}_raw.wav', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=7', '-ar', str(SR), f'{wd}/{name}.wav'], check=True)
    return f'{wd}/{name}.wav'
def note(freq, dur, amp=0.3, decay=2.2, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * decay * (1 + 0.35 * k)) for k, a in [(1, 1), (2, 0.45 * bright), (3, 0.22 * bright), (4, 0.1 * bright), (5, 0.05 * bright)])
    att = int(0.004 * SR); x[:att] *= np.linspace(0, 1, att); return (x * amp).astype(np.float32)
def mfreq(m): return 440 * 2 ** ((m - 69) / 12)
def text_img(s, fnt, fill, stroke=0, sfill=None, pad=8, shadow=None):
    l, tp, r, b = fnt.getbbox(s, stroke_width=stroke); im = Image.new('RGBA', (r - l + 2 * pad, b - tp + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shadow: d.text((pad - l + shadow[0], pad - tp + shadow[1]), s, font=fnt, fill=shadow[2], stroke_width=stroke, stroke_fill=shadow[2])
    d.text((pad - l, pad - tp), s, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=sfill); return im
def paste(c, im, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    if im is None or alpha <= 0.01 or scale <= 0.01: return
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if abs(scale - 1) > 1e-3: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 1: a = im.getchannel('A').point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2); sx, sy = max(0, -x), max(0, -y); ex, ey = min(im.width, W - x), min(im.height, H - y)
    if ex > sx and ey > sy: c.alpha_composite(im.crop((sx, sy, ex, ey)), (x + sx, y + sy))
def words(clip, a, b): return [(s, e, w.strip()) for seg in WJ.get(clip, []) for (s, e, w) in seg if a - 0.05 <= s < b - 0.05]
GN = [(np.asarray(Image.fromarray(np.random.default_rng(i).normal(128, 40, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.int16) - 128) for i in range(6)]
def grain(c, n, amt=0.25):
    a = np.asarray(c.convert('RGB'), np.int16); return Image.fromarray(np.clip(a + (GN[n % 6] * amt)[..., None], 0, 255).astype(np.uint8)).convert('RGBA')
def vignette(strength=150, cy=0.5):
    yy, xx = np.mgrid[0:H, 0:W]; v = np.clip((np.hypot((xx - 540) / 540, (yy - H * cy) / (H * 0.5)) - 0.55) / 0.75, 0, 1) ** 1.5 * strength
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255)); im.putalpha(Image.fromarray(v.astype(np.uint8))); return im
