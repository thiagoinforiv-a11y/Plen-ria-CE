# Estúdio virtual (teste de 05/11/2026)

Coloca uma pessoa gravada com o celular num estúdio de telejornal da Plenária CE, com várias câmeras virtuais.

1. `seg.html` + `seg.mjs`: recorte da pessoa quadro a quadro (MediaPipe Selfie Segmentation no Chromium;
   pacote npm `@mediapipe/selfie_segmentation`, copiado para `mp/`). Entrada: quadros em `f/`, saída: máscaras em `m/`.
2. `estudio_virtual.py`: monta o cenário (telão de LED, bancada, monitor com o mapa do CE), estabiliza a pessoa,
   corta pausas pela transcrição (words.json, faster-whisper com tempo por palavra), troca de câmera a cada frase,
   legenda em uma linha, tarja, trilha de jornal sintetizada e SFX. Usa `lib2.py`, `fx.py` e `sfx.py`.
   Fontes em /home/claude/fonts (Anton, Inter 500/800/900, Source Serif 4 itálico: npm @fontsource, woff2 → ttf).

Limites: troca de roupa e ângulos realmente novos exigem IA generativa de vídeo (não disponível aqui).
Melhor gravação: fundo liso (parede branca), 1–1,5 m da parede, luz de frente, roupa escura lisa, 1080p/4K.
