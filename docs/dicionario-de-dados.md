# Dicionário de dados

Banco: SQLite, arquivo `dados/financas.db`. Valores em **centavos** (inteiro). Datas em texto `AAAA-MM-DD`.

## unidades
Unidade de gestão: hoje "Casa"; no futuro "Propriedade".

| Campo | Tipo | Descrição |
| --- | --- | --- |
| id | inteiro | Identificador |
| nome | texto | Nome único |

## pessoas
| Campo | Tipo | Descrição |
| --- | --- | --- |
| id | inteiro | Identificador |
| unidade_id | inteiro | Unidade |
| nome | texto | Nome |
| telegram_id | inteiro | ID no Telegram; só quem tem ID é atendido pelo bot |
| peso_divisao | real | Peso na divisão proporcional (ex.: 0.58) |
| ativo | 0/1 | Inativos são ignorados |

## contas
Formas de pagamento e cartões.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| id | inteiro | Identificador |
| unidade_id | inteiro | Unidade |
| nome | texto | Ex.: "Crédito PicPay" |
| tipo | texto | credito, debito, pix, vale, dinheiro |
| titular_id | inteiro | Dono da conta; vazio = conjunta ou de quem lançar |
| dia_fechamento / dia_vencimento | inteiro | Só cartões de crédito |
| apelidos | JSON | Palavras reconhecidas nas mensagens |

## categorias
| Campo | Tipo | Descrição |
| --- | --- | --- |
| id | inteiro | Identificador |
| nome | texto | Ex.: "Mercado" |
| tipo | texto | saida ou entrada |
| regra_divisao | texto | proporcional, 50/50 ou individual (padrão da categoria) |
| apelidos | JSON | Palavras reconhecidas |

## lancamentos
| Campo | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| id | inteiro | Identificador | 42 |
| data | texto | Data do gasto | 2026-11-05 |
| tipo | texto | saida ou entrada | saida |
| valor_centavos | inteiro | Valor | 8750 (= R$ 87,50) |
| descricao | texto | Texto livre | Mercado |
| categoria_id / conta_id / autor_id | inteiro | Referências | |
| regra_divisao | texto | Divisão aplicada neste lançamento | proporcional |
| origem | texto | telegram, painel, importacao | telegram |
| mensagem_origem | texto | Mensagem original do chat | mercado 87,50 crédito picpay |
| status | texto | pendente, confirmado, cancelado (só confirmados entram nos totais) | confirmado |
| criado_em / atualizado_em | texto | Data e hora (UTC) | |

## historico
Toda criação, edição, confirmação, cancelamento ou desfazer.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| lancamento_id | inteiro | Lançamento afetado |
| acao | texto | criado, editado, confirmado, cancelado, desfeito |
| autor_id | inteiro | Quem fez (vazio = painel) |
| quando | texto | Data e hora (UTC) |
| antes / depois | JSON | Linha completa antes e depois |
