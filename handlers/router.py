# ============================================================
# handlers/router.py — Global Message Router
#
# This module acts as the top-level dispatcher for messages
# that don't belong to a specific named state but still need
# to be handled (e.g. unknown commands, unsupported media,
# banned-user interception, bare text with no active state).
#
# It also provides the global error handler registered on the
# Application instance.
# ============================================================

from __future__ import annotations

import logging
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

import database.db as db
from utils.text import sc
from handlers import states
from keyboards.menus import main_menu

logger = logging.getLogger(__name__)


# ── Banned user interceptor ───────────────────────────────────

async def handle_banned(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Silently drop all updates from banned users.
    Called from the Application's pre-handler chain in main.py
    (or you can register it as a very low group index handler).

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user = update.effective_user
    if user is None:
        return

    if db.is_banned(user.id):
        logger.info(f"[ROUTER] Blocked banned user={user.id}")
        if update.message:
            await update.message.reply_html(
                f"🚫 <b>{sc('Access Denied')}</b>\n"
                f"{sc('Your account has been restricted from using this bot.')}"
            )
        elif update.callback_query:
            await update.callback_query.answer(
                sc("you are banned from this bot"),
                show_alert=True,
            )


# ── Unknown command handler ───────────────────────────────────

async def handle_unknown_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Catch-all for any command that is not registered.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    if update.message is None:
        return

    await update.message.reply_html(
        f"<b>{sc('Unknown Command')}</b>\n\n"
        f"{sc('Use')} /start {sc('to open the main menu.')}"
    )


# ── Bare text (no active state) ───────────────────────────────

async def handle_idle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle plain text messages when the user is in the IDLE state
    (no active conversation flow).

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id = update.effective_user.id

    # Only respond if truly idle
    if not states.is_idle(user_id):
        return

    await update.message.reply_html(
        f"<b>{sc('Main Menu')}</b>\n\n"
        f"{sc('Select an option:')}\n"
        f"Or type /start to see the welcome message.",
        reply_markup=main_menu(),
    )


# ── Unsupported media types ───────────────────────────────────

async def handle_unsupported_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Politely tell the user when they send a media type
    (photo, video, sticker, audio, etc.) that the bot does not handle.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    if update.message is None:
        return

    # Only reply if not mid-flow
    user_id = update.effective_user.id
    if not states.is_idle(user_id):
        return

    await update.message.reply_html(
        f"<b>{sc('Unsupported Media')}</b>\n\n"
        f"{sc('This bot only accepts text and CSV documents.')}\n"
        f"{sc('Use')} /start {sc('to open the menu.')}",
    )


# ── Global error handler ──────────────────────────────────────

async def global_error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Catches all unhandled exceptions raised in any handler and logs
    them without crashing the bot.

    Sends a user-facing error message if the update contains a
    message or callback query we can reply to.

    Parameters
    ----------
    update  : object                    — May be an Update or None.
    context : ContextTypes.DEFAULT_TYPE
    """
    logger.error(
        "[ROUTER] Unhandled exception:\n%s",
        "".join(traceback.format_exception(
            type(context.error),
            context.error,
            context.error.__traceback__,
        )),
    )

    if not isinstance(update, Update):
        return

    error_text = (
        f"<b>⚠️ {sc('Internal Error')}</b>\n\n"
        f"{sc('Something went wrong. Please try again.')}\n"
        f"{sc('If the problem persists, contact the owner.')}"
    )

    try:
        if update.message:
            await update.message.reply_html(error_text)
        elif update.callback_query:
            await update.callback_query.answer(
                sc("an error occurred, please try again"),
                show_alert=True,
            )
    except Exception as exc:
        logger.error(f"[ROUTER] Could not send error message: {exc}")


# ── Handler Registration ──────────────────────────────────────

def register(app: Application) -> None:
    """
    Register all router-level handlers.

    These are registered at high group numbers so they act as
    fallbacks after all feature-specific handlers have had a chance.

    Parameters
    ----------
    app : Application
    """
    # Unknown commands — group 10 (fires last among command handlers)
    app.add_handler(
        MessageHandler(filters.COMMAND, handle_unknown_command),
        group=10,
    )

    # Idle text — group 9
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idle_text),
        group=9,
    )

    # Unsupported media — group 8
    app.add_handler(
        MessageHandler(
            (
                filters.PHOTO
                | filters.VIDEO
                | filters.AUDIO
                | filters.VOICE
                | filters.Sticker.ALL
                | filters.ANIMATION
                | filters.Document.ALL
            ) & ~(
                filters.Document.MimeType("text/csv")
                | filters.Document.FileExtension("csv")
            ),
            handle_unsupported_media,
        ),
        group=8,
    )

    # Global error handler
    app.add_error_handler(global_error_handler)
