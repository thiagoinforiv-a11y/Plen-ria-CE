# Estudo de gastos públicos (Câmara ou Prefeitura, qualquer cidade do Ceará)

Monta uma planilha de estudo com tudo o que o órgão comprou e contratou, quem ganhou, por quanto, e uma aba de **pontos de atenção**. Cada ponto vem com:

- **o fato**, com os números;
- **por que chama atenção**;
- **a linha de ataque**, ou seja, a pergunta que um vereador, a imprensa ou o Ministério Público faria;
- **a defesa provável** do gestor;
- **o que pedir pela Lei de Acesso à Informação**;
- **a base legal**.

> Alerta é indício para pedir documento, não prova de irregularidade. Material de estudo interno: confirme com os documentos antes de qualquer publicação.

## Como rodar

```bash
python3 scripts/gastos/estudo.py --cidade Varjota --orgao camara --de 2025 --ate 2026
python3 scripts/gastos/estudo.py --cidade Pacujá --orgao prefeitura --de 2025 --ate 2026
python3 scripts/gastos/estudo.py --cidade "Santa Quitéria" --orgao camara --cache   # reaproveita o que já baixou
```

A saída fica em `entregas/estudos/` (fora do git):

- `<cidade>-<orgao>-<de>-<ate>.xlsx`: a planilha;
- `<cidade>-<orgao>-<de>-<ate>.json`: os dados brutos, reaproveitados com `--cache`;
- `fornecedores.json`: índice de fornecedores de todos os estudos já feitos. Ele permite apontar quando o **mesmo CNPJ aparece em outra cidade**.

## De onde vêm os dados

| Fonte | O que traz | Host |
|---|---|---|
| PNCP (Portal Nacional de Contratações Públicas) | licitações, dispensas, contratos, itens, preço unitário estimado e pago, vencedor | pncp.gov.br |
| TCE-CE (dados abertos) | órgãos e CNPJs do município, contratos com nome do contratado (usado quando o órgão não publica no PNCP) | api-dados-abertos.tce.ce.gov.br |
| Tesouro Nacional (Siconfi) | repasse à Câmara (função Legislativa), receita, FPM | apidatalake.tesouro.gov.br (via `scripts/financas.py`) |

A cidade é encontrada pelo nome no TCE-CE, e os CNPJs da Câmara e da Prefeitura (com fundos de Saúde, Educação e Assistência) saem automaticamente.

## Pontos de atenção automáticos (`alertas.py`)

| Ponto | Regra |
|---|---|
| Órgão não publica no PNCP | nenhuma contratação no PNCP, mas há contratos no TCE-CE |
| Quase tudo sem licitação | 50% ou mais de dispensa/inexigibilidade |
| Valor colado no teto da dispensa | dispensa entre 85% e 100% do limite do ano (limites de 2023 a 2025 no código; anos seguintes: faixa de R$ 52 mil a R$ 70 mil, com aviso para conferir o decreto) |
| Possível fracionamento | 2 ou mais dispensas da mesma categoria no ano, somando mais que o limite |
| Pagou praticamente o preço estimado | 3 ou mais processos fechados a menos de 1% do estimado |
| Item pago acima do estimado | preço unitário 5% ou mais acima da estimativa |
| Fornecedor concentra o gasto | um fornecedor com 15% ou mais do total |
| Muito dinheiro em assessorias | 30% ou mais do valor em assessoria, consultoria e jurídico |
| Mesmo serviço contratado mais de uma vez | mesmo fornecedor com objetos parecidos |
| Contratações concentradas em dezembro | 3 ou mais processos entre 15 e 31/12 |
| Contrato alto com MEI ou empresa individual | 30 mil ou mais para nome com CPF, ME ou sociedade individual |
| Mesmo fornecedor em outra cidade | CNPJ presente em outro estudo da pasta |
| Combustível | litros contratados e quilômetros equivalentes |
| Repasse à Câmara cresceu muito | alta de 15% ou mais no repasse |

Para mudar textos ou regras, edite `TEXTOS` e `gerar()` em `alertas.py`. Para incluir o limite de dispensa de um ano novo, acrescente o ano em `LIMITES`, com os valores do decreto daquele ano.

## Limitações

- A API do TCE-CE não traz o **valor** dos empenhos e pagamentos, só a data e o credor. Para saber quanto foi pago de fato (por exemplo, litros abastecidos), é preciso o portal da transparência do órgão ou um pedido pela Lei de Acesso.
- No PNCP, a quantidade de uma ata ou contrato é o **máximo** previsto, não o consumido.
- Folha de pagamento e diárias não entram.
