# Gestão Financeira

Assistente financeiro do casal: os gastos são lançados por mensagem num bot do Telegram, ficam num banco de dados no computador de casa e aparecem num painel no navegador.

- Roda **localmente**, sem mensalidade: o bot busca as mensagens no Telegram, sem precisar abrir porta no roteador.
- Os dados ficam num único arquivo (`dados/financas.db`), que nunca vai para o GitHub.
- Fase atual: **Fase 1** — lançamento por texto, confirmação, resumos no bot e painel simples. Veja `docs/fases/`.

## O que já funciona

| No bot do Telegram | No painel (computador) |
| --- | --- |
| Lançar gasto em texto livre: `mercado 87,50 crédito picpay` | Receitas, gastos e saldo do mês |
| Confirmar, corrigir (categoria, forma, data, divisão) ou cancelar | Gastos por categoria e forma de pagamento |
| Pergunta a forma de pagamento quando falta | Acerto do casal |
| Botões fixos: **Resumos**, **Lançar**, **Desfazer último** | Faturas abertas dos cartões |
| Resumos: hoje, semana, mês, faturas, acerto do casal | Lista de lançamentos, confirmar pendentes, lançar e cancelar |

## Instalação (Windows)

Pré-requisito: [Python 3.11 ou mais novo](https://www.python.org/downloads/) — na instalação, marque **"Add Python to PATH"**.

### 1. Baixar o código

```bat
git clone https://github.com/SEU-USUARIO/gestao-financeira.git
cd gestao-financeira
```

### 2. Instalar as dependências (uma vez)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Criar o bot no Telegram (uma vez)

1. No Telegram, abra uma conversa com **@BotFather** e mande `/newbot`.
2. Escolha um nome (ex.: *Finanças da Casa*) e um usuário terminado em `bot` (ex.: `financas_casa_alexandre_bot`).
3. O BotFather responde com um **token** (algo como `123456:ABC-...`). Guarde: ele é a senha do bot.
4. Ainda no BotFather: `/setprivacy` → escolha o bot → **Disable** (para o bot ler as mensagens do grupo).
5. `/setjoingroups` → escolha o bot → **Disable** depois de adicioná-lo ao grupo do casal (impede que outros o coloquem em grupos).

### 4. Configurar

```bat
copy .env.example .env
notepad .env
```

Cole o token em `TELEGRAM_TOKEN=`. Salve.

```bat
python -m app.cadastros
```

Isso cria `config/cadastros.json`. Abra e ajuste: nome da parceira, peso de cada um na divisão (ex.: 0.58 e 0.42), cartões com dia de fechamento e vencimento, e os apelidos que vocês usam.

### 5. Descobrir os IDs do Telegram

```bat
python -m app.bot
```

Com o bot rodando, cada um manda `/id` para o bot no Telegram. Coloque os números em `telegram_id` no `config/cadastros.json`. Depois:

1. Crie um grupo com vocês dois e adicione o bot.
2. Mande `/id` **no grupo**: o "ID deste chat" (número negativo) vai em `GRUPO_AUTORIZADO=` no `.env`.
3. Pare o bot (Ctrl+C), rode `python -m app.cadastros` de novo e inicie o bot outra vez.

Pronto: mandem `/start` no grupo para aparecerem os botões.

## Uso diário

- **Bot:** dois cliques em `iniciar-bot.bat` (precisa ficar aberto).
- **Painel:** dois cliques em `iniciar-painel.bat` e abra http://localhost:8501.
- **Backup:** `python -m app.backup` cria uma cópia em `backups/`. Copie essa pasta para um HD externo de vez em quando.

### Como escrever os lançamentos

```
mercado 87,50 crédito picpay
farmácia 42,90 pix ontem
gasolina 180 cartão conjunto        → categoria Carro, divisão 50/50
almoço 36 vale 03/11
roupa 120 débito só meu             → fica fora da divisão
recebi salário 5.200
vale caiu 640                       → entrada no dia 1º do mês
```

O bot entende pelos **apelidos** do `config/cadastros.json`. Se uma palavra que vocês usam não for reconhecida, acrescente-a lá e rode `python -m app.cadastros`.

## Mudar para outro computador

1. Pare o bot no computador antigo (**o bot só pode rodar em um lugar por vez**).
2. No novo: passos 1 e 2 da instalação.
3. Copie do antigo para o novo: `.env`, `config/cadastros.json` e a pasta `dados/`.
4. Inicie o bot no novo.

## Testes

```bat
python -m pytest
```

## Estrutura

```
app/
  bot.py        conexão com o Telegram
  servico.py    regras da conversa (testável sem Telegram)
  parser.py     interpreta as mensagens (regras, sem IA)
  resumos.py    totais, faturas, acerto do casal
  db.py         banco de dados SQLite
  painel.py     painel no navegador
  cadastros.py  aplica config/cadastros.json no banco
  backup.py     cópia de segurança
config/         cadastros (o seu fica fora do Git)
docs/           decisões, diário de cada fase, dicionário de dados
tests/          testes automáticos
```
