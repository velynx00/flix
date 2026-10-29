# ============================================================
# handlers/router.py — Fallback handlers + Error Handling
# ============================================================

import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from database.db import db
from keyboards.menus import admin_panel
from utils.text import sc

logger = logging.getLogger(__name__)

# ── Admin Command ─────────────────────────────────────────────

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /admin command. Only accessible by the OWNER_ID.
    """
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        # Silently ignore if not owner
        return
        
    text = (
        f"<b>⧩ {sc('Admin Control Panel')} ⧩</b>\n\n"
        f"{sc('Welcome to the elite control center.')}\n"
        f"{sc('Select an action below.')}"
    )
    
    await update.message.reply_html(
        text,
        reply_markup=admin_panel(),
    )

# ── Callback for Admin Panel ──────────────────────────────────

async def cb_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id != config.OWNER_ID:
        return await query.answer("Unauthorized", show_alert=True)

    text = (
        f"<b>⧩ {sc('Admin Control Panel')} ⧩</b>\n\n"
        f"{sc('Welcome to the elite control center.')}\n"
        f"{sc('Select an action below.')}"
    )
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel(),
    )

# ── Global Error Handler ──────────────────────────────────────

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log the error and stop the bot from crashing.
    """
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# ── Handler Registration ──────────────────────────────────────

def register(app: Application) -> None:
    # Admin commands and callbacks
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(cb_admin_panel, pattern="^admin:panel$"))

    # Error handler (Keep this at the very end)
    app.add_error_handler(global_error_handler)
