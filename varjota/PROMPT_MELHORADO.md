# Prompt melhorado: estudo político-eleitoral municipal

> Copie o texto abaixo e troque o que está entre `[colchetes]`. Ele foi escrito para tirar o máximo de informação dos dados oficiais e deixar separado o que é **fato** do que é **interpretação**.

---

**Contexto:** quero um estudo político-eleitoral completo do município de **[VARJOTA – CE]** (código TSE **[98574]**, zona **[65]**), cobrindo as eleições municipais de **[2020 e 2024]** e as eleições gerais de **[2022 e 2026]**, com projeção para **[2028]**. O estudo serve para planejamento político, por isso preciso de números exatos e também das leituras de bastidor ("entrelinhas").

**Fontes obrigatórias:** use só os dados abertos do TSE (dadosabertos.tse.jus.br / cdn.tse.jus.br). Cite o arquivo de origem de cada número. Use estes conjuntos:
- `votacao_candidato_munzona`, `votacao_partido_munzona`, `detalhe_votacao_munzona` (resultado, legenda, brancos, nulos, abstenção)
- `votacao_secao` (resultado por seção e por local de votação)
- `consulta_cand` (perfil dos candidatos: gênero, idade, cor, escolaridade, ocupação, situação). Ligue os candidatos de anos diferentes pelo título de eleitor.
- `bem_candidato` (patrimônio declarado) e, se possível, `prestacao_de_contas` (receitas, despesas e custo por voto)
- `perfil_eleitorado` (idade, gênero e escolaridade do eleitorado)
- Se puder, inclua também os filiados por partido no município.

**Quero, nesta ordem:**

1. **Resumo executivo** em 10 linhas, com os números que mais importam.
2. **Eleitorado:**
   - aptos, comparecimento, abstenção, brancos e nulos em cada eleição
   - tendência do cadastro
   - pirâmide etária e escolaridade, comparando os anos
3. **Prefeito:**
   - votos, percentual e margem
   - composição das coligações
   - troca de vice
   - votos ganhos e perdidos por cada grupo
4. **Câmara Municipal:**
   - quociente eleitoral calculado e explicado passo a passo
   - quociente partidário
   - cada rodada de sobras pelas maiores médias, com as barreiras de 80% e de 10%/20%
   - quantos votos faltaram para a última cadeira mudar de dono
   - votos por cadeira de cada lista
   - menos votado eleito × mais votado não eleito
   - concentração de votos dentro de cada lista
   - votos de legenda
5. **Candidatos:**
   - quantidade por partido
   - mulheres candidatas e eleitas
   - renovação: quem tentou a reeleição, quem foi reeleito e quem desistiu
   - patrimônio declarado
6. **Migrações partidárias:** tabela de quem trocou de partido ou de grupo entre as eleições, e o resultado de cada um.
7. **Geografia do voto:**
   - resultado por local de votação, separando zona urbana e rural
   - onde o vencedor mais cresceu e menos cresceu
   - redutos de cada grupo
8. **Contexto estadual e federal:** voto em presidente, governador, senador e deputados, para identificar quais lideranças estaduais têm voto no município e se a máquina local transfere votos.
9. **Entrelinhas:** pelo menos 10 achados não óbvios, cada um marcado como **[FATO]** (número) ou **[LEITURA/HIPÓTESE]** (interpretação), com o número que sustenta cada um.
10. **Projeção para a eleição seguinte:**
    - aptos, comparecimento e válidos em 3 cenários (baixo, central e alto)
    - quociente eleitoral e barreiras projetados
    - número provável de listas e candidatos (teto: vagas + 1 por partido)
    - simulação de cadeiras em pelo menos 3 cenários
    - cenários para prefeito
    - variáveis-chave a acompanhar
11. **Limitações** e **próximos passos** (quais dados ainda faltam).

**Formato de entrega:**
- Relatório em Markdown com tabelas e gráficos em PNG 16:9.
- Arquivo `metricas.json` com todos os números.
- Script reproduzível.
- **Vídeo narrado em português** (16:9, 1080p), sem limite de duração, que percorra o estudo na ordem acima, com um gráfico ou cartão de texto por tema e a narração explicando o que o número significa.

**Regras:**
- Não invente parentescos, apoios ou acordos. Se for hipótese, diga que é hipótese.
- Mostre as contas: quociente, sobras e margens.
- Use linguagem clara, para quem não é especialista em direito eleitoral.
- Não chute números que não estão nos dados.
