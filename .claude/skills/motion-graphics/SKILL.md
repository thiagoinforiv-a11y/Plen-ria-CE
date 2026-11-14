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

## Acabamento (padrão a partir de 14/11/2026)

Inspirado na referência que o Thiago mandou: corte rápido no começo, uma ideia por tela, palavra-chave grande, transições que chamam atenção, câmera viva e legenda no compasso da voz.

1. **Ritmo.** Gancho nos primeiros 20–30 s: frases curtas (cenas de ~6 s, uma ideia cada). Depois, cenas mais longas para explicar. Feche com chamada para ação.
2. **`video/motion.js`** (inclua `<script src="motion.js"></script>` e, no fim da cena, antes de `window.render(0)`):
   `window.render = Motion.envolver(window.render, ctx, S, { respiro: [i], moldura: { serie: "RAIO-X · …", cta: "Comenta: …" } });`
   Dá câmera (empurrão lento + soco de zoom no corte), glitch e flash alternados nos cortes, respiro escuro antes da cena `i` (revelação) e a moldura (tarja da série no topo e chamada final).
3. **Música:** passe `--musica` no `mixar.py` (trilha original, abaixa sob a voz).
4. **Legenda sincronizada:** o `mixar.py` grava no mapa o tempo de cada palavra narrada. Depois de gravar o `raw.mp4`:
   `python3 video/legendar.py --video entregas/X/raw.mp4 --palavras entregas/X/a.mapa.json --saida entregas/X.mp4 --y 1720 --tam 74`
   Mostra 1 a 3 palavras por vez, a palavra dita entra com "pop", e número, sigla ou nome próprio sai em dourado. Fonte Oswald em `video/fontes/ttf/`. O `legendar.py` já comprime o vídeo final.
5. **Narração local.** O serviço de voz (speech.platform.bing.com) está liberado no ambiente: dá para narrar aqui, sem passar pelo GitHub (obrigatório para material interno). Guarde também o tempo de cada palavra (`NN.json`) para a legenda.

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

## Zona segura (TikTok, Reels, Shorts)
Os botões do app (lado direito, de y≈900 a 1700) e a descrição do post (de y≈1500 para baixo) cobrem o vídeo. Texto que precisa ser lido fica entre **y 220 e 1450** e **x 60 a 940**. Legenda: `--y 1440` (padrão). Marca e fonte podem ficar embaixo (são secundárias).

## Nota vira regra
Quando o Thiago corrigir algo num vídeo ("tira a tarja", "legenda muito embaixo", "corte feio"), corrija e registre a correção como regra nesta skill, com a data, para o próximo já sair certo.

## Objeto 3D que ilustra (referência: o prédio 3D do vídeo do condomínio)
Quando o assunto tem um "lugar" ou "objeto" que o público reconhece, monte ele em 3D e faça os dados acontecerem nele (como as janelas do prédio que acendem por situação). Base: `cena-camara-3d.html` (three.js em `video/vendor`, renderizado num canvas WebGL e copiado para o canvas 2D, com textos por cima). Ideias prontas:
- **Plenário** (cadeiras acendem por partido, por quem ficou/saiu, quem votou sim/não numa votação, a Mesa Diretora e o presidente).
- **Urna eletrônica** (abre e "imprime" o resultado de uma seção; ótimo para "urna a urna").
- **Prédio da prefeitura/escola/posto de saúde** (andares = secretarias; altura = gasto; janelas = contratos).
- **Mapa da cidade em relevo** (cada bairro sobe conforme os votos ou o gasto; "o voto tem endereço").
- **Cofre / pilha de moedas** (orçamento, emendas, repasse à Câmara).
- **Moto girando na vitrine** (estilo entrega, Super Choque).
Regras: câmera sempre em movimento lento; o objeto ocupa a metade de cima; nomes e números em lista na metade de baixo (nunca rótulo flutuando em cima de rótulo); fundo escuro com 1 cor de destaque; legenda de cores dentro da zona segura.
