# Ideia futura — Planejamento de objetivos

**Registrada em:** 16/11/2026 · **Status:** ideia, sem implementação prevista ainda
**Layout proposto:** artboard "Planejamento · objetivos (proposta)" no canvas de design do projeto

## O que é
Uma página de planejamento onde o casal cadastra objetivos financeiros com prazo e regras, e o aplicativo mostra quanto falta e se o objetivo está no ritmo.

Exemplo: **Reforma da casa, 36 meses.**

## Campos do cadastro
- Objetivo (nome)
- Valor alvo
- Já guardado
- Prazo em meses e mês de início
- Onde o dinheiro fica guardado (conta ou investimento)
- Regras a seguir, uma por linha (ex.: "aportar todo dia 5", "não usar para outras despesas", "50% do 13º vai para este objetivo")

## O que o aplicativo calcula
- Prazo final e tipo de prazo (curto até 12 meses, médio até 24, longo acima disso)
- **Quanto falta** e **aporte necessário por mês** = falta ÷ meses restantes
- Situação: compara o guardado com o esperado se a meta fosse dividida em partes iguais no prazo → *no ritmo*, *adiantado* ou *atrasado* (e de quanto)
- Soma dos aportes necessários de todos os objetivos e **quanto isso pesa na renda do casal**

## Telas propostas
1. Resumo: objetivos ativos, falta total, aporte mensal total, % da renda
2. Formulário de novo objetivo com prévia dos cálculos
3. Tabela de objetivos ordenada pelo prazo, com a coluna **Falta** em destaque, barra de progresso, aporte por mês e situação
4. Detalhe do objetivo: "Faltam R$ X em N meses", barra com marca do esperado até hoje, regras com cumprida/pendente no mês, histórico de aportes

## Decisões em aberto
- O aporte para um objetivo entra como lançamento normal (sai do saldo do mês) ou fica separado?
- As regras são só uma lista para marcar à mão, ou o aplicativo verifica algumas sozinho (ex.: data do aporte)?
- Relação com a tabela de metas atual (curto, médio e longo prazo e reserva de emergência): substitui ou complementa?

## Encaixe no plano
Substitui/expande a parte de "Metas" prevista para a Fase 5.
