#!/usr/bin/env python3
"""Transcreve a fala de um vídeo/áudio em português, com o tempo de cada palavra (para legenda sincronizada).
Uso: python3 video/transcrever.py --video bruto.mp4 --saida palavras.json [--modelo small]
Saída: [{"t": início, "d": duração, "p": "palavra"}], no mesmo formato que o video/legendar.py lê. Roda local (faster-whisper)."""
import argparse, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
ap = argparse.ArgumentParser(); ap.add_argument("--video", required=True); ap.add_argument("--saida", required=True); ap.add_argument("--modelo", default="small"); ap.add_argument("--vocab", default="", help="nomes próprios que ajudam a transcrição (ex.: Kelly, Tapuio, Cariré)")
a = ap.parse_args()
m = WhisperModel(a.modelo, device="cpu", compute_type="int8")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
segs, info = m.transcribe(np.frombuffer(raw, dtype=np.float32), language="pt", word_timestamps=True, vad_filter=True, initial_prompt=a.vocab or None)
pal = []
for s in segs:
    for w in s.words:
        pal.append({"t": round(w.start, 3), "d": round(w.end - w.start, 3), "p": w.word.strip()})
json.dump(pal, open(a.saida, "w", encoding="utf-8"), ensure_ascii=False)
print("✔", a.saida, len(pal), "palavras")
print(" ".join(w["p"] for w in pal))
