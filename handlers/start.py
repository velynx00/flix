import io
import logging
from typing import Optional

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import config
import database.db as db
from keyboards.menus import main_menu, premium_menu, back_btn
from utils.banner import generate_banner
from utils.text import sc, escape_html

logger = logging.getLogger(__name__)


# ─── Shared banner helper ─────────────────────────────────────
# Used by this file AND imported by help.py to avoid duplication.

async def _fetch_dp(bot, user_id: int) -> Optional[bytes]:
    """Fetch the user's Telegram profile photo bytes. Returns None on failure."""
    try:
        photos = await bot.get_user_profile_photos(user_id=user_id, limit=1)
        if not photos.total_count:
            return None
        file_id = photos.photos[0][-1].file_id
        tg_file = await bot.get_file(file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        return buf.getvalue()
    except Exception:
        return None


async def _send_new_banner(
    q,           # CallbackQuery object
    text: str,
    title: str,
    reply_markup,
) -> None:
    """
    Delete the old message, generate a fresh banner with the given title,
    and send a NEW photo message. Required because Telegram cannot edit
    a photo message to show a different photo — only delete + resend works.
    """
    try:
        await q.message.delete()
    except Exception:
        pass

    dp_bytes = await _fetch_dp(q.get_bot(), q.from_user.id)

    # generate_banner is SYNCHRONOUS — do NOT await it
    banner = generate_banner(dp_bytes, title=title)

    await q.get_bot().send_photo(
        chat_id=q.message.chat_id,
        photo=InputFile(banner, filename="nox_banner.png"),
        caption=text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
        has_spoiler=True,
    )


async def safe_edit(query, text: str, reply_markup=None) -> None:
    """Edit caption if message has a photo, else edit text. Swallows 'not modified'."""
    try:
        if query.message.photo:
            await query.edit_message_caption(
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
        else:
            await query.edit_message_text(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"safe_edit error: {e}")


def _build_welcome(user_id: int, user_name: str) -> str:
    safe_name = escape_html(user_name)
    return (
        f"<blockquote>🕷️ <b>{sc('welcome to nox syndicate')}</b></blockquote>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"👋 <b>Hey</b> <a href='tg://user?id={user_id}'><b>{safe_name}</b></a><b>!</b>\n"
        f"⚡ <b>{sc('the ultimate telegram scraper & adder')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1️⃣ {sc('scrape members')}</b>\n"
        f"<b>2️⃣ {sc('add members')}</b>\n"
        f"<b>3️⃣ {sc('check status')} : <code>/myplan</code></b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🛡 <b>{sc('secure & encrypted')}</b>\n"
        f"🚀 <b>{sc('powered by nox syndicate')}</b>"
    )


# ─── Command handlers ─────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.upsert_user(user.id, user.username, user.full_name)
    context.user_data.clear()   # wipe stale flow state

    dp_bytes = await _fetch_dp(context.bot, user.id)
    welcome_text = _build_welcome(user.id, user.full_name)

    try:
        # generate_banner is SYNCHRONOUS — no await
        banner = generate_banner(dp_bytes, title="SYSTEM OVERRIDE")
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=InputFile(banner, filename="nox_welcome.png"),
            has_spoiler=True,
            caption=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(),
        )
    except Exception as e:
        logger.error(f"cmd_start banner error: {e}")
        # Fallback: plain text if banner crashes
        await update.message.reply_html(welcome_text, reply_markup=main_menu())


async def cmd_myplan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id == config.OWNER_ID:
        plan_text = "👑 <b>Owner Plan — Lifetime</b>"
    else:
        plan_text = "💎 <b>Free Plan</b>\n\nUpgrade via Premium menu."
    await update.message.reply_html(plan_text, reply_markup=back_btn())


# ─── Callback handlers ────────────────────────────────────────

async def cb_menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    await _send_new_banner(
        q,
        _build_welcome(q.from_user.id, q.from_user.full_name),
        "SYSTEM OVERRIDE",
        main_menu(),
    )


async def cb_menu_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()

    text = (
        f"<b>💎 {sc('nox syndicate premium')} 💎</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🔥 <b>{sc('unlock the ultimate power')}</b>\n\n"
        f"<b>{sc('premium benefits')}:</b>\n"
        f"▸ {sc('unlimited scraping')}\n"
        f"▸ {sc('unlimited adding')}\n"
        f"▸ {sc('no daily limits')}\n"
        f"▸ {sc('priority support')}\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🛒 <b>{sc('to purchase, contact')}:</b> "
        f"<a href='https://t.me/Velynx007'><b>@Velynx007</b></a>"
    )
    await _send_new_banner(q, text, "PREMIUM ACCESS", premium_menu())


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("myplan",  cmd_myplan))
    app.add_handler(CallbackQueryHandler(cb_menu_back,    pattern="^menu:back$"))
    app.add_handler(CallbackQueryHandler(cb_menu_premium, pattern="^menu:premium$"))
