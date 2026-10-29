from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from keyboards.menus import scrape_menu, add_menu, back_btn
from utils.text import sc
from handlers.start import safe_edit


async def cb_menu_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>⟢ {sc('scraper engine')} ⟢</b>\n\n"
        f"{sc('extract members from any telegram group.')}\n\n"
        f"<b>{sc('limit')}: 50</b> {sc('members per session (free)')}.\n"
        f"{sc('press start scrape to begin.')}"
    )
    await safe_edit(q, text, scrape_menu())


async def cb_menu_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>✦ {sc('adder engine')} ✦</b>\n\n"
        f"{sc('inject members into your private group.')}\n\n"
        f"<b>{sc('limit')}: 50</b> {sc('members per session (free)')}.\n"
        f"{sc('press start adding to begin.')}"
    )
    await safe_edit(q, text, add_menu())


async def cb_scrape_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    context.user_data["action"]      = "scrape"
    context.user_data["waiting_for"] = "target"
    text = (
        f"<b>{sc('start scrape')}</b>\n\n"
        f"<b>{sc('send the group link or username')}:</b>\n"
        f"<i>Example: @publicgroup or https://t.me/publicgroup</i>"
    )
    await safe_edit(q, text, back_btn())


async def cb_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    context.user_data["action"]      = "add"
    context.user_data["waiting_for"] = "target"
    text = (
        f"<b>{sc('start add')}</b>\n\n"
        f"<b>{sc('send the source group link')}:</b>\n"
        f"<i>Example: @sourcegroup</i>"
    )
    await safe_edit(q, text, back_btn())


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(cb_menu_scrape,  pattern="^menu:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_menu_add,     pattern="^menu:add$"))
    app.add_handler(CallbackQueryHandler(cb_scrape_start, pattern="^scrape:start$"))
    app.add_handler(CallbackQueryHandler(cb_add_start,    pattern="^add:start$"))
