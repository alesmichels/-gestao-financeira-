# 0004 — Regras de divisão e acerto do casal

**Data:** 05/11/2026 · **Status:** aceita, revisar após o primeiro mês de uso

## Regras
- Cada categoria tem uma divisão padrão: **proporcional** à renda (peso em `cadastros.json`), **50/50** (carro) ou **individual**.
- A mensagem pode mudar a divisão: "só meu/minha" → individual; "50/50", "meio a meio" → 50/50.
- **Quem pagou** = titular da conta usada; se a conta não tem titular (Pix, Débito, Vale, Dinheiro), quem lançou.
- **Cartão de crédito sem titular** (conjunto) fica fora do acerto: a conta conjunta já é dividida.
- Acerto = o que cada um pagou − a parte que lhe cabia. Quem ficou negativo transfere para o outro.
- **Vale recebido** é lançado no dia 1º do mês de uso.

## Pontos a validar com o uso
- Pix e Débito de conta conjunta: hoje são atribuídos a quem lançou. Se vocês tiverem conta conjunta, criar contas separadas ("Pix conjunto") sem titular e tratá-las como o cartão conjunto.
