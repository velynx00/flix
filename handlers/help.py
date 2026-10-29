import io
import logging

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from keyboards.menus import help_menu, back_btn
from utils.text import sc
# Import the shared helper — NOT re-implemented here
from handlers.start import _send_new_banner

logger = logging.getLogger(__name__)


async def cb_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>❓ {sc('nox syndicate help center')}</b>\n\n"
        f"{sc('welcome to the help menu. choose a guide below to learn.')}\n\n"
        f"<b>⧩ {sc('available guides')} ⧩</b>"
    )
    await _send_new_banner(q, text, "HELP CENTER", help_menu())


async def cb_help_api(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>🔑 {sc('how to get api id & hash')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1.</b> {sc('go to')} <code>my.telegram.org</code>\n"
        f"<b>2.</b> {sc('login with your phone number.')}\n"
        f"<b>3.</b> {sc('click on')} <b>API development tools</b>.\n"
        f"<b>4.</b> {sc('create a new app (name can be anything).')}\n"
        f"<b>5.</b> {sc('copy your')} <b>App api_id</b> {sc('and')} <b>App api_hash</b>.\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"⚠️ <i>{sc('keep these codes safe. do not share them.')}</i>"
    )
    await _send_new_banner(q, text, "API GENERATION", back_btn())


async def cb_help_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>📥 {sc('scraping guide')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1.</b> {sc('press')} <b>{sc('scrape')}</b> {sc('button.')}\n"
        f"<b>2.</b> {sc('send the group link')} (e.g. <code>@publicgroup</code>).\n"
        f"<b>3.</b> {sc('enter the limit')} (1–50).\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<i>{sc('note: if no api is added, ask owner.')}</i>"
    )
    await _send_new_banner(q, text, "SCRAPER ENGINE", back_btn())


async def cb_help_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>📤 {sc('adding guide')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1.</b> {sc('press')} <b>{sc('add')}</b> {sc('button.')}\n"
        f"<b>2.</b> {sc('send the source group link.')}\n"
        f"<b>3.</b> {sc('enter limit')} (1–50).\n"
        f"<b>4.</b> {sc('send the private group link')} ({sc('you must be admin')}).\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"⚠️ <i>{sc('bot adds members with a 10sec delay to avoid ban.')}</i>"
    )
    await _send_new_banner(q, text, "ADDER ENGINE", back_btn())


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(cb_help_menu,   pattern="^menu:help$"))
    app.add_handler(CallbackQueryHandler(cb_help_api,    pattern="^help:api$"))
    app.add_handler(CallbackQueryHandler(cb_help_scrape, pattern="^help:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_help_add,    pattern="^help:add$"))
