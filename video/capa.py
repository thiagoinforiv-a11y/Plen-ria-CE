#!/usr/bin/env python3
"""Capa (thumbnail) 1080×1920 no padrão Plenária: fundo da própria cena, manchete grande, fotos em círculo com aro.
Tudo fica dentro da área central 1080×1350 (y 300–1600): é o que aparece no feed do Reels (4:5) e na grade do perfil (3:4), sem corte.
Gera também <saida>-areas.jpg mostrando os cortes, para conferir.
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
    bg = ImageEnhance.Brightness(bg).enhance(1.05); y = 640; bg = bg.crop((0, 0, W, min(bg.height, 620))); cap.paste(bg, (0, y))
    import numpy as np
    hh = bg.height; v = np.arange(hh) / hh; a_ = np.clip(1 - np.minimum(v / 0.22, (1 - v) / 0.3), 0, 1) ** 1.4   # escurece só as bordas de cima e de baixo
    m = Image.fromarray((np.tile(a_[:, None], (1, W)) * 255).astype("uint8")); cap.paste(Image.new("RGB", (W, hh), FUNDO), (0, y), m)
d = ImageDraw.Draw(cap)
def centro(txt, y, fonte, cor, esp=0):
    w = d.textlength(txt, font=fonte) + esp * (len(txt) - 1); x = (W - w) / 2
    if esp:
        for ch in txt: d.text((x, y), ch, font=fonte, fill=cor); x += d.textlength(ch, font=fonte) + esp
    else: d.text((x, y), txt, font=fonte, fill=cor)
centro(a.kicker, 335, FT(800, 32), OURO, esp=7)
t1 = 180
while d.textlength(a.linha1, font=FT(900, t1)) > W - 120: t1 -= 4
centro(a.linha1, 370 + (180 - t1) // 2, FT(900, t1), TX)
t2 = 104
while d.textlength(a.linha2, font=FT(900, t2)) > W - 120: t2 -= 2
centro(a.linha2, 568 + (104 - t2) // 2, FT(900, t2), OURO)
fotos = [f for f in a.fotos.split(",") if f]; nomes = a.nomes.split(",")
if fotos:
    n = len(fotos); r = 122 if n == 3 else 160; gap = (W - 2 * 60) / n
    for i, (f, nome) in enumerate(zip(fotos, nomes)):
        cx, cy = int(60 + gap * (i + 0.5)), 1235; im = Image.open(f).convert("RGB"); s = 2 * r / min(im.width, im.height * 0.8); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=90, threshold=2))
        quad = Image.new("RGB", (2 * r, 2 * r)); quad.paste(im, (int(r - im.width / 2), int(-0.05 * r)))
        mask = Image.new("L", (2 * r * 4, 2 * r * 4), 0); ImageDraw.Draw(mask).ellipse((0, 0, 2 * r * 4 - 1, 2 * r * 4 - 1), fill=255); mask = mask.resize((2 * r, 2 * r), Image.LANCZOS)
        glow = Image.new("RGBA", (2 * r + 120, 2 * r + 120), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((50, 50, 2 * r + 70, 2 * r + 70), fill=OURO + (170,)); glow = glow.filter(ImageFilter.GaussianBlur(28))
        cap.paste(glow, (cx - r - 60, cy - r - 60), glow); d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), fill=OURO); cap.paste(quad, (cx - r, cy - r), mask)
        tam = 38
        while d.textlength(nome, font=FT(800, tam)) > gap - 28: tam -= 1
        fn = FT(800, tam); w = d.textlength(nome, font=fn); d.text((cx - w / 2, cy + r + 26), nome, font=fn, fill=TX)
centro(a.rodape, 1500, FT(700, 30), T2)
cap.save(a.saida, quality=97, subsampling=0); print("✔", a.saida)
prev = cap.copy(); pd = ImageDraw.Draw(prev, "RGBA")
for (y0, y1, cor, nome) in ((285, 1635, (255, 80, 80, 255), "feed 4:5"), (240, 1680, (90, 180, 255, 255), "grade 3:4")):
    pd.rectangle((4, y0, W - 5, y1), outline=cor, width=5); pd.text((14, y0 + 8), nome, font=FT(800, 26), fill=cor)
prev.resize((540, 960)).save(a.saida.rsplit(".", 1)[0] + "-areas.jpg", quality=85)
