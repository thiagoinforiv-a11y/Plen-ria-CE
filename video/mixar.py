#!/usr/bin/env python3
"""Monta a trilha do vídeo: narração (uma faixa por cena) + efeitos sonoros sintetizados (sem música).
Cada cena estica para caber a fala; o mapa de tempo (cena → vídeo) vai para o gravador.
Uso: python3 video/mixar.py --voz antonio --saida trilha.wav --mapa mapa.json"""
import argparse, json, os, subprocess
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
RAIZ = os.path.dirname(os.path.abspath(__file__))
# início de cada cena no tempo da animação (cena.html), e fim
S = [0, 5.6, 11.2, 16.6, 20.6, 28.2, 35.2, 44.3, 52.3, 61.3, 68.3, 75.3, 82.0]
rng = np.random.default_rng(3)

def ler(arq):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", arq, "-af", "highpass=f=70,lowshelf=g=2:f=140,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,aecho=0.8:0.6:38:0.06",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def env(n, a=0.01, r=0.3):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / r); return e

def whoosh(d=0.7):
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = 512
    for i in range(0, n, seg):
        f = 300 + 3500 * np.sin(np.pi * i / n) ** 2
        sos = butter(2, [f * 0.6, min(f * 1.6, 20000)], "bandpass", fs=SR, output="sos"); out[i:i + seg] = sosfilt(sos, x[i:i + seg])
    return out * np.sin(np.pi * np.arange(n) / n) ** 2 * 0.5

def boom(d=1.6):
    n = int(d * SR); t = np.arange(n) / SR; f = 38 + 30 * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    c = sosfilt(butter(2, 2500, "lowpass", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t * 40) * 0.4
    return (s + c) * 0.9

def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 180) * 0.35

def pop():
    n = int(0.12 * SR); t = np.arange(n) / SR; f = 700 * np.exp(-t * 14) + 180; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * 0.5

def riser(d):
    n = int(d * SR); t = np.arange(n) / SR; f = 180 + 900 * (t / d) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + sosfilt(butter(2, 3000, "highpass", fs=SR, output="sos"), rng.standard_normal(n)) * 0.12
    return s * (t / d) ** 1.6 * (1 - np.clip((t - d + 0.08) / 0.08, 0, 1))

def swell(d=2.4, base=220):
    n = int(d * SR); t = np.arange(n) / SR; s = sum(np.sin(2 * np.pi * base * r * t) for r in (1, 1.26, 1.5, 2)) / 4
    return s * np.sin(np.pi * t / d) ** 2 * 0.22

def urna():  # bipes curtos, como a confirmação da urna eletrônica
    partes = []
    for f, d in ((1480, .07), (1250, .07), (1480, .07), (1250, .07), (1480, .32)):
        n = int(d * SR); t = np.arange(n) / SR; partes.append(np.sin(2 * np.pi * f * t) * np.minimum(1, (d - t) / 0.01) * np.minimum(1, t / 0.004)); partes.append(np.zeros(int(.012 * SR)))
    x = np.concatenate(partes); return sosfilt(butter(2, [400, 5000], "bandpass", fs=SR, output="sos"), x) * 0.35

def bip():
    n = int(0.09 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 1480 * t) * np.minimum(1, (0.09 - t) / 0.01) * 0.3

def radar(d):  # varredura: tom fino que sobe e "pings" espaçados
    n = int(d * SR); t = np.arange(n) / SR; base = sosfilt(butter(2, [800, 2400], "bandpass", fs=SR, output="sos"), rng.standard_normal(n)) * 0.05
    for k in np.arange(0.2, d, 0.55):
        i = int(k * SR); m = min(n - i, int(0.5 * SR)); tt = np.arange(m) / SR; base[i:i + m] += np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 9) * 0.25
    return base

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--voz", default="antonio"); ap.add_argument("--saida", required=True); ap.add_argument("--mapa", required=True)
    a = ap.parse_args()
    pasta = os.path.join(RAIZ, "audio", a.voz)
    falas = [ler(os.path.join(pasta, f"{i:02d}.mp3")) for i in range(len(S) - 1)]
    lead = [0.9] + [0.45] * (len(S) - 2)
    V = [0.0]
    for k in range(len(S) - 1):
        V.append(V[-1] + max(S[k + 1] - S[k], lead[k] + len(falas[k]) / SR + 0.75))
    def tv(ts):  # tempo da animação → tempo do vídeo
        k = max(i for i in range(len(S) - 1) if S[i] <= ts) if ts < S[-1] else len(S) - 2
        return V[k] + (ts - S[k]) * (V[k + 1] - V[k]) / (S[k + 1] - S[k])
    tot = int((V[-1] + 0.5) * SR); voz = np.zeros(tot); fx = np.zeros(tot)
    def por(buf, x, t, g=1.0):
        i = int(t * SR); j = min(tot, i + len(x)); buf[i:j] += x[: j - i] * g
    for k, f in enumerate(falas): por(voz, f, V[k] + lead[k])
    for k in range(1, len(S) - 1): por(fx, whoosh(), max(0, tv(S[k]) - 0.35), 0.55)
    for t in (0.6, 16.7, 77.2): por(fx, boom(), tv(t), 0.8)
    por(fx, riser(tv(20.2) - tv(16.9)), tv(16.9), 0.35)
    por(fx, radar(tv(20.2) - tv(17.0)), tv(17.0), 0.6)
    for a0, a1 in ((7.0, 9.4), (22.4, 24.2), (29.8, 31.6), (45.6, 48.4), (62.4, 64.6), (69.8, 71.4)):
        x0, x1 = tv(a0), tv(a1); t = x0; passo = 0.05
        while t < x1: por(fx, tick(), t, 0.5); passo *= 1.07; t += passo
    for t in (12.6, 13.5, 14.4): por(fx, bip(), tv(t), 0.8)          # pontos da linha do tempo: bipe da urna
    por(fx, urna(), tv(52.9), 0.9)                                    # maior local: confirmação da urna
    for t in (21.4, 21.7, 29.0, 29.3, 57.0, 62.0, 62.3): por(fx, pop(), tv(t), 0.45)
    for t, b in ((38.4, 196), (58.2, 175), (75.4, 220)): por(fx, swell(base=b), tv(t), 0.8)
    # níveis: voz na frente; efeitos ~15 dB abaixo e ainda mais baixos (ducking) enquanto a voz fala
    voz /= max(1e-6, np.sqrt(np.mean(voz[np.abs(voz) > 1e-3] ** 2)))
    fx /= max(1e-6, np.sqrt(np.mean(fx[np.abs(fx) > 1e-3] ** 2)))
    e = sosfilt(butter(1, 4, "lowpass", fs=SR, output="sos"), np.abs(voz))
    duck = 1 - 0.5 * np.clip(e / (np.percentile(e[e > 1e-3], 60) + 1e-9), 0, 1)
    mix = voz + fx * 10 ** (-15 / 20) * duck
    mix /= max(1e-6, np.abs(mix).max()) / 0.9
    tmp = a.saida + ".raw.wav"
    import wave
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), "-ac", "2", a.saida], check=True); os.remove(tmp)
    json.dump({"S": S, "V": V}, open(a.mapa, "w"))
    print("✔ trilha", a.saida, f"{V[-1]:.1f}s")

main()
