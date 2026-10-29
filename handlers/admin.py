# ============================================================
# handlers/admin.py — Owner-Only Admin Panel
#
# /admin   — open the admin panel
# Callbacks:
#   admin:panel            — re-open panel
#   admin:stats            — bot-wide statistics
#   admin:grant            — begin grant premium flow
#   admin:revoke_premium   — begin revoke premium flow
#   admin:revoke_session   — begin revoke session flow
#   admin:broadcast        — begin broadcast flow
#   plan:<name>            — complete a grant for a given plan
# Text message handler:
#   Intercepts messages during admin state flows
# ============================================================

from __future__ import annotations

import asyncio
import logging
from typing import Optional

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
import database.db as db
from keyboards.menus import (
    admin_panel,
    plan_selector,
    confirm_action,
    main_menu,
)
from utils.text import sc, escape_html, format_number
from handlers import states
from handlers.states import (
    STATE_ADMIN_AWAITING_GRANT_ID,
    STATE_ADMIN_AWAITING_REVOKE_ID,
    STATE_ADMIN_AWAITING_SESSION_ID,
    STATE_ADMIN_AWAITING_BROADCAST,
    STATE_ADMIN_GRANT_SELECT_PLAN,
)

logger = logging.getLogger(__name__)


# ── Owner guard ───────────────────────────────────────────────

def _is_owner(user_id: int) -> bool:
    """
    Return True if *user_id* is the bot owner defined in config.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    bool
    """
    return user_id == config.OWNER_ID


async def _deny(update: Update) -> None:
    """
    Send a standard 'access denied' reply for non-owner users.

    Parameters
    ----------
    update : Update
    """
    msg = update.message or (update.callback_query and update.callback_query.message)
    if update.callback_query:
        await update.callback_query.answer(sc("access denied"), show_alert=True)
        return
    if msg:
        await msg.reply_html(
            f"🚫 <b>{sc('Access Denied')}</b>\n"
            f"{sc('This area is restricted to the owner.')}"
        )


# ── Stats builder ─────────────────────────────────────────────

def _build_stats_text() -> str:
    """
    Assemble a formatted bot-statistics message.

    Returns
    -------
    str — HTML string.
    """
    total_users   = db.get_user_count()
    premium_count = db.get_premium_user_count()
    session_count = db.get_session_count()
    total_ops     = db.get_total_operations()

    return (
        f"<b>📊 {sc('Bot Statistics')} ─ {config.BOT_NAME}</b>\n\n"
        f"👥 <b>{sc('Total Users')}:</b> {format_number(total_users)}\n"
        f"⭐ <b>{sc('Premium Users')}:</b> {format_number(premium_count)}\n"
        f"🔑 <b>{sc('Active Sessions')}:</b> {format_number(session_count)}\n"
        f"⚙️ <b>{sc('Completed Ops')}:</b> {format_number(total_ops)}\n\n"
        f"🤖 <b>{sc('Version')}:</b> <code>v{config.VERSION}</code>"
    )


# ── /admin command ────────────────────────────────────────────

async def cmd_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle the /admin command.
    Only the owner may invoke this; everyone else is denied.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    states.clear_all(user_id)

    await update.message.reply_html(
        f"<b>🛡 {sc('Velyn Nox Admin Panel')}</b>\n\n"
        f"{sc('Welcome back, master. Select an action.')}",
        reply_markup=admin_panel(),
    )


# ── Panel / Stats callbacks ───────────────────────────────────

async def cb_admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='admin:panel'.
    Re-render the admin panel inline.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    await query.answer()
    states.clear_all(user_id)

    await query.edit_message_text(
        f"<b>🛡 {sc('Velyn Nox Admin Panel')}</b>\n\n"
        f"{sc('Select an action.')}",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel(),
    )


async def cb_admin_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='admin:stats'.
    Show aggregated bot statistics.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    await query.answer()
    text = _build_stats_text()
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel(),
    )


# ── Grant Premium flow ────────────────────────────────────────

async def cb_admin_grant(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='admin:grant'.
    Begin the grant-premium flow by asking for the target user_id.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    await query.answer()
    states.set_state(user_id, STATE_ADMIN_AWAITING_GRANT_ID)

    await query.edit_message_text(
        f"<b>✅ {sc('Grant Premium')} — {sc('Step 1/2')}</b>\n\n"
        f"{sc('Send the Telegram User ID of the person you want to grant premium to.')}\n\n"
        f"<i>{sc('Example: 123456789')}</i>",
        parse_mode=ParseMode.HTML,
    )


async def cb_plan_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='plan:<name>'.
    Complete the premium grant with the chosen plan.

    The target user_id was stored in the admin's scratch-pad under 'grant_target'.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    plan        = query.data.split(":")[1]   # e.g. 'monthly'
    target_id   = states.get_data(user_id, "grant_target")

    if target_id is None:
        await query.answer(sc("session expired, start again"), show_alert=True)
        states.clear_all(user_id)
        return

    await query.answer()

    # Perform the grant
    try:
        db.grant_premium(
            user_id    = target_id,
            plan       = plan,
            granted_by = user_id,
        )
    except Exception as exc:
        logger.error(f"[ADMIN] Grant failed: {exc}")
        await query.edit_message_text(
            f"❌ <b>{sc('Grant Failed')}</b>\n<code>{exc}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_panel(),
        )
        states.clear_all(user_id)
        return

    days   = config.PLAN_DURATIONS.get(plan, 30)
    states.clear_all(user_id)

    await query.edit_message_text(
        f"<b>✅ {sc('Premium Granted')}</b>\n\n"
        f"👤 <b>{sc('User ID')}:</b> <code>{target_id}</code>\n"
        f"⭐ <b>{sc('Plan')}:</b> {sc(plan)}\n"
        f"📅 <b>{sc('Duration')}:</b> {days} {sc('days')}",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel(),
    )

    # Notify the recipient
    try:
        await context.bot.send_message(
            chat_id    = target_id,
            text       = (
                f"🎉 <b>{sc('Congratulations!')}</b>\n\n"
                f"{sc('You have been granted')} <b>{sc(plan)} {sc('premium')}</b> "
                f"{sc('access for')} <b>{days} {sc('days')}</b>.\n\n"
                f"{sc('Enjoy the elite experience.')} ⭐"
            ),
            parse_mode = ParseMode.HTML,
        )
    except Exception as exc:
        logger.warning(f"[ADMIN] Could not notify user {target_id}: {exc}")


# ── Revoke Premium flow ───────────────────────────────────────

async def cb_admin_revoke_premium(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='admin:revoke_premium'.
    Begin the revoke-premium flow by asking for the target user_id.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    await query.answer()
    states.set_state(user_id, STATE_ADMIN_AWAITING_REVOKE_ID)

    await query.edit_message_text(
        f"<b>❌ {sc('Revoke Premium')} — {sc('Step 1/1')}</b>\n\n"
        f"{sc('Send the Telegram User ID to revoke premium from.')}\n\n"
        f"<i>{sc('Example: 123456789')}</i>",
        parse_mode=ParseMode.HTML,
    )


# ── Revoke Session flow ───────────────────────────────────────

async def cb_admin_revoke_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='admin:revoke_session'.
    Begin the revoke-session flow by asking for the target user_id.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    await query.answer()
    states.set_state(user_id, STATE_ADMIN_AWAITING_SESSION_ID)

    await query.edit_message_text(
        f"<b>🔑 {sc('Revoke Session')} — {sc('Step 1/1')}</b>\n\n"
        f"{sc('Send the Telegram User ID whose session you want to revoke.')}\n\n"
        f"<i>{sc('Example: 123456789')}</i>",
        parse_mode=ParseMode.HTML,
    )


# ── Broadcast flow ────────────────────────────────────────────

async def cb_admin_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='admin:broadcast'.
    Prompt the admin to type the broadcast message.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await _deny(update)
        return

    await query.answer()
    states.set_state(user_id, STATE_ADMIN_AWAITING_BROADCAST)

    await query.edit_message_text(
        f"<b>📢 {sc('Broadcast')} — {sc('Step 1/1')}</b>\n\n"
        f"{sc('Type the message you want to send to ALL users.')}\n"
        f"{sc('HTML formatting is supported.')}\n\n"
        f"<i>{sc('Example: Hello everyone! New update is live.')}</i>",
        parse_mode=ParseMode.HTML,
    )


# ── Message handler (catches text during admin flows) ─────────

async def handle_admin_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Intercept text messages when the owner is in an admin flow state.

    States handled:
        STATE_ADMIN_AWAITING_GRANT_ID
        STATE_ADMIN_AWAITING_REVOKE_ID
        STATE_ADMIN_AWAITING_SESSION_ID
        STATE_ADMIN_AWAITING_BROADCAST

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        return   # not for us

    current_state = states.get_state(user_id)
    text_input    = (update.message.text or "").strip()

    # ── Grant: awaiting target user ID ───────────────────────
    if current_state == STATE_ADMIN_AWAITING_GRANT_ID:
        if not text_input.isdigit():
            await update.message.reply_html(
                f"⚠️ <b>{sc('Invalid ID')}</b>\n"
                f"{sc('Please send a numeric Telegram User ID.')}"
            )
            return

        target_id = int(text_input)
        states.set_data(user_id, "grant_target", target_id)
        states.set_state(user_id, STATE_ADMIN_GRANT_SELECT_PLAN)

        await update.message.reply_html(
            f"<b>✅ {sc('Grant Premium')} — {sc('Step 2/2')}</b>\n\n"
            f"👤 <b>{sc('Target')}:</b> <code>{target_id}</code>\n\n"
            f"{sc('Now select the plan:')}",
            reply_markup=plan_selector(),
        )

    # ── Revoke premium: awaiting target user ID ───────────────
    elif current_state == STATE_ADMIN_AWAITING_REVOKE_ID:
        if not text_input.isdigit():
            await update.message.reply_html(
                f"⚠️ <b>{sc('Invalid ID')}</b>\n"
                f"{sc('Please send a numeric Telegram User ID.')}"
            )
            return

        target_id = int(text_input)

        if not db.is_premium(target_id):
            await update.message.reply_html(
                f"ℹ️ <b>{sc('User is not premium.')}</b>\n"
                f"<code>{target_id}</code>",
                reply_markup=admin_panel(),
            )
        else:
            db.revoke_premium(target_id)
            await update.message.reply_html(
                f"<b>❌ {sc('Premium Revoked')}</b>\n\n"
                f"👤 <b>{sc('User ID')}:</b> <code>{target_id}</code>",
                reply_markup=admin_panel(),
            )

            # Notify the revoked user
            try:
                await context.bot.send_message(
                    chat_id    = target_id,
                    text       = (
                        f"⚠️ <b>{sc('Premium Revoked')}</b>\n\n"
                        f"{sc('Your premium access has been revoked by the owner.')}"
                    ),
                    parse_mode = ParseMode.HTML,
                )
            except Exception:
                pass

        states.clear_all(user_id)

    # ── Revoke session: awaiting target user ID ───────────────
    elif current_state == STATE_ADMIN_AWAITING_SESSION_ID:
        if not text_input.isdigit():
            await update.message.reply_html(
                f"⚠️ <b>{sc('Invalid ID')}</b>\n"
                f"{sc('Please send a numeric Telegram User ID.')}"
            )
            return

        target_id = int(text_input)

        if not db.has_session(target_id):
            await update.message.reply_html(
                f"ℹ️ <b>{sc('No active session found.')}</b>\n"
                f"<code>{target_id}</code>",
                reply_markup=admin_panel(),
            )
        else:
            db.delete_session(target_id)
            await update.message.reply_html(
                f"<b>🔑 {sc('Session Revoked')}</b>\n\n"
                f"👤 <b>{sc('User ID')}:</b> <code>{target_id}</code>",
                reply_markup=admin_panel(),
            )

        states.clear_all(user_id)

    # ── Broadcast: awaiting the message text ──────────────────
    elif current_state == STATE_ADMIN_AWAITING_BROADCAST:
        broadcast_text = text_input
        all_users      = db.get_all_users()
        total          = len(all_users)
        sent           = 0
        failed         = 0

        progress_msg = await update.message.reply_html(
            f"<b>📢 {sc('Broadcasting...')}</b>\n"
            f"0 / {total}"
        )

        for i, row in enumerate(all_users):
            uid = row["user_id"]
            try:
                await context.bot.send_message(
                    chat_id    = uid,
                    text       = broadcast_text,
                    parse_mode = ParseMode.HTML,
                )
                sent += 1
            except Exception:
                failed += 1

            # Update progress every 20 users
            if (i + 1) % 20 == 0 or (i + 1) == total:
                try:
                    await progress_msg.edit_text(
                        f"<b>📢 {sc('Broadcasting...')}</b>\n"
                        f"{i + 1} / {total}",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass

            await asyncio.sleep(0.05)   # rate-limit guard

        states.clear_all(user_id)
        await progress_msg.edit_text(
            f"<b>✅ {sc('Broadcast Complete')}</b>\n\n"
            f"📤 <b>{sc('Sent')}:</b> {sent}\n"
            f"❌ <b>{sc('Failed')}:</b> {failed}\n"
            f"👥 <b>{sc('Total')}:</b> {total}",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_panel(),
        )


# ── Handler Registration ──────────────────────────────────────

def register(app: Application) -> None:
    """
    Attach all admin.py handlers to the Application instance.

    Parameters
    ----------
    app : Application — The running PTB Application.
    """
    # Commands
    app.add_handler(CommandHandler("admin", cmd_admin))

    # Callback queries
    app.add_handler(CallbackQueryHandler(cb_admin_panel,          pattern="^admin:panel$"))
    app.add_handler(CallbackQueryHandler(cb_admin_stats,          pattern="^admin:stats$"))
    app.add_handler(CallbackQueryHandler(cb_admin_grant,          pattern="^admin:grant$"))
    app.add_handler(CallbackQueryHandler(cb_admin_revoke_premium, pattern="^admin:revoke_premium$"))
    app.add_handler(CallbackQueryHandler(cb_admin_revoke_session, pattern="^admin:revoke_session$"))
    app.add_handler(CallbackQueryHandler(cb_admin_broadcast,      pattern="^admin:broadcast$"))
    app.add_handler(CallbackQueryHandler(cb_plan_selected,        pattern="^plan:"))

    # Admin text input — lower priority so other handlers fire first
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.User(config.OWNER_ID),
            handle_admin_text,
        ),
        group=5,   # high group number = low priority
    )
