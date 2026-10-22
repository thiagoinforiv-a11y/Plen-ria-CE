# Plenária CE — Mapa político por município

Página de análise eleitoral (começando por **Varjota/CE**) com apresentação animada de abertura
(GSAP, 1920×1080, ~15s) e um painel para quem entende de política:

- **Mais votados** por cargo e eleição, com limiar ajustável de "votação relevante" (% dos válidos).
- **Bairros**: quem venceu cada bairro, top 5 por bairro, placar de bairros vencidos e mapa de calor candidato × bairro.
- **Mapa** dos locais de votação (coordenadas do TSE), colorido pelo vencedor ou pela força de um candidato.
- **Seções**: tabela completa, filtro por bairro, votos de um candidato seção a seção e comparação de até 4 seções.
- **Comparar** até 4 candidatos por bairro ou por local, em votos ou % dos válidos.
- **Perfil** do candidato: foto, ficha, votos na cidade, posição, bairros vencidos, melhores seções,
  votação no estado e peso da cidade na votação dele, e **histórico na cidade** em outras eleições.

## Abrir

Abra `index.html` no navegador (funciona direto do arquivo; o GSAP está em `assets/vendor`).
A apresentação roda sozinha na primeira visita de cada dispositivo; depois, pelo botão **▶ Apresentação**
ou com `index.html?intro`.

## Dados

Tudo vem dos dados abertos do TSE. Nada é estimado ou inventado.

| Eleição | Nível | Fonte |
|---|---|---|
| 2012, 2016, 2020 (prefeito e vereador) | totais do município | TSE via espelho Base dos Dados |
| Eleitorado/comparecimento 2010–2022 | totais do município | TSE via espelho Base dos Dados |
| Deputados (2014, 2018, 2022, 2026…) | **seção, local e bairro** | TSE — `cdn.tse.jus.br` (rodar o importador abaixo) |

Para gerar o detalhe por seção/bairro dos deputados (precisa de acesso a `cdn.tse.jus.br`):

```bash
python3 scripts/plenaria.py tse --municipio Varjota --ano 2022 --ano 2018 --ano 2014 --baixar
```

O script baixa `votacao_secao`, `eleitorado_local_votacao` (bairro e coordenadas),
`consulta_cand` (ficha), `votacao_candidato_munzona` (votação no estado) e as fotos oficiais
(`foto_cand<ano>_CE_div.zip`; ficam em `fotos/`). Ele também liga a mesma pessoa entre eleições
(por hashes de CPF/título/nome+nascimento; CPF e título não vão para o arquivo publicado).

Base histórica (totais municipais):

```bash
python3 scripts/plenaria.py seed --municipio Varjota --cd-ibge 2314003
```

## Estrutura (pronta para outras cidades e login)

```
index.html              intro + painel
assets/css/app.css      tema (troque a cor da apresentação em --accent)
assets/js/intro.js      timeline GSAP da abertura
assets/js/app.js        painel
data/cidades.js         registro das cidades disponíveis (seletor de cidade)
data/ce/<cidade>.js     dados de cada cidade, gerados pelo script
scripts/plenaria.py     importador (seed + TSE)
```

Para outra cidade do Ceará, rode os mesmos comandos com `--municipio <Nome>` (e `--cd-ibge` no seed).
O login entra antes de `App.loadCity()` em `assets/js/app.js`; com ele, os arquivos de `data/`
devem passar a ser servidos por trás da autenticação.
