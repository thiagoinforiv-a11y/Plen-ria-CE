# Plenária CE — Mapa político por município

Página de análise eleitoral (começando por **Varjota/CE**) com apresentação animada de abertura
(GSAP, 1920×1080, ~15s) e um painel para quem entende de política:

- **Mais votados** por cargo e eleição, com limiar ajustável de "votação relevante" (% dos válidos).
- **Bairros**: quem venceu cada bairro, top 5 por bairro, placar de bairros vencidos e mapa de calor candidato × bairro.
- **Ficha da cidade**: quem manda, grupos políticos e deputados ligados, leitura, pontos a acompanhar e linha do tempo com selo de confiança por item.
- **Mapa das forças** (Leaflet): balões por bairro/distrito com a foto de quem lidera; ao tocar, sobem as 3 maiores forças.
  Dá para entrar no bairro → local de votação → seção, alternar entre deputados (2026) e vereadores/prefeito (2024)
  e fixar até 3 candidatos para acompanhar em todo o mapa.
- **Seções**: tabela completa, filtro por bairro, votos de um candidato seção a seção e comparação de até 4 seções.
- **Trajetória e comparação**: até 4 nomes (vereadores, prefeitos ou deputados) eleição a eleição desde 2000,
  com partido de cada ano, votos, % dos válidos, posição, resultado e tendência (crescimento/declínio).
- **Comparar** até 4 candidatos por bairro ou por local, em votos ou % dos válidos.
- **Raio-X de força**: índice por bairro e local (% na área ÷ % na cidade × 100), com "onde é forte",
  "onde é fraco", "onde pode crescer" (votos que faltam para a média dele) e concentração do voto;
  no mapa, "Raio-X de" pinta os balões pela força do candidato escolhido.
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
| 2000 a 2020 (prefeito e vereador) | totais do município | TSE via espelho Base dos Dados |
| Eleitorado/comparecimento 2000–2022 | totais do município | TSE via espelho Base dos Dados |
| Deputados (2014, 2018, 2022, 2026…) | **seção, local e bairro** | TSE — `cdn.tse.jus.br` (rodar o importador abaixo) |

Para gerar o detalhe por seção/bairro dos deputados (precisa de acesso a `cdn.tse.jus.br`):

```bash
python3 scripts/plenaria.py tse --municipio Varjota --ano 2026 --ano 2024 --ano 2022 --baixar
```

O script baixa `votacao_secao`, `eleitorado_local_votacao` (bairro e coordenadas),
`consulta_cand` (ficha), `votacao_candidato_munzona` (votação no estado) e as fotos oficiais
(`foto_cand<ano>_CE_div.zip`; ficam em `fotos/`). Ele também liga a mesma pessoa entre eleições
(por hashes de CPF/título/nome+nascimento; CPF e título não vão para o arquivo publicado).

Base histórica (totais municipais):

```bash
python3 scripts/plenaria.py seed --municipio Varjota --cd-ibge 2313955 --desde 2000
```

## Informação local (fora do GitHub)

`data/<uf>/<cidade>.local.js` guarda o que é conhecimento seu (quem apoiou quem, leituras).
Está no `.gitignore`: guarde uma cópia e coloque na pasta ao lado de `<cidade>.ficha.js`.

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
