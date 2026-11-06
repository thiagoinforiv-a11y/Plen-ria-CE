#!/usr/bin/env python3
"""Transcreve um vídeo gravado com tempo por palavra (faster-whisper, modelo small, CPU).
Uso: python3 video/transcrever.py entrada.mov saida.words.json
Precisa do huggingface.co liberado no ambiente (baixa o modelo uma vez). Arquivos de pessoas ficam em entregas/ (fora do git)."""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
segs, _ = WhisperModel("small", device="cpu", compute_type="int8").transcribe(a, language="pt", word_timestamps=True, vad_filter=True)
W = []
for s in segs:
    print(f"[{s.start:.1f}-{s.end:.1f}] {s.text.strip()}")
    W += [{"t": round(w.start, 2), "f": round(w.end, 2), "p": w.word.strip()} for w in s.words]
json.dump(W, open(sys.argv[2], "w"), ensure_ascii=False)
