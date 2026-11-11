# 0005 — Fase 1 só com o aplicativo local; bot desligado

**Data:** 10/11/2026 · **Status:** aceita

## Contexto
A instalação do bot (token, IDs, grupo, terminal aberto) pesou na hora de começar a usar. A prioridade é ter os lançamentos funcionando no dia a dia.

## Decisão
- A Fase 1 entrega só o **aplicativo no navegador**, rodando no computador.
- O **lançamento rápido** por frase ("mercado 87,50 crédito picpay") fica dentro do aplicativo, usando o mesmo interpretador que o bot usaria.
- Cadastros (pessoas, cartões, categorias, apelidos) passam a ser editados **no próprio aplicativo**, não mais no arquivo JSON.
- Instalação e abertura com dois cliques (`abrir-aplicativo.bat`), sem `.env` obrigatório.
- O bot continua no código, com dependência separada (`requirements-bot.txt`), pronto para ser ligado depois (`docs/bot-telegram.md`).

## Consequências
- Os lançamentos só podem ser feitos no computador onde o aplicativo roda.
- Os dados são gravados a cada clique em Salvar, no arquivo `dados\financas.db`; fechar o navegador não apaga nada.
- Quando o bot for ligado, ele grava no mesmo banco: nada do que foi lançado no aplicativo se perde.
