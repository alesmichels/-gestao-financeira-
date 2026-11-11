# Fase 1 — Lançamentos no aplicativo local (MVP)

**Início:** 05/11/2026 · **Ajuste de escopo:** 10/11/2026 (decisão 0005: só aplicativo local; bot desligado)

## Objetivo
Registrar gastos em segundos no aplicativo do computador e ver o mês, sem voltar à planilha.

## Critério de pronto
- [ ] Aplicativo instalado e abrindo pelo `abrir-aplicativo.bat`
- [ ] Configurações ajustadas (nomes, pesos, cartões)
- [ ] 90% das frases do lançamento rápido entendidas sem correção
- [ ] Um mês fechado no aplicativo, sem usar a planilha

## Entregue
- **05/11/2026:** banco SQLite com unidades de gestão, pessoas, contas, categorias, lançamentos e histórico; interpretador de frases; bot do Telegram; painel simples.
- **10/11/2026:** aplicativo com três páginas (Visão geral, Lançamentos, Configurações); lançamento rápido por frase com conferência antes de salvar; edição e cancelamento de lançamentos; cadastros editáveis no aplicativo; backup e download do banco; instalação com dois cliques; bot passou a ser opcional. 36 testes automáticos.

## Diário
| Data | O que aconteceu |
| --- | --- |
| 10/11/2026 | Tentativa de instalação: PowerShell em vez de cmd e Git ausente. Escopo reduzido para só o aplicativo local, com instalação por dois cliques e download por ZIP como alternativa ao Git. |
| 05/11/2026 | Código da Fase 1 criado e testado com dados simulados. |

## Fica para as próximas fases
- Bot do Telegram (pronto no código, ligar quando fizer sentido)
- Importação de extrato OFX/CSV
- Metas, investimentos e mercado
- Backup automático agendado
