import logging

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import config
from keyboards.menus import admin_panel
from utils.text import sc
from utils.banner import generate_scary_dp
from handlers.start import safe_edit

logger = logging.getLogger(__name__)

_ADMIN_TEXT = (
    f"<b>🛡 {sc('nox syndicate admin panel')}</b>\n"
    f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
    f"{sc('welcome to the elite control center.')}\n"
    f"{sc('select an action below.')}"
)


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != config.OWNER_ID:
        return
    await update.message.reply_html(_ADMIN_TEXT, reply_markup=admin_panel())


async def cb_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID:
        await q.answer("⛔ Unauthorized", show_alert=True)
        return
    await safe_edit(q, _ADMIN_TEXT, admin_panel())


async def cb_admin_addapi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID:
        return
    context.user_data["waiting_for"] = "api_id"
    text = (
        f"<b>{sc('add session')}</b>\n\n"
        f"<b>{sc('step 1/3: enter api id')}:</b>\n"
        f"<i>Get it from my.telegram.org</i>"
    )
    await safe_edit(q, text)


async def cb_admin_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID:
        return
    # Placeholder — extend with DB revoke logic
    await safe_edit(
        q,
        f"<b>{sc('revoke session')}</b>\n\n<i>Send the phone number to revoke:</i>",
    )


async def cb_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID:
        return
    import database.db as db
    try:
        total_users = db.get_total_users()
    except Exception:
        total_users = "N/A"
    text = (
        f"<b>📊 {sc('bot stats')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"👥 <b>{sc('total users')}:</b> <code>{total_users}</code>\n"
        f"⚡ <b>{sc('status')}:</b> {sc('online')}"
    )
    await safe_edit(q, text, admin_panel())


async def cb_admin_dp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a scary DP and send it to the admin with BotFather instructions."""
    q = update.callback_query
    await q.answer(sc("generating dark dp..."), show_alert=False)
    if q.from_user.id != config.OWNER_ID:
        return

    try:
        dp_buf = generate_scary_dp()   # SYNCHRONOUS — no await
        caption = (
            f"<b>😈 {sc('your khatarnak dp is ready!')} 😈</b>\n\n"
            f"<b>{sc('how to set as bot dp')}:</b>\n"
            f"1. Image ko save karo.\n"
            f"2. <a href='https://t.me/BotFather'>@BotFather</a> mein jao.\n"
            f"3. /setuserpic command do.\n"
            f"4. Apna bot select karo aur ye image upload karo.\n\n"
            f"<i>{sc('powered by nox syndicate')}</i>"
        )
        await q.message.reply_photo(
            photo=InputFile(dp_buf, filename="dark_dp.jpg"),
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"cb_admin_dp error: {e}")
        await q.message.reply_text(f"❌ Error generating DP: {e}")


def register(app: Application) -> None:
    app.add_handler(CommandHandler("admin",   cmd_admin))
    app.add_handler(CallbackQueryHandler(cb_admin_panel,   pattern="^admin:panel$"))
    app.add_handler(CallbackQueryHandler(cb_admin_addapi,  pattern="^admin:addapi$"))
    app.add_handler(CallbackQueryHandler(cb_admin_revoke,  pattern="^admin:revoke$"))
    app.add_handler(CallbackQueryHandler(cb_admin_stats,   pattern="^admin:stats$"))
    app.add_handler(CallbackQueryHandler(cb_admin_dp,      pattern="^admin:dp$"))
