#!/usr/bin/env python3
"""Recorta a pessoa do fundo, quadro a quadro (máscara de IA, MODNet, Apache-2.0, roda local com onnxruntime).
Uso: python3 video/recortar.py --quadros pasta_com_00001.jpg... --saida pasta_mascaras [--modelo entregas/_modelos/modnet.onnx]
Gera <saida>/00001.png ... (PNG com transparência: opaco = pessoa). Suaviza no tempo para não tremer.
O modelo baixa uma vez de huggingface.co/Xenova/modnet (onnx/model.onnx) para entregas/_modelos/."""
import argparse, glob, os, numpy as np
import onnxruntime as ort
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument("--quadros", required=True); ap.add_argument("--saida", required=True)
ap.add_argument("--modelo", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "entregas", "_modelos", "modnet.onnx")); ap.add_argument("--suave", type=float, default=0.55)
a = ap.parse_args(); os.makedirs(a.saida, exist_ok=True)
s = ort.InferenceSession(a.modelo, providers=["CPUExecutionProvider"]); ant = None
fs = sorted(glob.glob(os.path.join(a.quadros, "*.jpg")))
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGB"); W, H = im.size; r = 512 / max(W, H); w, h = int(W * r) // 32 * 32, int(H * r) // 32 * 32
    x = (np.asarray(im.resize((w, h), Image.BILINEAR), dtype=np.float32) / 255 - 0.5) / 0.5
    m = s.run(None, {"input": x.transpose(2, 0, 1)[None]})[0][0, 0]
    if ant is not None: m = a.suave * ant + (1 - a.suave) * m      # suaviza no tempo
    ant = m
    al = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR); rgba = Image.new("RGBA", (W, H), (255, 255, 255, 0)); rgba.putalpha(al); rgba.save(os.path.join(a.saida, os.path.basename(f).replace(".jpg", ".png")))
    if i % 100 == 0: print(f"{i}/{len(fs)}")
print("✔", a.saida, len(fs), "máscaras")
