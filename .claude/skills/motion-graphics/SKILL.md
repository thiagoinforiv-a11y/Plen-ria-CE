---
name: motion-graphics
description: Faz vídeos verticais (9:16) em motion graphics no padrão Plenária CE — partículas que viram mapa, barras e anéis, tipografia cinética palavra a palavra, números que contam, foto em círculo no fecho. Use quando o Thiago pedir "faça um vídeo", raio-X de político, análise de eleição em vídeo ou material animado interno.
---

# Motion graphics Plenária CE

Vídeo 1080×1920, 30 fps, desenhado em canvas (`video/cena-*.html`) e gravado com Playwright (`video/gravar.mjs`).

## Passo a passo

1. **Dados primeiro.** Tudo sai do TSE (`data/ce/<cidade>.js`, seção a seção) ou de outra fonte oficial. Gere um `video/dados-<nome>.json` só com o que a cena usa. Não invente número, nome nem fala.
2. **Roteiro em cenas.** 8 a 13 cenas de ~7 s. Cada cena tem: título curto, um visual de partículas (forma), um número de impacto e uma frase-legenda. Termine com foto em círculo + 3 linhas de fecho.
3. **Cena.** Copie a cena mais parecida (`cena-lia.html`, `cena-cid.html`, `cena-lucy.html`, `cena-camara-renovacao.html`) e troque `forma.*`, `KF` e `render`. Formas prontas: `ranking` (barras), colunas, anel, mapa por bairro/local, dispersão seção a seção, grade de seções, halo.
4. **Provas.** `node video/gravar.mjs --cena X.html --provas <pasta> t1,t2,...` e monte um grid. Se a tela vier sem partículas, procure NaN (posições inválidas somem; uma forma quebrada contamina a cena seguinte na transição).
5. **Narração (vídeo público).** Textos em `video/narracao.json` → commit/push → automação do GitHub gera `video/audio/<id>/antonio/NN.mp3` na branch `narracao`. Uma frase por cena. Evite reticências. Números por extenso.
6. **Mixagem e gravação.**
   `python3 video/mixar.py --trilha video/trilha-X.json --voz antonio --saida entregas/X/a.wav --mapa entregas/X/a.mapa.json`
   `node video/gravar.mjs --cena cena-X.html entregas/X/raw.mp4 30 --trilha video/trilha-X.json --mapa entregas/X/a.mapa.json --audio entregas/X/a.wav`
   `ffmpeg -i raw.mp4 -c:v libx264 -crf 25 -maxrate 2200k -bufsize 4400k -c:a aac -b:a 128k -movflags +faststart final.mp4`

## Tipografia cinética

Palavras entram uma a uma (escala + subida). `*palavra*` = destaque dourado, maior e com brilho. Use em títulos e frases de impacto; deixe números grandes com `texto()`.

```js
const kin = (frase, x, y, t, t0, t1, o = {}) => { /* ver cena-lucy-kelly.local.html */ };
kin("A BASE *CRESCEU*", W / 2, 300, t, S[4] + 0.3, S[5], { tam: 80 });
```

Regras: no máximo 6 palavras por linha; 1 destaque por linha; título no topo (y≈300), legenda embaixo (y≈1600); nada abaixo de y≈1780 (marca e fonte).

## Público × interno

- **Público (@falathiagoo / @plenariace):** tom de notícia, sem pedido de voto, sem "apoio", "grupo", "padrinho", "traição" ou "racha". Cena, dados e narração podem ir ao GitHub.
- **Interno (apoio político, estratégia, briefing):** arquivos com `.local.` no nome (`video/cena-*.local.html`, `video/*.local.json`), que o `.gitignore` não versiona. Sem narração automática (ela passa pelo GitHub público): use só trilha, com faixas mudas em `video/audio/<id>/antonio/NN.mp3` (ruído baixíssimo, 0,2 s). O vídeo sai em `entregas/` com "INTERNO" no nome.
- Foto de pessoa enviada pelo Thiago fica em `entregas/midia/` (fora do git). Foto oficial de candidato pode vir de `fotos/` (TSE).
