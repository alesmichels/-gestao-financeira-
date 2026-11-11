# Bot do Telegram (opcional, desligado por enquanto)

O código do bot está pronto (`app/bot.py` e `app/servico.py`) e usa o mesmo banco do aplicativo. Ele fica desligado até decidirmos ligar; veja a decisão 0005.

## Para ligar no futuro

1. Na pasta do aplicativo, abra o Prompt e instale:
   ```bat
   .venv\Scripts\activate
   pip install -r requirements-bot.txt
   ```
2. No Telegram, fale com **@BotFather**: `/newbot` → escolha nome e usuário → guarde o **token**. Depois `/setprivacy` → **Disable**.
3. Configure:
   ```bat
   copy .env.example .env
   notepad .env
   ```
   Cole o token em `TELEGRAM_TOKEN=`.
4. Rode `python -m app.bot`. No Telegram, mande `/id` ao bot e anote o número. Coloque-o na coluna **ID do Telegram** da pessoa, em Configurações no aplicativo, e salve.
5. Reinicie o bot (Ctrl+C e `python -m app.bot`) e mande `mercado 10 pix`.
6. Grupo do casal: crie o grupo, adicione o bot, mande `/id` no grupo, coloque o número (negativo) em `GRUPO_AUTORIZADO=` no `.env` e reinicie o bot. No @BotFather, `/setjoingroups` → **Disable**.

O bot e o aplicativo podem rodar ao mesmo tempo. O bot só pode rodar em **um** computador por vez.
