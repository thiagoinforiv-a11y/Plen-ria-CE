#!/usr/bin/env python3
"""Gera a narração do vídeo com vozes neurais (Microsoft Edge TTS), uma faixa por cena e por voz.
Roda na automação do GitHub (este ambiente não alcança o serviço de voz).
Saída: video/audio/<vídeo>/<voz>/NN.mp3 e NN.json (tempo de cada palavra, em segundos)."""
import asyncio, hashlib, json, os, sys
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
    # VOZES=antonio limita às vozes pedidas; faixa já gerada com o mesmo texto e voz é reaproveitada (cache)
    so = [x for x in os.environ.get("VOZES", "").split(",") if x]
    for vid, cenas in cfg["videos"].items():
        for v in cfg["vozes"]:
            if so and v["id"] not in so:
                continue
            pasta = os.path.join(RAIZ, "audio", vid, v["id"]); os.makedirs(pasta, exist_ok=True)
            for i, t in enumerate(cenas):
                base = os.path.join(pasta, f"{i:02d}")
                h = hashlib.sha1(json.dumps([t, v], ensure_ascii=False).encode()).hexdigest()
                if os.path.exists(base + ".mp3") and os.path.exists(base + ".hash") and open(base + ".hash").read() == h:
                    continue
                for tent in range(4):  # o serviço de voz às vezes não devolve áudio; tenta de novo
                    try:
                        await cena(t, v, base); break
                    except edge_tts.exceptions.NoAudioReceived:
                        if tent == 3: raise
                        print("… sem áudio, tentando de novo:", vid, i); await asyncio.sleep(5 * (tent + 1))
                open(base + ".hash", "w").write(h)
                print("✔", vid, v["id"], i)

asyncio.run(main())
