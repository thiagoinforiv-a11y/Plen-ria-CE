#!/usr/bin/env python3
"""Narra aqui mesmo (sem passar pelo GitHub): mesmas vozes do video/narracao.json, com o tempo de cada palavra.
Uso: python3 video/narrar_local.py <id do vídeo em narracao.json | arquivo .json com a lista de falas> [--video-id nome] [--voz antonio]
Saída: video/audio/<id>/<voz>/NN.mp3 e NN.json (o mixar.py lê os dois). Precisa do serviço de voz liberado no ambiente."""
import argparse, asyncio, json, os, edge_tts
RAIZ = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("fonte"); ap.add_argument("--video-id"); ap.add_argument("--voz", default="antonio"); a = ap.parse_args()
cfg = json.load(open(os.path.join(RAIZ, "narracao.json"), encoding="utf-8")); v = [x for x in cfg["vozes"] if x["id"] == a.voz][0]
falas = json.load(open(a.fonte, encoding="utf-8")) if a.fonte.endswith(".json") else cfg["videos"][a.fonte]
vid = a.video_id or os.path.basename(a.fonte).split(".")[0]; pasta = os.path.join(RAIZ, "audio", vid, a.voz); os.makedirs(pasta, exist_ok=True)
async def uma(i, t):
    for k in range(6):
        try:
            com = edge_tts.Communicate(t, v["voz"], rate=v["rate"], pitch=v["pitch"], boundary="WordBoundary", proxy=os.environ.get("HTTPS_PROXY")); pal = []
            with open(f"{pasta}/{i:02d}.mp3", "wb") as f:
                async for c in com.stream():
                    if c["type"] == "audio": f.write(c["data"])
                    elif c["type"] == "WordBoundary": pal.append({"t": c["offset"] / 1e7, "d": c["duration"] / 1e7, "p": c["text"]})
            json.dump(pal, open(f"{pasta}/{i:02d}.json", "w", encoding="utf-8"), ensure_ascii=False); print("✔", vid, i); return
        except Exception as e:
            print("… de novo", i, type(e).__name__); await asyncio.sleep(3 + 3 * k)
    raise SystemExit(f"falhou a fala {i}")
async def main():
    for i, t in enumerate(falas): await uma(i, t)
asyncio.run(main())
