---
name: estilos-video
description: Catálogo de estilos de edição com nome (ex.: "elétrico", "partículas · política") para aplicar sobre vídeos filmados pelo Thiago ou gerar vídeos animados. Use quando ele pedir "edita no estilo X", mandar um vídeo de referência para virar estilo novo, ou mandar um bruto para finalizar.
---

# Estilos de vídeo

Cada estilo é um arquivo em `video/estilos/<nome>.html` (desenha um quadro a partir do vídeo filmado + roteiro) e, se tiver, um gerador de trilha `video/estilos/som_<nome>.py`.

## Catálogo

| Estilo | Para quê | Arquivos |
|---|---|---|
| **entrega** (vlog comercial, padrão Super Choque Motos) | entrega de moto, evento de parceiro, depoimento de cliente | `estilos/entrega.html`, `transcrever.py` |
| **elétrico** (quadrinhos, "super-herói elétrico") | vídeo filmado com ação: entrega, chegada, bastidor, anúncio | `estilos/eletrico.html`, `estilos/som_eletrico.py` |
| **partículas · política** | raio-X de político, eleição, dados | `cena-*.html` + skill `motion-graphics` |

### entrega (padrão do Thiago, referência: vídeo "Mais uma entrega" da Super Choque Motos × Posto Kelly)
Cortes secos a cada 0,6–1,5 s no começo e falas mais longas depois; leve aproximação em cada trecho. Abertura com logo + "MAIS UMA" (branco, espaçado) e "ENTREGA" (vermelho, grande). Legenda em caixa alta Montserrat 800, branca, palavra-chave em vermelho (#ff3d1f), filete vermelho embaixo, a 80% da altura, 2–3 palavras por vez. Pílulas no topo ("ENTREGA SUPER CHOQUE", "BINGO · DIA 26", "CONVIDADOS ESPECIAIS"). Logo do parceiro salta na hora em que é citado. Fecho em fundo vinho: "Entrega feita." com a foto da entrega em moldura, "Chave entregue pela Super Choque." e cartão da marca ("compra, troca e venda de motos", "em parceria com").
Roteiro: `{ "trechos": [[arquivo, ini, fim], ...] (ou --video já montado), "palavras": "auto", "vocab": "nomes próprios", "destaques": [...], "titulo": [t0, t1, "MAIS UMA", "ENTREGA", logo], "pilulas": [[t0, t1, "TEXTO", "vermelha"|"branca"]], "logos": [[t0, t1, png, x, y, largura]], "extra": s, "final": { t0, foto, titulo, rodape, logo, slogan, parceiro } }`. Com `"palavras": "auto"`, a fala é transcrita aqui (`video/transcrever.py`, faster-whisper, roda sem internet depois de baixar o modelo); confira nomes próprios no `.palavras.json` antes do render final. Logos e vídeos ficam em `entregas/midia/` (fora do git).

### elétrico
Cor fria e contrastada, vinheta azul-escura; faíscas em volta da pessoa o tempo todo; em cada batida: flash branco-azulado, soco de zoom, tremida, separação de cor, 3 raios das bordas até a pessoa e linhas de velocidade; balões de texto em quadrinhos (estrela vermelha ou azul, retícula, letra Anton amarela com contorno preto e brilho azul); granulação leve. Trilha original: batida eletrônica a 128 bpm + choque, impacto e "whoosh" em cada batida.

## Como aplicar (vídeo filmado)

1. Assista o bruto (quadros a cada 1 s) e marque: onde está a pessoa (`alvo`, 0–1), os momentos fortes (`batidas`, em segundos, de preferência a cada 1,5 s) e os textos (2 a 3 palavras, `\n` quebra a linha).
2. Roteiro `entregas/<x>.roteiro.json`: `{ "alvo": [0.5, 0.42], "textoY": 0.2, "ini": 0, "dur": 12, "batidas": [...], "textos": [[t0, t1, "TEXTO", "amarelo"|"azul"]] }`.
3. Trilha: `python3 video/estilos/som_eletrico.py --roteiro R --dur D --saida trilha.wav [--video bruto.mp4]` (com `--video`, mistura a voz/áudio original por baixo).
4. Render: `node video/estilo.mjs --estilo eletrico --video bruto.mp4 --roteiro R --audio trilha.wav --saida entregas/<x>.mp4`.
5. Se houver fala, legende por cima com `video/legendar.py` (precisa do tempo das palavras).

## Estilo novo a partir de uma referência

1. Quadros da referência (grid a cada ~1 s), cortes (`ffmpeg ... select='gt(scene,0.2)'`), voz (altura) e ritmo.
2. Anote: paleta, letra, transições, efeitos de batida, ritmo dos cortes, legenda, música.
3. Crie `video/estilos/<nome>.html` copiando o `eletrico.html` e troque as camadas. Não copie personagem, logotipo ou nome de marca de terceiros; reproduza a linguagem visual.
4. Teste com vídeo de banco gratuito (Pixabay, chave no ambiente) antes do bruto real e registre aqui no catálogo.

Vídeos e roteiros de pessoas ficam em `entregas/` (fora do git).
