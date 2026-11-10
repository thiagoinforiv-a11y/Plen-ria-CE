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

for c in E["cartoes"]:
    if c["tipo"] == "lista":
        for j in range(len(c["itens"])): por(pop(), c["de"] + 0.4 + j * 0.3, 0.5, 0.3 if j % 2 else -0.3)
    if c["tipo"] == "nome": por(whoosh(0.35), c["de"], 0.5, -0.6)

# trilha de fundo sintetizada (opcional, "fundo": true): acordes suaves em loop, baixa sob a voz e sobe no fechamento
if E.get("fundo"):
    n = len(buf); t = np.arange(n) / SR; bed = np.zeros(n)
    acordes = [[261.63, 329.63, 392.0, 493.88], [220.0, 261.63, 329.63, 392.0], [174.61, 220.0, 261.63, 329.63], [196.0, 246.94, 293.66, 392.0]]
    dur_ac = 2.4
    for k in range(int(n / SR / dur_ac) + 1):
        i0 = int(k * dur_ac * SR); i1 = min(n, int((k + 1) * dur_ac * SR + 0.6 * SR)); tt = np.arange(i1 - i0) / SR
        env = np.minimum(1, tt / 0.5) * np.exp(-np.maximum(0, tt - dur_ac) * 6)
        for f in acordes[k % 4]: bed[i0:i1] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * env * 0.05
        bed[i0:i1] += np.sin(2 * np.pi * acordes[k % 4][0] / 2 * tt) * env * 0.08
    # pulso leve (batida) para dar ritmo
    for b in np.arange(0, n / SR, 0.6):
        i = int(b * SR); m = min(n - i, int(0.15 * SR)); tt = np.arange(m) / SR
        bed[i:i + m] += np.sin(2 * np.pi * (55 + 40 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 18) * 0.12
    fimde = E.get("fim", {}).get("de", 1e9)
    g = np.where(t < fimde, 0.35, 0.35 + 0.65 * np.minimum(1, (t - fimde) / 0.6))
    g *= np.minimum(1, (n / SR - t) / 1.0)
    buf[:, 0] += bed * g; buf[:, 1] += bed * g
    if fimde < 1e8: por(impacto(1.6), fimde, 0.8)

with wave.open(saida, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())
