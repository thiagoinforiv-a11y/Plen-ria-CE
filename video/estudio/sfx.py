import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
_rng = np.random.default_rng(7)
def _bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype='band', fs=SR, output='sos'), x)
def whoosh(d=0.5):
    n = int(d * SR); t = np.linspace(0, 1, n); x = _rng.standard_normal(n); acc = np.zeros(n); k = 8
    for i in range(k):
        a, b = i * n // k, (i + 1) * n // k; fc = 300 + 3500 * np.sin(np.pi * (a + b) / 2 / n) ** 2
        acc[a:b] = _bp(x, fc * 0.6, min(fc * 1.6, 20000))[a:b]
    e = np.sin(np.pi * t) ** 2.2
    return (acc * e / (np.abs(acc).max() + 1e-9) * 0.8).astype(np.float32)
def impact(d=1.1):
    n = int(d * SR); t = np.arange(n) / SR; f = 52 + 90 * np.exp(-t * 18); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 4.0); nz = _bp(_rng.standard_normal(n), 80, 2500) * np.exp(-t * 22) * 0.6
    x = np.tanh((body + nz) * 1.6); return (x / np.abs(x).max() * 0.9).astype(np.float32)
def pop(d=0.12):
    n = int(d * SR); t = np.arange(n) / SR; f = 900 * np.exp(-t * 30) + 380
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * 0.8).astype(np.float32)
def tick(d=0.04):
    n = int(d * SR); t = np.arange(n) / SR; x = _bp(_rng.standard_normal(n), 2500, 9000) * np.exp(-t * 160)
    return (x / np.abs(x).max() * 0.6).astype(np.float32)
def riser(d=1.0):
    n = int(d * SR); t = np.linspace(0, 1, n); x = _rng.standard_normal(n); acc = np.zeros(n); k = 10
    for i in range(k):
        a, b = i * n // k, (i + 1) * n // k; fc = 400 + 6000 * ((a + b) / 2 / n) ** 2
        acc[a:b] = _bp(x, fc * 0.7, min(fc * 1.4, 20000))[a:b]
    tone = np.sin(2 * np.pi * np.cumsum(200 + 600 * t ** 2) / SR) * 0.25
    y = (acc / (np.abs(acc).max() + 1e-9) + tone) * t ** 2.0; return (y / np.abs(y).max() * 0.8).astype(np.float32)
def swell(d=1.6):
    n = int(d * SR); t = np.linspace(0, 1, n)
    x = sum(np.sin(2 * np.pi * f * np.arange(n) / SR) for f in (110, 165, 220, 330)) / 4
    return (x * np.sin(np.pi * t) ** 1.5 * 0.6).astype(np.float32)
out = np.zeros(1)
