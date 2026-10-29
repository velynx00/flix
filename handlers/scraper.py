# ============================================================
# handlers/scraper.py — Scrape Flow + Add Flow Handlers
#
# Scrape Flow:
#   cb_scrape_start      → prompt group input
#   handle_scrape_text   → run engine, stream progress, offer CSV export
#   cb_scrape_export     → send CSV to user
#
# Add Flow:
#   cb_add_start         → prompt for CSV document
#   handle_add_document  → receive CSV, prompt for target group
#   handle_add_text      → run engine, stream progress
#
# Session Setup Flow:
#   cb_session_setup     → ask for API choice
#   cb_api_custom        → ask for api_id
#   cb_api_default       → jump to phone prompt
#   handle_session_text  → process api_id, api_hash, phone, code, 2fa
#   cb_session_revoke    → delete session from DB
#   cb_otp_cancel        → abort session setup
# ============================================================

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import Optional

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telethon import errors as telethon_errors

import config
import database.db as db
from core.engine import (
    scrape_members,
    add_members,
    export_to_csv,
    load_from_csv,
    create_session_send_code,
    create_session_sign_in,
)
from keyboards.menus import (
    cancel_operation,
    main_menu,
    scrape_menu,
    add_menu,
    session_menu,
    api_choice_menu,
    otp_resend_menu,
)
from utils.text import sc, build_progress_bar, escape_html
from handlers import states
from handlers.states import (
    STATE_SCRAPE_AWAITING_GROUP,
    STATE_ADD_AWAITING_SOURCE_CSV,
    STATE_ADD_AWAITING_TARGET_GROUP,
    STATE_SESSION_AWAITING_API_ID,
    STATE_SESSION_AWAITING_API_HASH,
    STATE_SESSION_AWAITING_PHONE,
    STATE_SESSION_AWAITING_CODE,
    STATE_SESSION_AWAITING_PASSWORD,
)

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────
# SCRAPE FLOW
# ────────────────────────────────────────────────────────────

async def cb_scrape_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='scrape:start'.
    Prompt the user to send the target group link/username.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # Verify session exists before entering state
    if not db.has_session(user_id):
        await query.edit_message_text(
            f"🔑 <b>{sc('No Session Found')}</b>\n\n"
            f"{sc('Please setup a session first.')}",
            parse_mode=ParseMode.HTML,
            reply_markup=session_menu(has_session=False),
        )
        return

    states.set_state(user_id, STATE_SCRAPE_AWAITING_GROUP)
    states.clear_data(user_id)

    await query.edit_message_text(
        f"<b>⟢ {sc('Scraper Engine')} ⟢</b>\n\n"
        f"<b>{sc('Step 1 of 1')}</b>\n"
        f"{sc('Send the group username or link to scrape.')}\n\n"
        f"<i>{sc('Examples:')}</i>\n"
        f"  <code>@telegram</code>\n"
        f"  <code>https://t.me/telegram</code>",
        parse_mode=ParseMode.HTML,
    )


async def handle_scrape_group_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Text message handler for STATE_SCRAPE_AWAITING_GROUP.

    Runs the scrape engine, sends live progress updates, and on
    completion stores the members list in the user's scratch-pad
    so cb_scrape_export can write the CSV.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id     = update.effective_user.id
    group_input = (update.message.text or "").strip()

    if not group_input:
        await update.message.reply_html(
            f"⚠️ {sc('Please send a valid group link or username.')}"
        )
        return

    # ── Determine limit ───────────────────────────────────────
    is_prem = db.is_premium(user_id)
    limit   = None if is_prem else config.FREE_SCRAPE_LIMIT

    # ── Retrieve session ──────────────────────────────────────
    sess = db.get_session(user_id)
    if not sess:
        states.clear_all(user_id)
        await update.message.reply_html(
            f"🔑 <b>{sc('Session expired.')}</b> {sc('Please setup again.')}",
            reply_markup=main_menu(),
        )
        return

    states.set_state(user_id, None)   # exit state — we're processing
    states.clear_cancel(user_id)

    # ── Send initial progress message ─────────────────────────
    progress_msg = await update.message.reply_html(
        f"<b>⟢ {sc('Scraping')} <code>{escape_html(group_input)}</code></b>\n\n"
        f"{build_progress_bar(0, 1)} {sc('Starting...')}",
        reply_markup=cancel_operation(),
    )

    members      : list[dict] = []
    op_id        = db.create_operation(user_id, "scrape", group_input)
    last_edit_at : float      = 0.0
    EDIT_INTERVAL: float      = 2.5   # seconds between progress edits

    try:
        async for member in scrape_members(
            session_string = sess["session_string"],
            api_id         = sess["api_id"],
            api_hash       = sess["api_hash"],
            group_input    = group_input,
            limit          = limit,
            user_id        = user_id,
        ):
            members.append(member)
            now = asyncio.get_event_loop().time()

            # Throttle edits to avoid Telegram 429
            if now - last_edit_at >= EDIT_INTERVAL:
                last_edit_at = now
                bar = build_progress_bar(
                    len(members),
                    limit if limit else len(members) + 1,
                )
                try:
                    await progress_msg.edit_text(
                        f"<b>⟢ {sc('Scraping')} <code>{escape_html(group_input)}</code></b>\n\n"
                        f"{bar}\n"
                        f"👥 <b>{sc('Found')}:</b> {len(members)}",
                        parse_mode    = ParseMode.HTML,
                        reply_markup  = cancel_operation(),
                    )
                except Exception:
                    pass   # edit rate-limit; skip silently

        # ── Scrape finished ───────────────────────────────────
        cancelled = states.is_cancelled(user_id)
        states.clear_cancel(user_id)

        if not members:
            db.finish_operation(op_id, 0, "error", "no_members_found")
            await progress_msg.edit_text(
                f"<b>{sc('No members found.')}</b>\n"
                f"{sc('The group may be private or empty.')}",
                parse_mode=ParseMode.HTML,
                reply_markup=scrape_menu(),
            )
            states.clear_all(user_id)
            return

        # Store in scratch-pad for CSV export
        states.set_data(user_id, "scraped_members", members)
        states.set_data(user_id, "scraped_group",   group_input)

        db.increment_scrape_count(user_id, len(members))
        db.finish_operation(op_id, len(members), "partial" if cancelled else "done")
        db.update_session_last_used(user_id)

        suffix = sc("(cancelled)") if cancelled else sc("complete")
        await progress_msg.edit_text(
            f"<b>✅ {sc('Scrape')} {suffix}</b>\n\n"
            f"👥 <b>{sc('Members Scraped')}:</b> {len(members)}\n"
            f"📦 <b>{sc('Group')}:</b> <code>{escape_html(group_input)}</code>\n\n"
            f"<b>{sc('Tap Export CSV to download the list.')}</b>",
            parse_mode   = ParseMode.HTML,
            reply_markup = scrape_menu(),
        )

    except Exception as exc:
        logger.error(f"[SCRAPER] Scrape error for user={user_id}: {exc}")
        db.finish_operation(op_id, len(members), "error", str(exc)[:200])
        states.clear_all(user_id)
        await progress_msg.edit_text(
            f"<b>❌ {sc('Scrape Failed')}</b>\n\n"
            f"<code>{escape_html(str(exc)[:300])}</code>",
            parse_mode   = ParseMode.HTML,
            reply_markup = scrape_menu(),
        )


async def cb_scrape_export(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='scrape:export'.
    Write the in-memory scraped list to a CSV and send it to the user.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    members = states.get_data(user_id, "scraped_members")

    if not members:
        await query.answer(
            sc("no scraped data — run a scrape first"),
            show_alert=True,
        )
        return

    group   = states.get_data(user_id, "scraped_group", "unknown")
    csv_path = export_to_csv(members)

    try:
        with open(csv_path, "rb") as f:
            await context.bot.send_document(
                chat_id  = query.message.chat_id,
                document = InputFile(f, filename=f"velyn_scrape_{user_id}.csv"),
                caption  = (
                    f"<b>📄 {sc('Scrape Export')}</b>\n\n"
                    f"👥 <b>{sc('Members')}:</b> {len(members)}\n"
                    f"📦 <b>{sc('Group')}:</b> <code>{escape_html(group)}</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
    finally:
        # Clean up temp file
        try:
            os.remove(csv_path)
        except OSError:
            pass


# ────────────────────────────────────────────────────────────
# ADD FLOW
# ────────────────────────────────────────────────────────────

async def cb_add_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='add:start'.
    Ask the user to upload their scrape CSV.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if not db.has_session(user_id):
        await query.edit_message_text(
            f"🔑 <b>{sc('No Session Found')}</b>\n\n"
            f"{sc('Please setup a session first.')}",
            parse_mode=ParseMode.HTML,
            reply_markup=session_menu(has_session=False),
        )
        return

    states.set_state(user_id, STATE_ADD_AWAITING_SOURCE_CSV)
    states.clear_data(user_id)

    await query.edit_message_text(
        f"<b>✦ {sc('Member Injector')} ✦</b>\n\n"
        f"<b>{sc('Step 1 of 2')}</b>\n"
        f"{sc('Upload the scraped members CSV file.')}\n\n"
        f"<i>{sc('The file must have been exported from this bot.')}</i>",
        parse_mode=ParseMode.HTML,
    )


async def handle_add_csv_upload(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Document handler for STATE_ADD_AWAITING_SOURCE_CSV.
    Downloads the uploaded CSV, validates it, then asks for the target group.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id  = update.effective_user.id
    document = update.message.document

    if document is None or not document.file_name.endswith(".csv"):
        await update.message.reply_html(
            f"⚠️ {sc('Please upload a .csv file.')}"
        )
        return

    # Download to a temp file
    fd, tmp_path = tempfile.mkstemp(suffix=".csv", prefix="velyn_add_")
    os.close(fd)

    try:
        tg_file = await context.bot.get_file(document.file_id)
        await tg_file.download_to_drive(tmp_path)

        members = load_from_csv(tmp_path)
    except Exception as exc:
        logger.error(f"[SCRAPER] CSV load error: {exc}")
        await update.message.reply_html(
            f"❌ <b>{sc('Failed to read CSV')}</b>\n<code>{escape_html(str(exc))}</code>"
        )
        return
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if not members:
        await update.message.reply_html(
            f"⚠️ <b>{sc('CSV is empty.')}</b>"
        )
        return

    # Enforce free-tier limit on the add count too
    is_prem = db.is_premium(user_id)
    if not is_prem and len(members) > config.FREE_ADD_LIMIT:
        members = members[: config.FREE_ADD_LIMIT]
        await update.message.reply_html(
            f"⚠️ <b>{sc('Free tier limit applied.')}</b>\n"
            f"{sc('Only the first')} <b>{config.FREE_ADD_LIMIT}</b> "
            f"{sc('members will be added.')}\n"
            f"{sc('Upgrade to premium for unlimited.')}"
        )

    states.set_data(user_id, "add_members", members)
    states.set_state(user_id, STATE_ADD_AWAITING_TARGET_GROUP)

    await update.message.reply_html(
        f"<b>✦ {sc('Member Injector')} ✦</b>\n\n"
        f"<b>{sc('Step 2 of 2')}</b>\n"
        f"📋 <b>{sc('Members loaded')}:</b> {len(members)}\n\n"
        f"{sc('Now send the target group link or username.')}\n\n"
        f"<i>{sc('Example: @mygroup or https://t.me/mygroup')}</i>",
        parse_mode=ParseMode.HTML,
    )


async def handle_add_target_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Text message handler for STATE_ADD_AWAITING_TARGET_GROUP.
    Runs the add engine with live progress updates.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id      = update.effective_user.id
    group_input  = (update.message.text or "").strip()

    if not group_input:
        await update.message.reply_html(
            f"⚠️ {sc('Please send a valid group link or username.')}"
        )
        return

    members = states.get_data(user_id, "add_members")
    if not members:
        await update.message.reply_html(
            f"⚠️ {sc('Member list lost — please restart the add flow.')}",
            reply_markup=main_menu(),
        )
        states.clear_all(user_id)
        return

    sess = db.get_session(user_id)
    if not sess:
        states.clear_all(user_id)
        await update.message.reply_html(
            f"🔑 <b>{sc('Session expired.')}</b> {sc('Please setup again.')}",
            reply_markup=main_menu(),
        )
        return

    states.set_state(user_id, None)
    states.clear_cancel(user_id)

    total         = len(members)
    added_count   = 0
    skipped_count = 0
    error_count   = 0
    op_id         = db.create_operation(user_id, "add", group_input)
    last_edit_at  : float = 0.0
    EDIT_INTERVAL : float = 3.0

    progress_msg = await update.message.reply_html(
        f"<b>✦ {sc('Adding Members to')} <code>{escape_html(group_input)}</code></b>\n\n"
        f"{build_progress_bar(0, total)}\n"
        f"⏳ {sc('Starting in')} {config.ADD_DELAY_SECONDS}s {sc('intervals...')}",
        reply_markup=cancel_operation(),
    )

    try:
        async for result in add_members(
            session_string     = sess["session_string"],
            api_id             = sess["api_id"],
            api_hash           = sess["api_hash"],
            target_group_input = group_input,
            members            = members,
            delay              = config.ADD_DELAY_SECONDS,
            user_id            = user_id,
        ):
            status = result["status"]

            if status == "added":
                added_count += 1
            elif status == "cancelled":
                break
            elif status == "error":
                error_count += 1
            else:
                skipped_count += 1

            processed = added_count + skipped_count + error_count
            now = asyncio.get_event_loop().time()

            if now - last_edit_at >= EDIT_INTERVAL:
                last_edit_at = now
                bar = build_progress_bar(processed, total)
                try:
                    await progress_msg.edit_text(
                        f"<b>✦ {sc('Adding to')} <code>{escape_html(group_input)}</code></b>\n\n"
                        f"{bar}\n"
                        f"✅ {sc('Added')}: {added_count}   "
                        f"⏭ {sc('Skipped')}: {skipped_count}   "
                        f"❌ {sc('Errors')}: {error_count}",
                        parse_mode   = ParseMode.HTML,
                        reply_markup = cancel_operation(),
                    )
                except Exception:
                    pass

        cancelled = states.is_cancelled(user_id)
        states.clear_cancel(user_id)

        db.increment_add_count(user_id, added_count)
        db.finish_operation(
            op_id  = op_id,
            count  = added_count,
            status = "partial" if cancelled else "done",
        )
        db.update_session_last_used(user_id)

        suffix = sc("(cancelled)") if cancelled else sc("complete")
        await progress_msg.edit_text(
            f"<b>✅ {sc('Add Operation')} {suffix}</b>\n\n"
            f"✅ <b>{sc('Added')}:</b> {added_count}\n"
            f"⏭ <b>{sc('Skipped')}:</b> {skipped_count}\n"
            f"❌ <b>{sc('Errors')}:</b> {error_count}\n"
            f"📦 <b>{sc('Target')}:</b> <code>{escape_html(group_input)}</code>",
            parse_mode   = ParseMode.HTML,
            reply_markup = main_menu(),
        )

    except Exception as exc:
        logger.error(f"[SCRAPER] Add error for user={user_id}: {exc}")
        db.finish_operation(op_id, added_count, "error", str(exc)[:200])
        await progress_msg.edit_text(
            f"<b>❌ {sc('Add Failed')}</b>\n\n"
            f"<code>{escape_html(str(exc)[:300])}</code>",
            parse_mode   = ParseMode.HTML,
            reply_markup = main_menu(),
        )

    states.clear_all(user_id)


# ────────────────────────────────────────────────────────────
# SESSION SETUP FLOW
# ────────────────────────────────────────────────────────────

async def cb_session_setup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='session:setup'.
    Ask the user whether to use their own API credentials or the defaults.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    states.clear_all(user_id)

    await query.edit_message_text(
        f"<b>🔑 {sc('Session Setup')} — {sc('Step 1 of 4')}</b>\n\n"
        f"{sc('Choose your API credentials:')}\n\n"
        f"▸ <b>{sc('Own API')}</b>: {sc('Use your api_id + api_hash from my.telegram.org')}\n"
        f"▸ <b>{sc('Default API')}</b>: {sc('Use the built-in credentials (less stable)')}\n\n"
        f"<i>{sc('Own credentials are recommended for heavy use.')}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=api_choice_menu(),
    )


async def cb_api_custom(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='api:custom'.
    Enter the custom API ID input state.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    states.set_state(user_id, STATE_SESSION_AWAITING_API_ID)

    await query.edit_message_text(
        f"<b>🔑 {sc('Session Setup')} — {sc('Step 2 of 4')}</b>\n\n"
        f"{sc('Send your')} <b>API ID</b> {sc('(numeric, from my.telegram.org):')}\n\n"
        f"<i>{sc('Example: 12345678')}</i>",
        parse_mode=ParseMode.HTML,
    )


async def cb_api_default(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='api:default'.
    Store the default API creds and jump straight to the phone step.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    states.set_data(user_id, "api_id",   config.DEFAULT_API_ID)
    states.set_data(user_id, "api_hash", config.DEFAULT_API_HASH)
    states.set_state(user_id, STATE_SESSION_AWAITING_PHONE)

    await query.edit_message_text(
        f"<b>🔑 {sc('Session Setup')} — {sc('Step 3 of 4')}</b>\n\n"
        f"✅ <b>{sc('Default API credentials selected.')}</b>\n\n"
        f"{sc('Now send your phone number in international format:')}\n\n"
        f"<i>{sc('Example: +919876543210')}</i>",
        parse_mode=ParseMode.HTML,
    )


async def cb_session_revoke(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='session:revoke'.
    Delete the user's stored Telethon session.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    db.delete_session(user_id)
    states.clear_all(user_id)

    await query.edit_message_text(
        f"<b>🗑 {sc('Session Revoked')}</b>\n\n"
        f"{sc('Your session has been removed.')}\n"
        f"{sc('You can setup a new one anytime.')}",
        parse_mode   = ParseMode.HTML,
        reply_markup = session_menu(has_session=False),
    )


async def cb_otp_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='otp:cancel'.
    Abort the session setup flow mid-OTP.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # Disconnect the pending client if stored
    pending_client = states.get_data(user_id, "pending_client")
    if pending_client:
        try:
            await pending_client.disconnect()
        except Exception:
            pass

    states.clear_all(user_id)

    await query.edit_message_text(
        f"<b>↩ {sc('Setup Cancelled')}</b>\n\n"
        f"{sc('Session setup was aborted.')}",
        parse_mode   = ParseMode.HTML,
        reply_markup = main_menu(),
    )


async def cb_otp_resend(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='otp:resend'.
    Disconnect the pending client and restart from the phone step.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer(sc("resending code..."), show_alert=False)

    pending_client = states.get_data(user_id, "pending_client")
    if pending_client:
        try:
            await pending_client.disconnect()
        except Exception:
            pass

    states.set_data(user_id, "pending_client",    None)
    states.set_data(user_id, "phone_code_hash",   None)
    states.set_state(user_id, STATE_SESSION_AWAITING_PHONE)

    await query.edit_message_text(
        f"<b>🔑 {sc('Resend OTP')}</b>\n\n"
        f"{sc('Send your phone number again to receive a new code:')}\n\n"
        f"<i>{sc('Example: +919876543210')}</i>",
        parse_mode=ParseMode.HTML,
    )


async def handle_session_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Text message handler for all session setup states.

    State machine:
        STATE_SESSION_AWAITING_API_ID     → validate int → store → ask hash
        STATE_SESSION_AWAITING_API_HASH   → validate str → store → ask phone
        STATE_SESSION_AWAITING_PHONE      → send OTP → store client/hash → ask code
        STATE_SESSION_AWAITING_CODE       → sign in → maybe ask 2FA → save session
        STATE_SESSION_AWAITING_PASSWORD   → sign in with 2FA → save session

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id      = update.effective_user.id
    text_input   = (update.message.text or "").strip()
    current_state = states.get_state(user_id)

    # ── API ID ────────────────────────────────────────────────
    if current_state == STATE_SESSION_AWAITING_API_ID:
        if not text_input.isdigit():
            await update.message.reply_html(
                f"⚠️ <b>{sc('Invalid API ID')}</b>\n"
                f"{sc('Must be a numeric value.')}"
            )
            return

        states.set_data(user_id, "api_id", int(text_input))
        states.set_state(user_id, STATE_SESSION_AWAITING_API_HASH)

        await update.message.reply_html(
            f"<b>🔑 {sc('Session Setup')} — {sc('Step 3 of 4')}</b>\n\n"
            f"✅ <b>API ID:</b> <code>{text_input}</code>\n\n"
            f"{sc('Now send your')} <b>API Hash</b> {sc('(32-character hex string):')}\n\n"
            f"<i>{sc('Example: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4')}</i>",
            parse_mode=ParseMode.HTML,
        )

    # ── API Hash ──────────────────────────────────────────────
    elif current_state == STATE_SESSION_AWAITING_API_HASH:
        if len(text_input) < 10:
            await update.message.reply_html(
                f"⚠️ <b>{sc('Invalid API Hash')}</b>\n"
                f"{sc('Must be a 32-character hex string.')}"
            )
            return

        states.set_data(user_id, "api_hash", text_input)
        states.set_state(user_id, STATE_SESSION_AWAITING_PHONE)

        await update.message.reply_html(
            f"<b>🔑 {sc('Session Setup')} — {sc('Step 3 of 4')}</b>\n\n"
            f"✅ <b>API Hash:</b> <code>{text_input[:6]}…</code>\n\n"
            f"{sc('Now send your phone number in international format:')}\n\n"
            f"<i>{sc('Example: +919876543210')}</i>",
            parse_mode=ParseMode.HTML,
        )

    # ── Phone ─────────────────────────────────────────────────
    elif current_state == STATE_SESSION_AWAITING_PHONE:
        phone    = text_input
        api_id   = states.get_data(user_id, "api_id",   config.DEFAULT_API_ID)
        api_hash = states.get_data(user_id, "api_hash", config.DEFAULT_API_HASH)

        wait_msg = await update.message.reply_html(
            f"⏳ <b>{sc('Sending OTP to')} <code>{escape_html(phone)}</code>…</b>"
        )

        try:
            client, phone_code_hash = await create_session_send_code(
                phone    = phone,
                api_id   = api_id,
                api_hash = api_hash,
            )
        except telethon_errors.FloodWaitError as exc:
            await wait_msg.edit_text(
                f"⚠️ <b>{sc('Flood Wait')}</b> — {sc('retry after')} {exc.seconds}s",
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception as exc:
            await wait_msg.edit_text(
                f"❌ <b>{sc('Failed to send OTP')}</b>\n<code>{escape_html(str(exc))}</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        states.set_data(user_id, "phone",           phone)
        states.set_data(user_id, "phone_code_hash", phone_code_hash)
        states.set_data(user_id, "pending_client",  client)
        states.set_state(user_id, STATE_SESSION_AWAITING_CODE)

        await wait_msg.edit_text(
            f"<b>🔑 {sc('Session Setup')} — {sc('Step 4 of 4')}</b>\n\n"
            f"📲 <b>{sc('OTP sent to')} <code>{escape_html(phone)}</code></b>\n\n"
            f"{sc('Send the code you received (digits only):')}\n\n"
            f"<i>{sc('Example: 12345')}</i>",
            parse_mode   = ParseMode.HTML,
            reply_markup = otp_resend_menu(),
        )

    # ── OTP Code ──────────────────────────────────────────────
    elif current_state == STATE_SESSION_AWAITING_CODE:
        code            = text_input.replace(" ", "")
        phone           = states.get_data(user_id, "phone")
        phone_code_hash = states.get_data(user_id, "phone_code_hash")
        pending_client  = states.get_data(user_id, "pending_client")
        api_id          = states.get_data(user_id, "api_id",   config.DEFAULT_API_ID)
        api_hash        = states.get_data(user_id, "api_hash", config.DEFAULT_API_HASH)

        if not pending_client:
            await update.message.reply_html(
                f"⚠️ {sc('Session expired. Please restart setup.')}",
                reply_markup=session_menu(has_session=False),
            )
            states.clear_all(user_id)
            return

        wait_msg = await update.message.reply_html(
            f"⏳ <b>{sc('Verifying code…')}</b>"
        )

        try:
            session_string = await create_session_sign_in(
                client          = pending_client,
                phone           = phone,
                phone_code_hash = phone_code_hash,
                code            = code,
            )
        except telethon_errors.SessionPasswordNeededError:
            # 2FA required
            states.set_state(user_id, STATE_SESSION_AWAITING_PASSWORD)
            # Keep pending_client connected for 2FA
            states.set_data(user_id, "pending_client", pending_client)
            await wait_msg.edit_text(
                f"🔐 <b>{sc('Two-Factor Authentication Required')}</b>\n\n"
                f"{sc('Send your 2FA password:')}\n\n"
                f"<i>{sc('(your Telegram account password)')}</i>",
                parse_mode=ParseMode.HTML,
            )
            return
        except telethon_errors.PhoneCodeInvalidError:
            await wait_msg.edit_text(
                f"❌ <b>{sc('Invalid Code')}</b>\n"
                f"{sc('The OTP you entered is wrong. Try again.')}",
                parse_mode   = ParseMode.HTML,
                reply_markup = otp_resend_menu(),
            )
            return
        except telethon_errors.PhoneCodeExpiredError:
            await wait_msg.edit_text(
                f"⌛ <b>{sc('Code Expired')}</b>\n"
                f"{sc('Request a new code.')}",
                parse_mode   = ParseMode.HTML,
                reply_markup = otp_resend_menu(),
            )
            states.set_state(user_id, STATE_SESSION_AWAITING_PHONE)
            return
        except Exception as exc:
            logger.error(f"[SESSION] Sign-in error: {exc}")
            await wait_msg.edit_text(
                f"❌ <b>{sc('Sign-in Failed')}</b>\n<code>{escape_html(str(exc)[:300])}</code>",
                parse_mode=ParseMode.HTML,
            )
            states.clear_all(user_id)
            return

        _complete_session_save(user_id, session_string, phone, api_id, api_hash)
        states.clear_all(user_id)

        await wait_msg.edit_text(
            f"<b>✅ {sc('Session Created Successfully')}</b>\n\n"
            f"📱 <b>{sc('Phone')}:</b> <code>{escape_html(phone)}</code>\n"
            f"🔑 <b>{sc('Session')}:</b> {sc('active')}\n\n"
            f"{sc('You can now use Scrape and Add features.')}",
            parse_mode   = ParseMode.HTML,
            reply_markup = main_menu(),
        )

    # ── 2FA Password ──────────────────────────────────────────
    elif current_state == STATE_SESSION_AWAITING_PASSWORD:
        password        = text_input
        phone           = states.get_data(user_id, "phone")
        phone_code_hash = states.get_data(user_id, "phone_code_hash")
        pending_client  = states.get_data(user_id, "pending_client")
        api_id          = states.get_data(user_id, "api_id",   config.DEFAULT_API_ID)
        api_hash        = states.get_data(user_id, "api_hash", config.DEFAULT_API_HASH)

        if not pending_client:
            await update.message.reply_html(
                f"⚠️ {sc('Session lost. Please restart setup.')}",
                reply_markup=session_menu(has_session=False),
            )
            states.clear_all(user_id)
            return

        wait_msg = await update.message.reply_html(
            f"⏳ <b>{sc('Verifying 2FA password…')}</b>"
        )

        try:
            session_string = await create_session_sign_in(
                client          = pending_client,
                phone           = phone,
                phone_code_hash = phone_code_hash,
                code            = "",          # not needed at this stage
                password        = password,
            )
        except telethon_errors.PasswordHashInvalidError:
            await wait_msg.edit_text(
                f"❌ <b>{sc('Wrong Password')}</b>\n"
                f"{sc('Try again:')}",
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception as exc:
            logger.error(f"[SESSION] 2FA error: {exc}")
            await wait_msg.edit_text(
                f"❌ <b>{sc('2FA Failed')}</b>\n<code>{escape_html(str(exc)[:300])}</code>",
                parse_mode=ParseMode.HTML,
            )
            states.clear_all(user_id)
            return

        _complete_session_save(user_id, session_string, phone, api_id, api_hash)
        states.clear_all(user_id)

        await wait_msg.edit_text(
            f"<b>✅ {sc('Session Created Successfully')}</b>\n\n"
            f"📱 <b>{sc('Phone')}:</b> <code>{escape_html(phone)}</code>\n"
            f"🔑 <b>{sc('Session')}:</b> {sc('active')}\n\n"
            f"{sc('2FA verified. You can now use Scrape and Add features.')}",
            parse_mode   = ParseMode.HTML,
            reply_markup = main_menu(),
        )


def _complete_session_save(
    user_id: int,
    session_string: str,
    phone: str,
    api_id: int,
    api_hash: str,
) -> None:
    """
    Persist a successfully created Telethon session to the database
    and ensure the user row exists.

    Parameters
    ----------
    user_id        : int
    session_string : str
    phone          : str
    api_id         : int
    api_hash       : str
    """
    db.save_session(
        user_id        = user_id,
        session_string = session_string,
        api_id         = api_id,
        api_hash       = api_hash,
        phone          = phone,
    )
    logger.info(f"[SESSION] Session saved for user={user_id}")


# ── Handler Registration ──────────────────────────────────────

def register(app: Application) -> None:
    """
    Attach all scraper.py handlers to the Application instance.

    Parameters
    ----------
    app : Application
    """
    # ── Scrape callbacks ──────────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_scrape_start,  pattern="^scrape:start$"))
    app.add_handler(CallbackQueryHandler(cb_scrape_export, pattern="^scrape:export$"))

    # ── Add callbacks ─────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_add_start, pattern="^add:start$"))

    # ── Session callbacks ─────────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_session_setup,  pattern="^session:setup$"))
    app.add_handler(CallbackQueryHandler(cb_session_revoke, pattern="^session:revoke$"))
    app.add_handler(CallbackQueryHandler(cb_api_custom,     pattern="^api:custom$"))
    app.add_handler(CallbackQueryHandler(cb_api_default,    pattern="^api:default$"))
    app.add_handler(CallbackQueryHandler(cb_otp_cancel,     pattern="^otp:cancel$"))
    app.add_handler(CallbackQueryHandler(cb_otp_resend,     pattern="^otp:resend$"))

    # ── Text messages (state-driven, group=2) ─────────────────
    # group=2 so they run after command handlers but before the admin group=5
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_session_text,
        ),
        group=2,
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_scrape_group_input,
        ),
        group=3,
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_add_target_group,
        ),
        group=4,
    )

    # ── Document upload (CSV for add flow) ────────────────────
    app.add_handler(
        MessageHandler(
            filters.Document.MimeType("text/csv") | filters.Document.FileExtension("csv"),
            handle_add_csv_upload,
        ),
        group=1,
    )
