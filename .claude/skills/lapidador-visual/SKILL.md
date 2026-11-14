---
name: lapidador-visual
description: Passa o acabamento "escuro premium" em qualquer tela que a gente gerou (painel, dashboard, página, sistema, protótipo) para tirar a "cara de IA". Use quando o Thiago pedir para melhorar o visual, deixar profissional/premium, ou antes de entregar um painel novo.
---

# Lapidador visual (escuro premium)

Objetivo: a tela parecer produto pronto, não protótipo. Mude só a camada visual; dados, textos e comportamento continuam iguais.

## 1. Antes de mexer
- Tire print da tela atual (Playwright, 390 px de largura para celular e 1440 px para computador) e guarde como "antes".
- Liste o que denuncia "cara de IA": cards todos iguais, cinza sobre cinza, gradiente roxo genérico, emoji como ícone, sombra pesada, borda arredondada demais, texto centralizado em tudo, números sem destaque, tabela crua.

## 2. Sistema de cores (tokens no `:root`)
- Fundo `#0b0f14`; painel `#11161d`; painel elevado `#161c25`; borda `rgba(255,255,255,.07)`.
- Texto `#e8edf2`; secundário `#93a1b0`; apagado `#5d6b79`.
- **Uma** cor de destaque por produto (ex.: Plenária `#ffd166` dourado; Super Choque `#ff3d1f`), usada só no que importa: número principal, botão primário, item selecionado.
- Estados: positivo `#3ddc97`, alerta `#ffb020`, problema `#ff5d5d` — sempre com texto, nunca só a cor.
- Se a página precisar de modo claro, defina os mesmos tokens em `@media (prefers-color-scheme: light)`.

## 3. Tipografia
- Uma família só (Montserrat ou a do projeto), pesos 400/600/800.
- Escala: 12 (rótulo, caixa alta, espaçamento .08em) · 14 (corpo) · 18 (título de card) · 28–40 (número de destaque, `font-variant-numeric: tabular-nums`).
- Alinhe à esquerda; centralize só número isolado em card.

## 4. Composição
- Grade de 8 px. Respiro generoso: padding 20–24 px no card, 16 px entre cards, 32–48 px entre seções.
- Raio 14–16 px no card, 10 px em botão/pílula. Borda fina em vez de sombra; sombra só no elemento flutuante.
- Hierarquia: 1 número herói por seção; o resto menor e mais apagado.
- Tabelas: cabeçalho em caixa alta apagado, linhas com 1 px de borda, números à direita, linha em foco com fundo levemente mais claro.
- Ícones de traço fino (SVG inline, 1,5 px), nada de emoji.

## 5. Gráficos
- Fundo transparente, grade quase invisível, só o eixo necessário, rótulo direto na barra/linha (sem legenda separada quando der).
- Cor de destaque só na série principal; as outras em cinza.

## 6. Movimento
- Transição 150–200 ms em hover/foco; números contam ao entrar (600 ms, uma vez). Nada piscando.

## 7. Celular
- Uma coluna abaixo de 640 px, alvo de toque ≥ 44 px, tabela larga vira lista de cards, sem rolagem horizontal da página.

## 8. Fechar
- Print "depois" nos mesmos tamanhos e mostre antes × depois lado a lado.
- Confira contraste do texto secundário sobre o painel (mínimo 4,5:1) e se nenhum número mudou.
