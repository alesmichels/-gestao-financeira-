# 0002 — Execução local, custo zero

**Data:** 29/10/2026 · **Status:** aceita

## Decisão
Tudo roda num computador de casa. O bot usa *long polling* (busca as mensagens no Telegram), então não há porta aberta nem túnel. O painel abre só em `localhost`.

## Consequências
- Se o computador desligar, as mensagens ficam guardadas no Telegram por até 24 horas e são processadas quando ele voltar.
- O bot só pode rodar em **um** computador por vez.
- Backup é responsabilidade nossa: `python -m app.backup` + cópia para HD externo.
