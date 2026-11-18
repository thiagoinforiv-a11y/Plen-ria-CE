#!/usr/bin/env python3
"""Trilha para vlog comercial (original, sem direitos): batida leve e efeitos nos momentos do roteiro, com a fala em primeiro plano.
Uso: python3 video/estilos/som_vlog.py --video video_editado.mp4 --roteiro r.json --saida final.mp4
Efeitos: whoosh nas pílulas e no título, pop nos logos/cartões, impacto no fecho; música abaixa sob a voz."""
import argparse, json, subprocess, numpy as np
from scipy.signal import butter, sosfilt
SR = 48000; rng = np.random.default_rng(3)
def env(n, a=0.005, r=0.2): t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / r)
lp = lambda x, f: sosfilt(butter(2, f, "lowpass", fs=SR, output="sos"), x); hp = lambda x, f: sosfilt(butter(2, f, "highpass", fs=SR, output="sos"), x)
def kick(): n = int(.35 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-t * 30)) / SR) * env(n, .002, .12)
def hat(): n = int(.06 * SR); return hp(rng.standard_normal(n), 7000) * env(n, .001, .02) * .35
def whoosh(d=.55):
    n = int(d * SR); x = rng.standard_normal(n); o = np.zeros(n)
    for i in range(0, n, 2400): fc = 300 + 5200 * (i / n) ** 1.6; seg = sosfilt(butter(2, [fc, fc * 1.7], "bandpass", fs=SR, output="sos"), x[i:i + 2400]); o[i:i + len(seg)] = seg
    return o * np.sin(np.pi * np.arange(n) / n) ** 2 * 1.4
def pop(): n = int(.12 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * (900 - 2500 * t) * t) * env(n, .001, .03)
def impacto(): n = int(1.2 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 8)) / SR) * env(n, .002, .4) + lp(rng.standard_normal(n), 900) * env(n, .001, .08) * .6
def musica(dur, bpm=100):
    n = int(dur * SR); x = np.zeros(n); pb = 60 / bpm; acordes = [[220, 261.6, 329.6], [196, 246.9, 293.7], [174.6, 220, 261.6], [196, 246.9, 293.7]]
    t = 0.0; k = 0
    while t < dur:
        i = int(t * SR); kk = kick(); x[i:i + len(kk)] += kk[: n - i] * (1 if k % 2 == 0 else .55)
        j = int((t + pb / 2) * SR); hh = hat()
        if j < n: x[j:j + len(hh)] += hh[: n - j]
        if k % 4 == 0:
            m = min(n - i, int(pb * 4 * SR)); tt = np.arange(m) / SR; pad = sum(np.sin(2 * np.pi * f * tt) for f in acordes[(k // 4) % 4]) / 3
            x[i:i + m] += lp(pad, 1800) * np.minimum(1, tt / .4) * np.exp(-tt / 3) * .35
        t += pb; k += 1
    return x
ap = argparse.ArgumentParser(); ap.add_argument("--video", required=True); ap.add_argument("--roteiro", required=True); ap.add_argument("--saida", required=True); a = ap.parse_args()
R = json.load(open(a.roteiro)); dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
voz = np.frombuffer(raw, dtype=np.float32).astype(float); n = int(dur * SR); voz = np.pad(voz, (0, max(0, n - len(voz))))[:n]
fx = np.zeros(n)
def por(x, t, g): i = max(0, int(t * SR)); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g
if R.get("titulo"): por(whoosh(.7), R["titulo"][0], .8); por(impacto(), R["titulo"][0] + .3, .6)
for p in R.get("pilulas", []): por(whoosh(), p[0] - .35, .6); por(pop(), p[0], .5)
for l in R.get("logos", []): por(pop(), l[0], .7)
if R.get("nome"): por(whoosh(.5), R["nome"][0] - .3, .6)
for c in R.get("extras_sfx", []): por(pop(), c, .6)
if R.get("final"): por(whoosh(.8), R["final"]["t0"] - .5, .8); por(impacto(), R["final"]["t0"], .8)
mu = musica(dur); voz /= max(1e-6, np.abs(voz).max()); mu /= max(1e-6, np.abs(mu).max()); fx /= max(1e-6, np.abs(fx).max())
e = lp(np.abs(voz), 4); duck = 1 - .65 * np.clip(e / (np.percentile(e[e > 1e-4], 70) + 1e-9), 0, 1)
mix = voz * .9 + mu * .22 * duck + fx * .35; mix /= np.abs(mix).max() / .95
import wave, os
w = a.saida + ".wav"
with wave.open(w, "wb") as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((mix * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-i", w, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1:LRA=9", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", a.saida], check=True); os.remove(w); print("✔", a.saida)
