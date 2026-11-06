"""Bot do Telegram (long polling: não precisa de endereço público nem porta aberta).

Uso:  python -m app.bot
"""
import logging

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton,
                      ReplyKeyboardMarkup, Update)
from telegram.constants import ChatType, ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from app import config, db, servico

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # não registrar URLs com o token
log = logging.getLogger("bot")

CON = None
UID = None
TECLADO = ReplyKeyboardMarkup([[KeyboardButton(t) for t in linha] for linha in servico.TECLADO_FIXO],
                              resize_keyboard=True, is_persistent=True)


def _autorizado(update: Update):
    """Devolve a pessoa cadastrada, ou None se a mensagem deve ser ignorada."""
    usuario = update.effective_user
    chat = update.effective_chat
    if usuario is None or chat is None:
        return None
    pessoa = db.pessoa_por_telegram(CON, usuario.id)
    if pessoa is None:
        log.warning("Ignorado: usuário %s não cadastrado (chat %s)", usuario.id, chat.id)
        return None
    if chat.type != ChatType.PRIVATE and str(chat.id) != config.GRUPO_AUTORIZADO:
        log.warning("Ignorado: grupo %s não autorizado", chat.id)
        return None
    return pessoa


def _teclado_inline(botoes):
    if not botoes:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton(rotulo, callback_data=dado) for rotulo, dado in linha]
                                 for linha in botoes])


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra os IDs para configurar. Responde a qualquer pessoa, mas não revela dados."""
    u, c = update.effective_user, update.effective_chat
    await update.message.reply_text(
        f"Seu ID do Telegram: <code>{u.id}</code>\nID deste chat: <code>{c.id}</code>",
        parse_mode=ParseMode.HTML)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pessoa = _autorizado(update)
    if pessoa is None:
        await update.message.reply_text("Olá! Este bot é privado. Mande /id e passe o número para quem administra.")
        return
    await update.message.reply_text(f"Olá, {pessoa['nome']}!\n\n{servico.AJUDA}",
                                    parse_mode=ParseMode.HTML, reply_markup=TECLADO)


async def ao_receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pessoa = _autorizado(update)
    if pessoa is None or update.message is None:
        return
    em_grupo = update.effective_chat.type != ChatType.PRIVATE
    resp = servico.processar_texto(CON, UID, pessoa, update.message.text, config.hoje(), em_grupo)
    if resp is None:
        return
    await update.message.reply_text(resp.texto, parse_mode=ParseMode.HTML,
                                    reply_markup=_teclado_inline(resp.botoes) or TECLADO)


async def ao_clicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    pessoa = _autorizado(update)
    if pessoa is None:
        await q.answer("Sem permissão.")
        return
    await q.answer()
    try:
        resp = servico.processar_callback(CON, UID, pessoa, q.data, config.hoje())
    except Exception:
        log.exception("Erro ao processar botão %s", q.data)
        await q.message.reply_text("Deu um erro aqui. O lançamento não foi alterado; tente de novo.")
        return
    if resp.editar:
        await q.edit_message_text(resp.texto, parse_mode=ParseMode.HTML, reply_markup=_teclado_inline(resp.botoes))
    else:
        await q.message.reply_text(resp.texto, parse_mode=ParseMode.HTML, reply_markup=_teclado_inline(resp.botoes))


async def ao_errar(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Erro não tratado", exc_info=context.error)


def main():
    global CON, UID
    if not config.TELEGRAM_TOKEN or "coloque" in config.TELEGRAM_TOKEN:
        raise SystemExit("Falta o TELEGRAM_TOKEN no arquivo .env (veja o README).")
    CON = db.conectar()
    UID = db.unidade_padrao(CON)
    if not config.GRUPO_AUTORIZADO:
        log.warning("GRUPO_AUTORIZADO vazio: o bot só responde em conversa direta até você preencher.")
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler(["start", "ajuda"], cmd_start))
    app.add_handler(CallbackQueryHandler(ao_clicar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ao_receber_texto))
    app.add_error_handler(ao_errar)
    log.info("Bot rodando. Banco: %s. Ctrl+C para parar.", config.DB_PATH)
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
