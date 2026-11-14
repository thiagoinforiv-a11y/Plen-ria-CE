# Para continuar o trabalho (sessão nova)

## FLUXO ENXUTO (leia só isto para postar; economiza créditos)
1. Pauta → `video/noticias/<id>.json`: `{id, fontes, cenas:[{fala, tarja, midia?, ini?, credito?, grande?, sub?}]}`.
   Cenas curtas (1 frase), 5–7 cenas, 30–45 s. `midia` = foto/vídeo real enviado pelo Thiago (pasta entregas/ ou uploads).
2. Fala em narracao.json (`videos[id]`) → commit/push → Action gera a voz (branch narracao) → `git checkout origin/narracao -- video/audio`.
3. `node video/noticia.mjs video/noticias/<id>.json` → MP4 pronto (tarja azul, só ela na tela; sem partículas).
4. Copiar para o worktree da branch `midia` (noticias/), push, e agendar no Metricool (blogId 6990789, TikTok+IG,
   tiktokData.title obrigatório, isAigc/isAiGenerated true por causa da voz sintética, horário America/Fortaleza).
5. Vídeo gravado pelo Thiago (estilo análise política): `python3 video/transcrever.py bruto.mov entregas/brutos/X.words.json` →
   plano em video/edicoes/X.json (correções de palavras, tarja, cartões foto/número, zooms) → `node video/editar.mjs video/edicoes/X.json`.
   Legenda palavra a palavra + punch-in + fotos/números com mola + SFX sintetizados. Brutos e transcrições ficam em entregas/ (fora do git).
Não usar Action para baixar mídia de sites bloqueados (bloqueado por segurança). Mídia real vem do Thiago.

Leia este arquivo e depois `video/PROXIMOS-PASSOS.md` e `video/estudio/LEIAME.md`.
Branch de trabalho: `claude/mapa-politico-varjota`.

## Quem e o quê
- Thiago Costa (@falathiagoo, Kroma.mov, Varjota-CE). Fala pelo celular, muitas vezes por áudio transcrito
  (nomes chegam errados: "Divajosa" = Varjota, "Rede Otávio" = Reriutaba, "Rig Fields" = Higgsfield).
- Responder sempre em **português**, curto.
- Projeto Plenária CE: site de inteligência eleitoral (index.html + assets/js/app.js + data/ce/*.js) e uma série de
  vídeos verticais 1080×1920 em estilo escuro com partículas (video/*.html renderizados por video/gravar.mjs).

## Regras que não podem ser quebradas
- Repositório estava **privado** até 05/11/2026 (o Thiago tornou público para os links de vídeo). Trate como público: informação local de grupos políticos, apoios e lideranças fica só em arquivos ignorados
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

## Atualização 05/11/2026 (tarde)
- Série curta Parte 1 "Os números da Câmara" (7 cidades): `node video/curta.mjs ce/<cidade>` → narração (Action) →
  `video/mixar.py --trilha video/trilha-curta1-<cidade>.json` → `gravar.mjs --cena "cena-curta.html?d=curta-<cidade>.json"`.
  Fecha com o presidente da Câmara (data/fontes/presidentes-camara.json, com fonte). Santa Quitéria já elegeu Renato Catunda (2027–2028).
  Tom: sem partidos/grupos ("quem manda" é sensível: eleição da Mesa em curso).
- Tarja padrão do perfil (selo branco @PLENARIACE + título em tarja azul, Oswald): `node video/tarja.mjs entrada.mp4 "TÍTULO" saida.mp4 [--ate 7]`.
  Todo vídeo novo sai com tarja; nos de dados, só no gancho (capa no quadro de ~5 s).
- Publicação: Metricool (marca 6990789, fuso da conta Europe/Madrid) com TikTok e Instagram @plenariace conectados.
  Vídeo precisa de URL pública: branch `midia` (raw.githubusercontent.com/.../midia/...). TikTok exige `tiktokData.title`.
  Agenda final 05/11 (Fortaleza): SQ 14h30, Ipu 15h30, Cariré 16h30, Pires Ferreira 17h30 (TikTok+IG); Reriutaba 18h30 e Pacujá 19h30 (só IG,
  já estavam no TikTok sem tarja); Varjota já estava nos dois (versão com tarja ficou como rascunho no Metricool).
  Fluxo padrão: repositório público + branch `midia` = links prontos; o Metricool copia o vídeo ao agendar.
- Métricas do TikTok (set/2026): bombam confronto real + frase entre aspas, curtos (15–34 s), sessões de Câmara. Perfil ficou 45 dias parado.
- Rede da sessão bloqueia litterbox/catbox; .claude/settings.json tem a regra, mas falta liberar o domínio no ambiente.
- Próximos passos: Parte 2 "As surpresas"; vídeo por vereador (collab); clipes reais com tarja (pauta do Thiago); rotina diária de métricas (oferecida).
- Rotina diária de métricas: scheduled task `trig_01Tiwng3pbYxi1ezWKwx3jay`, 7h43 Fortaleza, dispara na sessão session_01HG11nb4K6fTzP98Tv79TRZ (só leitura no Metricool).
- Informação local (apoios, grupos): cópia no repositório PRIVADO thiagoinforiv-a11y/plenaria-local (subido pelo Thiago). Em sessão nova: varjota.local.js → data/ce/; lados.local.json e historico-varjota.local.json → video/. Nunca no repositório público.

## Atualização 10/11/2026 (leia isto primeiro numa sessão nova)
Economia: comece sessão nova por assunto; ao trocar, peça "atualiza o CONTINUAR.md". Desligue conectores sem uso
(vidIQ está sem créditos). A rotina diária de métricas (trigger trig_01Tiwng3pbYxi1ezWKwx3jay, 7h43) roda nesta sessão antiga;
se quiser, recriar com create_new_session_on_fire.

### Estudo de gastos (qualquer cidade do CE) — `scripts/gastos/` (README lá)
- `python3 scripts/gastos/estudo.py --cidade Ipu --orgao camara|prefeitura --de 2025 --ate 2026 [--cache]`
  → entregas/estudos/<cidade>-<orgao>-<de>-<ate>.xlsx (aba 1 "Pontos de atenção": fato, por que, ataque, defesa, o que pedir, base legal)
  + .json bruto + .painel.json + entregas/estudos/fornecedores.json (cruza CNPJ entre órgãos).
- Fontes: PNCP (pncp.gov.br), TCE-CE (api-dados-abertos.tce.ce.gov.br; Varjota=177, Pacujá=125; valores de empenho NÃO vêm na API),
  Siconfi (scripts/financas.py). Hosts liberados no ambiente: pncp.gov.br, cdn.tse.jus.br e os anteriores.
- Feitos: Câmara e Prefeitura de Varjota e de Pacujá (biênio 2025–2026). Câmara de Pacujá não publica no PNCP;
  Prefeitura de Pacujá quase não publica resultado (painel usa contratos do TCE-CE).
- Painel (artifact tipo Dashboard): https://claude.ai/artifact/SGou5Lr2gnb2VBds5xAyCQ — seletor Cidade + Prefeitura|Câmara;
  dados em datasets processos/itens/alertas/entradas (arquivos /_blob); página em files/index.html (fonte local entregas/camara/dash/v2/).
  Para nova cidade: rodar estudo.py, juntar os *.painel.json, subir os 4 arquivos e trocar as URLs dos datasets; incluir a cidade no <select>.
- Câmara de Varjota: repasse 2,60 mi (2024) → 3,88 mi (2025, +49%); 20 de 21 processos por dispensa; microfone de lapela R$ 2.009,89 (Alider, 2026);
  combustível contratado 13 mil L/ano para 1 carro e 1 motorista (Thiago confirmou). Valores pagos ao posto: pedir no portal/LAI.
  Portal da transparência da Câmara não foi encontrado (pedir o link ao Thiago).

### Empresa do Thiago (para licitações)
- Empresa do Thiago: ME, empresário individual, Varjota (CNPJ e cartão em entregas/oportunidades/, fora do git).
  21 CNAEs: 59.11-1-02 (principal), 59.11-1-01/99, 59.12-0-99, 74.20-0-01/02/03/04, 73.11-4-00, 73.19-0-02/03, 74.10-2-99,
  82.30-0-01, 90.01-9-02/06, 77.39-0-03/99, 77.11-0-00, 74.90-1-05.
- Busca de editais abertos: entregas/oportunidades/ (abertas.py UF..., filtro.py, planilha2.py) → oportunidades-licitacoes-abertas.xlsx
  e mapa-cnaes.png. Foco só Ceará. CENP: sem certificado não disputa publicidade; objeto social com eventos/promoção pode impedir
  certificação "full service" (sugestão: empresa separada só de agência). Faltam CNAEs: 73.19-0-04, 63.91-7-00, 62.01-5-02, 63.19-4-00, 59.20-1-00, 73.19-0-99.
- Conflito: se Thiago assumir cargo de comunicação num município, a empresa não pode contratar com ele (Lei 14.133, art. 14).

### Outros entregues (arquivos em entregas/, fora do git)
- Secretaria de Comunicação: entregas/secom/secom-proposta-e-recursos.pdf + secom-mapa.png (emendas Pix, Transferegov, PNAB, regras 2028).
- Natal Solidário de Varjota (ação privada de doação, sem palanque): entregas/natal/ (mapa, plano PDF, planilha de controle).
  2026 é ano eleitoral até 31/12: Prefeitura não pode distribuir bens (art. 73 §10).
- Vídeos de lideranças locais (raio-X por bairro, sem marca Plenária): entregas/cleuton/, Raony em entregas/ (detalhes só nos arquivos locais).

### Pautas em aberto (roteiros prontos na conversa de 10/11)
- Concurso da Câmara de Varjota: PL 34/2026 (19/10/2026, presidente Francisco Roberto Lira de Farias): 5 vagas + 4 reserva
  (aux. administrativo 2+1 médio; serv. gerais, motorista B, vigia 1+1 fund. incompleto), 40h, R$ 1.621. NÃO confirmado se já foi votado
  (Thiago vai checar: Câmara (88) 3639-1792). Gancho: "Tem vaga na Câmara… e não é pra vereador." Vídeo do presidente em
  entregas/midia/camara-presidente/ (transcrição .words.json).
- Forquilha 2028: Tenente Linha Dura, pré-candidato a vereador (Rádio Pioneira FM, Programa Livre, 28/10). Frase: "eu tenho meu nome".
  Áudio em entregas/midia/linha-dura/. Não confirmado: SBT / "alma sebosa" (não citar sem fonte). Duas versões de roteiro: A "Linha dura na
  farda… e agora na Câmara?" e B "O nome que já mexeu em Forquilha". Aguardando escolha do Thiago.
- @plenariace sem post desde 05/11; nada agendado. Métricas: CCJ 670 views (melhor), Tijuca única com comentários, Pacujá único com compartilhamentos.
