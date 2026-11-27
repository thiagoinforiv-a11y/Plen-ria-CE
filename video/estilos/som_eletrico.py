#!/usr/bin/env python3
"""Trilha do estilo elétrico (original, sem direitos): batida eletrônica + choque elétrico, impacto e "whoosh" em cada batida do roteiro.
Uso: python3 video/estilos/som_eletrico.py --roteiro r.json --dur 10.8 --saida trilha.wav [--video bruto.mp4 (mistura o áudio original baixo)]"""
import argparse, json, subprocess, numpy as np
from scipy.signal import butter, sosfilt
SR = 48000; rng = np.random.default_rng(7)
def env(n, a=0.005, r=0.2): t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / r)
def choque(d=0.45):
    n = int(d * SR); t = np.arange(n) / SR; x = rng.standard_normal(n) * (rng.random(n) < 0.18)              # estalos
    x = sosfilt(butter(2, [1800, 9000], "bandpass", fs=SR, output="sos"), x) * 3
    zum = np.sign(np.sin(2 * np.pi * (120 + 40 * np.sin(2 * np.pi * 9 * t)) * t)) * 0.35                      # zumbido de alta tensão
    return (x + zum * sosfilt(butter(2, 2500, "lowpass", fs=SR, output="sos"), rng.standard_normal(n)) * 0.6 + zum * 0.25) * env(n, 0.002, d / 3)
def impacto(d=0.9):
    n = int(d * SR); t = np.arange(n) / SR; f = 70 * np.exp(-t * 6) + 38
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.28) * 1.4 + sosfilt(butter(2, 1200, "lowpass", fs=SR, output="sos"), rng.standard_normal(n)) * env(n, 0.001, 0.05) * 0.8
def whoosh(d=0.5):
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n)
    for i in range(0, n, 2400):
        fc = 400 + 5000 * (i / n) ** 2; seg = sosfilt(butter(2, [fc, fc * 1.6], "bandpass", fs=SR, output="sos"), x[i:i + 2400]); out[i:i + len(seg)] = seg
    return out * np.sin(np.pi * np.arange(n) / n) ** 2 * 1.5
def batida(dur, bpm=128):
    n = int(dur * SR); x = np.zeros(n); pb = 60 / bpm
    kick = impacto(0.4) * 0.9; hat = sosfilt(butter(2, 7000, "highpass", fs=SR, output="sos"), rng.standard_normal(int(0.05 * SR))) * env(int(0.05 * SR), 0.001, 0.015) * 0.5
    t = 0.0; k = 0
    while t < dur:
        i = int(t * SR)
        if k % 2 == 0: x[i:i + len(kick)] += kick[: n - i]
        j = int((t + pb / 2) * SR)
        if j < n: x[j:j + len(hat)] += hat[: n - j]
        b = int(t * SR); m = min(n - b, int(pb * SR)); tt = np.arange(m) / SR; nota = [55, 55, 65.4, 49][(k // 2) % 4]
        x[b:b + m] += sosfilt(butter(2, 400, "lowpass", fs=SR, output="sos"), np.sign(np.sin(2 * np.pi * nota * tt))) * env(m, 0.005, 0.18) * 0.35
        t += pb / 2 * 2; k += 1
    return x
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--roteiro", required=True); ap.add_argument("--dur", type=float, required=True); ap.add_argument("--saida", required=True); ap.add_argument("--video")
    a = ap.parse_args(); R = json.load(open(a.roteiro)); n = int(a.dur * SR); fx = np.zeros(n); mus = batida(a.dur)
    def por(x, t, g):
        i = max(0, int(t * SR)); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g
    for b in R["batidas"]: por(whoosh(), b - 0.45, 0.5); por(impacto(), b, 0.9); por(choque(), b, 0.8)
    mix = mus / (np.abs(mus).max() + 1e-9) * 0.55 + fx / (np.abs(fx).max() + 1e-9) * 0.8
    if a.video:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-t", str(a.dur), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        v = np.frombuffer(raw, dtype=np.float32)[:n]
        if len(v): mix[: len(v)] += v / (np.abs(v).max() + 1e-9) * 0.3
    mix = np.stack([mix, mix], 1); mix /= np.abs(mix).max() / 0.9
    import wave
    with wave.open(a.saida + ".tmp.wav", "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.saida + ".tmp.wav", "-af", "loudnorm=I=-12:TP=-1:LRA=9", "-ar", str(SR), a.saida], check=True); import os; os.remove(a.saida + ".tmp.wav"); print("✔", a.saida)
main()
