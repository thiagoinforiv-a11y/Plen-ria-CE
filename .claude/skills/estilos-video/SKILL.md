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
| **tela** (gravação de tela estilo TikTok) | mostrar painel, estudo, sistema ou site rolando no celular, com fala | `legendar.py --estilo tela`, gravação com Playwright |
| **elétrico** (quadrinhos, "super-herói elétrico") | vídeo filmado com ação: entrega, chegada, bastidor, anúncio | `estilos/eletrico.html`, `estilos/som_eletrico.py` |
| **partículas · política** | raio-X de político, eleição, dados | `cena-*.html` + skill `motion-graphics` |

### entrega (padrão do Thiago, referência: vídeo "Mais uma entrega" da Super Choque Motos × Posto Kelly)
Cortes secos a cada 0,6–1,5 s no começo e falas mais longas depois; leve aproximação em cada trecho. Abertura com logo + "MAIS UMA" (branco, espaçado) e "ENTREGA" (vermelho, grande). Legenda em caixa alta Montserrat 800, branca, palavra-chave em vermelho (#ff3d1f), filete vermelho embaixo, a 80% da altura, 2–3 palavras por vez. Pílulas no topo ("ENTREGA SUPER CHOQUE", "BINGO · DIA 26", "CONVIDADOS ESPECIAIS"). Logo do parceiro salta na hora em que é citado. Fecho em fundo vinho: "Entrega feita." com a foto da entrega em moldura, "Chave entregue pela Super Choque." e cartão da marca ("compra, troca e venda de motos", "em parceria com").
Roteiro: `{ "trechos": [[arquivo, ini, fim], ...] (ou --video já montado), "palavras": "auto", "vocab": "nomes próprios", "destaques": [...], "titulo": [t0, t1, "MAIS UMA", "ENTREGA", logo], "pilulas": [[t0, t1, "TEXTO", "vermelha"|"branca"]], "logos": [[t0, t1, png, x, y, largura]], "extra": s, "final": { t0, foto, titulo, rodape, logo, slogan, parceiro } }`. Com `"palavras": "auto"`, a fala é transcrita aqui (`video/transcrever.py`, faster-whisper, roda sem internet depois de baixar o modelo); confira nomes próprios no `.palavras.json` antes do render final. Logos e vídeos ficam em `entregas/midia/` (fora do git).

### tela (referência: vídeo "Claude Arrogante" do Mestres da IA)
Tela do celular (432×768 CSS × 2,5 = 1080×1920) rolando a página com pausas nos pontos citados na fala; título fixo nos primeiros 4 s em caixas brancas com letra preta (`--titulo "Linha 1|Linha 2"`); legenda branca com contorno preto, como foi falada, 2–3 palavras. Fluxo: página pronta (passe antes o `lapidador-visual`) → gravar rolagem com Playwright (`page.screenshot` quadro a quadro, scrollTo por tempo) + narração → `transcrever.py` → corrija nomes no `.json` → `legendar.py --estilo tela --y 1520 --tam 76 --titulo ...`.

### elétrico
Cor fria e contrastada, vinheta azul-escura; faíscas em volta da pessoa o tempo todo; em cada batida: flash branco-azulado, soco de zoom, tremida, separação de cor, 3 raios das bordas até a pessoa e linhas de velocidade; balões de texto em quadrinhos (estrela vermelha ou azul, retícula, letra Anton amarela com contorno preto e brilho azul); granulação leve. Trilha original: batida eletrônica a 128 bpm + choque, impacto e "whoosh" em cada batida.

## Limpar o bruto falado (antes de qualquer estilo)
`python3 video/transcrever.py --video bruto.mp4 --saida bruto.palavras.json --vocab "nomes"` → `python3 video/cortar.py --video bruto.mp4 --palavras bruto.palavras.json --saida limpo.mp4`. Corta os silêncios e lista tropeços (repetição, frase recomeçada) em `limpo.tropecos.md` para revisar; os aprovados vão em `--cortes aprovados.json` (`{"cortes":[{"ini":..,"fim":..}]}`). Gancho: os 3 primeiros segundos precisam dar um motivo para assistir até o fim.

## Como aplicar (vídeo filmado)

1. Assista o bruto (quadros a cada 1 s) e marque: onde está a pessoa (`alvo`, 0–1), os momentos fortes (`batidas`, em segundos, de preferência a cada 1,5 s) e os textos (2 a 3 palavras, `\n` quebra a linha).
2. Roteiro `entregas/<x>.roteiro.json`: `{ "alvo": [0.5, 0.42], "textoY": 0.2, "ini": 0, "dur": 12, "batidas": [...], "textos": [[t0, t1, "TEXTO", "amarelo"|"azul"]] }`.
3. Trilha: `python3 video/estilos/som_eletrico.py --roteiro R --dur D --saida trilha.wav [--video bruto.mp4]` (com `--video`, mistura a voz/áudio original por baixo).
4. Render: `node video/estilo.mjs --estilo eletrico --video bruto.mp4 --roteiro R --audio trilha.wav --saida entregas/<x>.mp4`.
5. Se houver fala, legende por cima com `video/legendar.py` (precisa do tempo das palavras).

## Referências públicas consultadas (14/11/2026, todas MIT)
- nateherkai/herk-edit-kit: pipeline de edição em agentes (cortar silêncio → cortar tropeço → edição curta), "gancho de 3 s", nota do usuário vira regra.
- MakersMCP/easycaptionkit: legenda fora da área dos botões de cada app (zona segura).
- Barty-Bart/motion-graphics: passe de som medido, com efeitos gravados CC0 em vez de sintetizados; B-roll de uma forma só que se transforma.
- bangtutorial/bang-motion e Vincentwei1021/anything2explainer: motion em HTML/GSAP renderizado quadro a quadro (mesmo método nosso), explicadores narrados.
Usamos as ideias; o código aqui é nosso.

## Estilo novo a partir de uma referência

1. Quadros da referência (grid a cada ~1 s), cortes (`ffmpeg ... select='gt(scene,0.2)'`), voz (altura) e ritmo.
2. Anote: paleta, letra, transições, efeitos de batida, ritmo dos cortes, legenda, música.
3. Crie `video/estilos/<nome>.html` copiando o `eletrico.html` e troque as camadas. Não copie personagem, logotipo ou nome de marca de terceiros; reproduza a linguagem visual.
4. Teste com vídeo de banco gratuito (Pixabay, chave no ambiente) antes do bruto real e registre aqui no catálogo.

Vídeos e roteiros de pessoas ficam em `entregas/` (fora do git).

## Zona segura (TikTok, Reels, Shorts)
Os botões do app (lado direito, de y≈900 a 1700) e a descrição do post (de y≈1500 para baixo) cobrem o vídeo. Texto que precisa ser lido fica entre **y 220 e 1450** e **x 60 a 940**. Legenda: `--y 1440` (padrão). Marca e fonte podem ficar embaixo (são secundárias).

## Nota vira regra
Quando o Thiago corrigir algo num vídeo ("tira a tarja", "legenda muito embaixo", "corte feio"), corrija e registre a correção como regra nesta skill, com a data, para o próximo já sair certo.

## Padrão de entrega (pedido do Thiago em 14/11/2026: vale para TODO vídeo)
1. **Narração** sempre (`video/narrar_local.py <id>` gera voz + tempo das palavras aqui mesmo; texto em `narracao.json`, ou em `*.local.json` se for interno).
2. **Fotos das pessoas** citadas, sempre que existirem: foto oficial do TSE (`fotos/ce/<cidade>/<ano>/<sq>.jpg`; anos antigos saem do pacote do TSE lendo só os arquivos necessários, sem baixar o zip inteiro). Foto em círculo com aro da cor do estado, nunca quadrada.
3. **Capa (thumbnail)** junto com o vídeo: `video/capa.py` (fundo da própria cena sem textos — `cena.html?limpo=1` —, manchete curta em 2 linhas, fotos com aro e brilho, rodapé com a fonte). Conteúdo entre y 240 e 1680 por causa do corte 3:4 da grade do perfil.
4. **O mais ilustrado possível**: objeto 3D ou mapa quando o tema tem um lugar; nada de "aberração" (forma estranha, texto sobre desenho, borda cortada). Prova em 4 tempos antes de gravar.
