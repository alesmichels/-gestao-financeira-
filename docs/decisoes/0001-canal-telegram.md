# 0001 — Canal de conversa: Telegram

**Data:** 30/10/2026 · **Status:** aceita

## Contexto
O registro de gastos precisa ser feito por chat, de preferência num grupo do casal, sem custo e com o sistema rodando em casa.

## Decisão
Usar um bot do Telegram, num grupo do casal e também em conversa direta.

## Alternativas descartadas
- **WhatsApp, API oficial:** grupos só para empresas com selo verificado (até 8 pessoas); exige endereço público 24 h; cobra respostas acima de 1.000/mês e qualquer mensagem iniciada pelo bot; proíbe chatbots de uso geral desde 15/01/2026.
- **WhatsApp, API não oficial:** funciona em grupo, mas viola os termos e o número pode ser banido.

## Consequências
- Os dois precisam usar o Telegram.
- O bot fica isolado em `app/bot.py`; a lógica da conversa está em `app/servico.py`. Um canal novo (ex.: WhatsApp para a propriedade) seria outro adaptador usando o mesmo `servico.py`.
