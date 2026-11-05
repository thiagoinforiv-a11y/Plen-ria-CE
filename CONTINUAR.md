# Para continuar o trabalho (sessão nova)

Leia este arquivo e depois `video/PROXIMOS-PASSOS.md` e `video/estudio/LEIAME.md`.
Branch de trabalho: `claude/mapa-politico-varjota`.

## Quem e o quê
- Thiago Costa (@falathiagoo, Kroma.mov, Varjota-CE). Fala pelo celular, muitas vezes por áudio transcrito
  (nomes chegam errados: "Divajosa" = Varjota, "Rede Otávio" = Reriutaba, "Rig Fields" = Higgsfield).
- Responder sempre em **português**, curto.
- Projeto Plenária CE: site de inteligência eleitoral (index.html + assets/js/app.js + data/ce/*.js) e uma série de
  vídeos verticais 1080×1920 em estilo escuro com partículas (video/*.html renderizados por video/gravar.mjs).

## Regras que não podem ser quebradas
- Repositório é **público**: informação local de grupos políticos, apoios e lideranças fica só em arquivos ignorados
  (`data/**/*.local.js`, `video/*.local.json`). Nada disso em commit, narração ou legenda.
- Perfil @falathiagoo é de notícia: tom **neutro**, sem pedido de voto, sem palavras como "traição" ou "racha".
- Não inventar nomes, números ou falas; dado oficial do TSE prevalece sobre busca na web.
- Áudio/vídeo de pessoas só vai ao GitHub (transcrição) com autorização explícita do Thiago a cada vez.
- Nunca ajudar em compra de voto (art. 41-A). Não publicar CPF/título.

## Como entregar vídeo
- Comprimir (`-crf 25 -maxrate 2200k`) e enviar como **anexo** (display "attach"): só assim o celular mostra o botão
  de compartilhar/salvar. Arquivos grandes ou enviados como prévia não baixam.
- Legenda sempre em uma linha; duração ideal 30–45 s para viralizar.

## Estado em 05/11/2026
- Entregues: históricos 2016–2028 das 7 cidades (Varjota, Pacujá, Reriutaba, Pires Ferreira, Ipu, Santa Quitéria,
  Cariré); "vereadores, um por um" das 7 cidades; raio-X de Varjota; estúdio virtual (teste com vídeo do carro).
- Plugins instalados pelo Thiago (carregam em sessão nova): Headroom, cartographer, transcribe-so, Speedometer.
  Sugerido também: Social Media Skills.
- Narração: GitHub Action `narracao.yml` (edge-tts, voz Antonio) → branch `narracao`; reaproveita faixas já geradas.
- Dados TSE: Action `importar-tse.yml` (lista em data/fontes/importar-tse.txt) → branch `dados-tse`; ignora
  eleições suplementares (ex.: Santa Quitéria 2025 está registrada na ficha, não nos dados de 2024).
- Próximo: versão curta para viralizar (partes 1/2/3 por cidade) e um vídeo por vereador para collab
  (oferecer a todos os vereadores, de todos os grupos).
