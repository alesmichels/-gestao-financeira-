# Fase 1 — Lançamento por texto (MVP)

**Início:** 05/11/2026

## Objetivo
Lançar gastos pelo Telegram em segundos e ver o mês no painel, sem voltar à planilha.

## Critério de pronto
- [ ] 90% das mensagens reais viram lançamentos corretos sem correção
- [ ] Uma semana de uso pelos dois sem voltar à planilha

## Entregue em 05/11/2026
- Banco SQLite com unidades de gestão (Casa; Propriedade no futuro), pessoas, contas, categorias, lançamentos e histórico de alterações.
- Interpretação de mensagens por regras e apelidos configuráveis.
- Bot: confirmar / corrigir / cancelar, pergunta a forma de pagamento quando falta, botões fixos (Resumos, Lançar, Desfazer último), menu de resumos (hoje, semana, mês, faturas, acerto do casal).
- Segurança: responde só aos IDs cadastrados e ao grupo autorizado; segredos no `.env`; dados fora do Git.
- Painel Streamlit: visão geral do mês, pendentes, faturas, acerto, lista e lançamento manual.
- Backup manual (`python -m app.backup`).
- 30 testes automáticos (`python -m pytest`).

## Diário
| Data | O que aconteceu |
| --- | --- |
| 05/11/2026 | Código da Fase 1 criado e testado com dados simulados. Próximo: instalar, criar o bot e usar de verdade. |

## Ainda não faz (fases seguintes)
- Leitura de foto de comprovante e áudio (Fase 6)
- IA local para mensagens fora do padrão
- Metas, investimentos e mercado (Fases 4 e 5)
- Resumo semanal automático e backup agendado (Fase 5)
- Importação de extrato OFX/CSV
