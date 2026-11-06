#!/usr/bin/env python3
"""Efeitos sonoros sintetizados para a edição (sem direitos autorais): whoosh na entrada de cada cartão,
pop + tique de contagem nos números, impacto grave na pergunta e na tarja de abertura.
Uso: python3 video/sfx_edicao.py edicao.json saida.wav duracao"""
import json, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)
E = json.load(open(sys.argv[1], encoding="utf-8")); saida = sys.argv[2]; dur = float(sys.argv[3])
buf = np.zeros((int((dur + 2) * SR), 2))

def por(x, t, g=1.0, pan=0.0):
    i = int(t * SR); j = min(len(buf), i + len(x)); x = x[: j - i] * g
    buf[i:j, 0] += x * np.cos((pan + 1) * np.pi / 4); buf[i:j, 1] += x * np.sin((pan + 1) * np.pi / 4)

def whoosh(d=0.45):
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = 512
    for i in range(0, n, seg):
        f = 400 + 4000 * np.sin(np.pi * i / n) ** 2
        out[i:i + seg] = sosfilt(butter(2, [f * 0.6, min(f * 1.6, 20000)], "bandpass", fs=SR, output="sos"), x[i:i + seg])
    return out * np.sin(np.pi * np.arange(n) / n) ** 2 * 0.6

def pop():
    n = int(0.12 * SR); t = np.arange(n) / SR; f = 900 * np.exp(-t * 16) + 200
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28) * 0.7

def tique():
    n = int(0.025 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200) * 0.35

def impacto(d=1.2):
    n = int(d * SR); t = np.arange(n) / SR; f = 60 * np.exp(-t * 2) + 30
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)
    c = sosfilt(butter(2, [900, 6000], "bandpass", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t * 50) * 0.4
    return (s + c) * 0.9

if E.get("tarja"): por(impacto(), 0.05, 0.7); por(whoosh(), 0.0, 0.6, -0.5)
for i, c in enumerate(E["cartoes"]):
    lado = {"esq": -0.6, "dir": 0.6}.get(c.get("lado"), 0.0)
    por(whoosh(), max(0, c["de"] - 0.2), 0.8, lado)
    if c["tipo"] == "foto": por(pop(), c["de"] + 0.15, 0.6, lado)
    else:
        por(pop(), c["de"] + 0.1, 0.9)
        if c.get("valor") is not None:
            t = c["de"]; passo = 0.04
            while t < c["de"] + 0.9: por(tique(), t, 0.6); passo *= 1.08; t += passo
        if c.get("texto") == "?": por(impacto(), c["de"], 0.9)
for t, z in (E.get("zooms") or [])[1:]:
    if z > 1: por(whoosh(0.25), max(0, t - 0.1), 0.25)
buf /= max(1e-6, np.abs(buf).max()) / 0.8
with wave.open(saida, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes())
