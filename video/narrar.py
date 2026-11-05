#!/usr/bin/env python3
"""Gera a narração do vídeo com vozes neurais (Microsoft Edge TTS), uma faixa por cena e por voz.
Roda na automação do GitHub (este ambiente não alcança o serviço de voz).
Saída: video/audio/<vídeo>/<voz>/NN.mp3 e NN.json (tempo de cada palavra, em segundos)."""
import asyncio, json, os, sys
import edge_tts

RAIZ = os.path.dirname(os.path.abspath(__file__))

async def cena(texto, v, base):
    com = edge_tts.Communicate(texto, v["voz"], rate=v["rate"], pitch=v["pitch"], boundary="WordBoundary")
    palavras = []
    with open(base + ".mp3", "wb") as f:
        async for c in com.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                palavras.append({"t": c["offset"] / 1e7, "d": c["duration"] / 1e7, "p": c["text"]})
    json.dump(palavras, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False)

async def main():
    cfg = json.load(open(os.path.join(RAIZ, "narracao.json"), encoding="utf-8"))
    for vid, cenas in cfg["videos"].items():
        for v in cfg["vozes"]:
            pasta = os.path.join(RAIZ, "audio", vid, v["id"]); os.makedirs(pasta, exist_ok=True)
            for i, t in enumerate(cenas):
                await cena(t, v, os.path.join(pasta, f"{i:02d}"))
                print("✔", vid, v["id"], i)

asyncio.run(main())
