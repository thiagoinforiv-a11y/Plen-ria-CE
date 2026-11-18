# Próximos passos dos vídeos (anotado em 05/11/2026)

Prontos e entregues (MP4 leve, enviado ao Thiago): históricos 2016–2028 (Varjota, Pacujá, Reriutaba, Pires Ferreira,
Ipu, Santa Quitéria, Cariré); "vereadores, um por um" (Varjota + as 6 cidades); raio-X de Varjota; estúdio virtual (teste).

A fazer:
1. Versão curta para viralizar: série por cidade — Parte 1 "Quem manda na Câmara", Parte 2 "As surpresas",
   Parte 3 "2028" (30–45 s cada; gancho nos 2 primeiros segundos; legenda grande; pergunta no fim).
2. Um vídeo por vereador (20–30 s) para collab — oferecer a TODOS os vereadores (perfil @falathiagoo é neutro).
3. Estúdio virtual com gravação nova na parede branca + elementos visuais do raio-X.
4. "Fim de um ciclo em Pacujá": aguardando os vídeos de Alex Melo, Milena Melo, Raimundo Filho e a foto do grupo 2024.
   Narrar sem interpretar falas, sem ligar à cassação, sem sugerir que um vídeo respondeu ao outro.

Como gerar: `node video/historico.mjs ce/<cidade>`, `node video/dados-vereadores-detalhe.mjs ce/<cidade>`,
push de video/narracao.json → narração (branch narracao), `python3 video/mixar.py --trilha ...`, `node video/gravar.mjs ...`.
Entrega: comprimir (crf 25, maxrate 2200k) e enviar como anexo — no celular só aparece o botão de salvar assim.
