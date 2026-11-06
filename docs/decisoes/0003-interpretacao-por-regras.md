# 0003 — Interpretar mensagens por regras (sem IA) na Fase 1

**Data:** 05/11/2026 · **Status:** aceita

## Decisão
A Fase 1 interpreta as mensagens com regras simples (`app/parser.py`) e apelidos configuráveis (`config/cadastros.json`). Toda mensagem vira um lançamento **pendente** e só conta nos totais depois de confirmada.

## Por quê
- Rápido, previsível, sem custo e sem exigir hardware para IA.
- O formato que vocês usam no dia a dia é curto e repetitivo ("mercado 87,50 crédito picpay").
- A confirmação obrigatória pega os erros.

## Próximo passo
Medir a taxa de acerto com mensagens reais (meta da Fase 1: 90%). O modelo local (Ollama) entra depois, só para as mensagens que as regras não entenderem.
