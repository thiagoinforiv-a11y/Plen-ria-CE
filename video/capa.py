#!/usr/bin/env python3
"""Capa (thumbnail) 1080×1920 no padrão Plenária: fundo da própria cena, manchete grande, fotos em círculo com aro.
Conteúdo importante fica entre y 240 e 1680 (a grade do perfil mostra a capa cortada em 3:4).
Uso: python3 video/capa.py --fundo quadro.jpg --kicker "CÂMARA DE VARJOTA" --linha1 "SÓ 3" --linha2 "FICARAM NAS 3" --fotos a.jpg,b.jpg,c.jpg --nomes "A,B,C" --rodape "..." --saida capa.jpg"""
import argparse, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
R = os.path.dirname(os.path.abspath(__file__)); FT = lambda w, s: ImageFont.truetype(os.path.join(R, "fontes", "ttf", f"Montserrat-{w}.ttf"), s)
OURO, TX, T2, FUNDO = (245, 196, 81), (242, 245, 248), (147, 161, 176), (10, 14, 20)
ap = argparse.ArgumentParser()
for k in ("fundo", "kicker", "linha1", "linha2", "fotos", "nomes", "rodape", "saida"): ap.add_argument("--" + k, default="")
ap.add_argument("--recorte", default="0,420,1080,1140"); a = ap.parse_args()
W, H = 1080, 1920; cap = Image.new("RGB", (W, H), FUNDO)
if a.fundo:
    x0, y0, x1, y1 = map(int, a.recorte.split(",")); bg = Image.open(a.fundo).convert("RGB").crop((x0, y0, x1, y1)).resize((W, int(W * (y1 - y0) / (x1 - x0))))
    bg = ImageEnhance.Brightness(bg).enhance(1.05); y = 590; cap.paste(bg, (0, y))
    import numpy as np
    hh = bg.height; v = np.arange(hh) / hh; a_ = np.clip(1 - np.minimum(v / 0.22, (1 - v) / 0.3), 0, 1) ** 1.4   # escurece só as bordas de cima e de baixo
    m = Image.fromarray((np.tile(a_[:, None], (1, W)) * 255).astype("uint8")); cap.paste(Image.new("RGB", (W, hh), FUNDO), (0, y), m)
d = ImageDraw.Draw(cap)
def centro(txt, y, fonte, cor, esp=0):
    w = d.textlength(txt, font=fonte) + esp * (len(txt) - 1); x = (W - w) / 2
    if esp:
        for ch in txt: d.text((x, y), ch, font=fonte, fill=cor); x += d.textlength(ch, font=fonte) + esp
    else: d.text((x, y), txt, font=fonte, fill=cor)
centro(a.kicker, 250, FT(800, 34), OURO, esp=8)
f1 = FT(900, 200); centro(a.linha1, 300, f1, TX)
f2 = FT(900, 92 if len(a.linha2) > 12 else 120); centro(a.linha2, 520, f2, OURO)
fotos = [f for f in a.fotos.split(",") if f]; nomes = a.nomes.split(",")
if fotos:
    n = len(fotos); r = 135 if n == 3 else 170; gap = (W - 2 * 60) / n
    for i, (f, nome) in enumerate(zip(fotos, nomes)):
        cx, cy = int(60 + gap * (i + 0.5)), 1250; im = Image.open(f).convert("RGB"); s = 2 * r / min(im.width, im.height * 0.8); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        quad = Image.new("RGB", (2 * r, 2 * r)); quad.paste(im, (int(r - im.width / 2), int(-0.05 * r)))
        mask = Image.new("L", (2 * r * 4, 2 * r * 4), 0); ImageDraw.Draw(mask).ellipse((0, 0, 2 * r * 4 - 1, 2 * r * 4 - 1), fill=255); mask = mask.resize((2 * r, 2 * r), Image.LANCZOS)
        glow = Image.new("RGBA", (2 * r + 120, 2 * r + 120), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((50, 50, 2 * r + 70, 2 * r + 70), fill=OURO + (170,)); glow = glow.filter(ImageFilter.GaussianBlur(28))
        cap.paste(glow, (cx - r - 60, cy - r - 60), glow); d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), fill=OURO); cap.paste(quad, (cx - r, cy - r), mask)
        tam = 38
        while d.textlength(nome, font=FT(800, tam)) > gap - 28: tam -= 1
        fn = FT(800, tam); w = d.textlength(nome, font=fn); d.text((cx - w / 2, cy + r + 30), nome, font=fn, fill=TX)
centro(a.rodape, 1600, FT(700, 34), T2)
cap.save(a.saida, quality=94); print("✔", a.saida)
