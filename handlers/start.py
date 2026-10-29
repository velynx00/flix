# ============================================================
# handlers/start.py — /start command + Main Menu Callbacks
#
# Responsibilities:
#   • /start   — Send welcome message with banner (has_spoiler=True)
#   • /myplan  — Show premium plan details
#   • /status  — Show usage stats
#   • Callback: menu:back, menu:scrape, menu:add, menu:premium
#   • Callback: status:refresh
#   • Callback: op:cancel   — Request operation abort
# ============================================================

from __future__ import annotations

import asyncio
import io
import logging
from datetime import datetime, timezone
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
from keyboards.menus import (
    main_menu,
    premium_menu,
    scrape_menu,
    add_menu,
    session_menu,
    status_menu,
)
from utils.banner import generate_banner
from utils.text import sc, escape_html, build_progress_bar, seconds_to_human
from handlers import states

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────

def _build_welcome(user_id: int, user_name: str) -> str:
    """
    Compose the HTML welcome message exactly as specified.

    Parameters
    ----------
    user_id   : int — Telegram user ID for the mention link.
    user_name : str — Display name.

    Returns
    -------
    str — HTML string ready for parse_mode=HTML.
    """
    return (
        f"<b>⧩ {sc('Velyn Nox Premium')} ⧩</b>\n"
        f"<b>{sc('The Ultimate Telegram Scraper & Adder')}</b>\n\n"
        f"🔥 <b>{sc('Welcome to the Elite Network')}, "
        f"<a href='tg://user?id={user_id}'>{escape_html(user_name)}</a>!</b>\n\n"
        f"<blockquote>"
        f"<b>{sc('How to Use')}</b>\n"
        f"▸ <b>{sc('Scrape')}</b> : {sc('Extracts members from a group')}\n"
        f"▸ <b>{sc('Add')}</b> : {sc('Injects members into your group')}\n"
        f"▸ <b>{sc('Premium')}</b> : {sc('Unlocks unlimited use')}"
        f"</blockquote>\n"
        f"<b>{sc('Select an option below to begin.')}</b>"
    )


def _build_status_text(ctx: dict) -> str:
    """
    Build a formatted /status message from the user's context dict.

    Parameters
    ----------
    ctx : dict — Output of db.get_full_user_context().

    Returns
    -------
    str — HTML-formatted status string.
    """
    user       = ctx["user"]
    prem       = ctx["is_premium"]
    prem_info  = ctx["premium_info"]
    has_sess   = ctx["has_session"]
    recent_ops = ctx["recent_ops"]

    # ── Header ──────────────────────────────────────────────
    lines = [
        f"<b>⧩ {sc('Account Status')} ⧩</b>\n",
        f"👤 <b>{sc('User')}:</b> {escape_html(user['full_name'])}",
        f"🆔 <b>{sc('ID')}:</b> <code>{user['user_id']}</code>",
        "",
    ]

    # ── Premium block ────────────────────────────────────────
    if prem and prem_info:
        expires_str = prem_info["expires_at"]
        plan        = prem_info["plan"].capitalize()
        lines += [
            f"⭐ <b>{sc('Plan')}:</b> {sc(plan)} {sc('Premium')}",
            f"📅 <b>{sc('Expires')}:</b> <code>{expires_str}</code>",
            "",
        ]
    else:
        lines += [
            f"🔒 <b>{sc('Plan')}:</b> {sc('Free Tier')}",
            f"   <i>{sc('Upgrade to remove limits')}</i>",
            "",
        ]

    # ── Session block ─────────────────────────────────────────
    sess_label = sc("active") if has_sess else sc("not configured")
    lines += [
        f"🔑 <b>{sc('Session')}:</b> {sess_label}",
        "",
    ]

    # ── Usage stats ───────────────────────────────────────────
    lines += [
        f"📤 <b>{sc('Total Scrapes')}:</b> {user['total_scrapes']}",
        f"📥 <b>{sc('Total Adds')}:</b> {user['total_adds']}",
        "",
    ]

    # ── Recent ops ────────────────────────────────────────────
    if recent_ops:
        lines.append(f"<b>{sc('Recent Operations')}:</b>")
        for op in recent_ops[:3]:
            icon   = "📤" if op["op_type"] == "scrape" else "📥"
            target = op["target_group"] or sc("unknown")
            lines.append(
                f"  {icon} {sc(op['op_type'])} · {target} · "
                f"{op['count']} {sc('members')} · "
                f"<code>{op['status']}</code>"
            )

    return "\n".join(lines)


async def _fetch_user_dp(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> Optional[bytes]:
    """
    Download the user's Telegram profile photo as raw bytes.
    Returns None on any failure (no photo set, network error, etc.).

    Parameters
    ----------
    context : ContextTypes.DEFAULT_TYPE
    user_id : int

    Returns
    -------
    bytes | None
    """
    try:
        photos = await context.bot.get_user_profile_photos(
            user_id=user_id, limit=1
        )
        if photos.total_count == 0:
            return None
        file_id = photos.photos[0][-1].file_id
        tg_file = await context.bot.get_file(file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        return buf.getvalue()
    except Exception as exc:
        logger.warning(f"[DP] Could not fetch DP for {user_id}: {exc}")
        return None


# ── /start handler ────────────────────────────────────────────

async def cmd_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle the /start command.

    Flow:
        1. Upsert user in DB.
        2. Fetch user DP bytes (for the banner).
        3. Generate the Pillow banner PNG.
        4. Send banner with has_spoiler=True.
        5. Reply with the welcome HTML + main_menu keyboard.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user     = update.effective_user
    chat     = update.effective_chat
    user_id  = user.id
    username = user.username
    name     = user.full_name

    # ── Register / refresh user ───────────────────────────────
    db.upsert_user(user_id, username, name)

    # ── Clear any stale state from prior sessions ─────────────
    states.clear_all(user_id)

    # ── Generate banner ───────────────────────────────────────
    dp_bytes = await _fetch_user_dp(context, user_id)
    try:
        banner_path = generate_banner(dp_bytes)
    except Exception as exc:
        logger.error(f"[START] Banner generation failed: {exc}")
        banner_path = None

    # ── Send banner ───────────────────────────────────────────
    if banner_path:
        try:
            with open(banner_path, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat.id,
                    photo=InputFile(f, filename="velyn_nox.png"),
                    has_spoiler=True,
                )
        except Exception as exc:
            logger.warning(f"[START] Could not send banner: {exc}")

    # ── Send welcome message ──────────────────────────────────
    welcome_text = _build_welcome(user_id, name)
    is_owner     = (user_id == config.OWNER_ID)

    await update.message.reply_html(
        welcome_text,
        reply_markup=main_menu(),
        disable_web_page_preview=True,
    )
    logger.info(f"[START] user={user_id} ({name}) started the bot.")


# ── /myplan handler ───────────────────────────────────────────

async def cmd_myplan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle the /myplan command.
    Shows the user's current premium plan status with expiry info.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    user_id = update.effective_user.id
    ctx     = db.get_full_user_context(user_id)
    text    = _build_status_text(ctx)

    await update.message.reply_html(
        text,
        reply_markup=status_menu(),
        disable_web_page_preview=True,
    )


# ── /status handler ───────────────────────────────────────────

async def cmd_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle the /status command.
    Mirrors /myplan — shows full account status.

    Parameters
    ----------
    update  : Update
    context : ContextTypes.DEFAULT_TYPE
    """
    await cmd_myplan(update, context)


# ── Callback Query handlers ───────────────────────────────────

async def cb_menu_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='menu:back'.
    Returns the user to the main menu message.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    name    = query.from_user.full_name

    await query.answer()
    states.clear_all(user_id)

    welcome_text = _build_welcome(user_id, name)
    await query.edit_message_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu(),
        disable_web_page_preview=True,
    )


async def cb_menu_scrape(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='menu:scrape'.
    Route to the scrape sub-menu or prompt session setup if none exists.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    has_sess = db.has_session(user_id)

    if not has_sess:
        text = (
            f"<b>⧩ {sc('Session Required')} ⧩</b>\n\n"
            f"{sc('You need to connect a Telegram account (session)')}\n"
            f"{sc('before you can scrape members.')}\n\n"
            f"<b>{sc('Setup your session now:')}</b>"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=session_menu(has_session=False),
        )
        return

    text = (
        f"<b>⟢ {sc('Scraper Engine')} ⟢</b>\n\n"
        f"{sc('Extract every member from any public group.')}\n\n"
        f"▸ <b>{sc('Free tier')}</b>: {config.FREE_SCRAPE_LIMIT} {sc('members')}\n"
        f"▸ <b>{sc('Premium')}</b>: {sc('unlimited')}\n\n"
        f"<b>{sc('Tap Start Scrape and send the group link.')}</b>"
    )
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=scrape_menu(),
    )


async def cb_menu_add(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='menu:add'.
    Route to the add-members sub-menu or prompt session setup.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    has_sess = db.has_session(user_id)

    if not has_sess:
        text = (
            f"<b>⧩ {sc('Session Required')} ⧩</b>\n\n"
            f"{sc('You need a connected session to add members.')}\n\n"
            f"<b>{sc('Setup your session now:')}</b>"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=session_menu(has_session=False),
        )
        return

    text = (
        f"<b>✦ {sc('Member Injector')} ✦</b>\n\n"
        f"{sc('Inject members from a scraped CSV into your group.')}\n\n"
        f"▸ <b>{sc('Free tier')}</b>: {config.FREE_ADD_LIMIT} {sc('members')}\n"
        f"▸ <b>{sc('Premium')}</b>: {sc('unlimited')}\n"
        f"▸ <b>{sc('Delay')}</b>: {config.ADD_DELAY_SECONDS}s {sc('per member')}\n\n"
        f"<b>{sc('Tap Start Adding to proceed.')}</b>"
    )
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=add_menu(),
    )


async def cb_menu_premium(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='menu:premium'.
    Show the premium info/upgrade menu.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    is_prem = db.is_premium(user_id)
    is_owner = (user_id == config.OWNER_ID)
    await query.answer()

    if is_prem:
        info = db.get_premium_info(user_id)
        text = (
            f"<b>★ {sc('Premium Active')} ★</b>\n\n"
            f"⭐ <b>{sc('Plan')}:</b> {sc(info['plan'])}\n"
            f"📅 <b>{sc('Expires')}:</b> <code>{info['expires_at']}</code>\n\n"
            f"{sc('All limits are removed. Enjoy the elite access.')}"
        )
    else:
        text = (
            f"<b>★ {sc('Velyn Nox Premium')} ★</b>\n\n"
            f"{sc('Unlock the full power of the scraper & adder.')}\n\n"
            f"<b>{sc('Premium Benefits')}:</b>\n"
            f"▸ {sc('Unlimited member scraping')}\n"
            f"▸ {sc('Unlimited member adding')}\n"
            f"▸ {sc('Priority support')}\n"
            f"▸ {sc('Early access to new features')}\n\n"
            f"<b>{sc('Contact the owner to purchase:')}</b> "
            f"<a href='tg://user?id={config.OWNER_ID}'>{sc('Owner')}</a>"
        )

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=premium_menu(is_owner=is_owner),
        disable_web_page_preview=True,
    )


async def cb_premium_myplan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='premium:myplan'.
    Show plan details inline.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    ctx  = db.get_full_user_context(user_id)
    text = _build_status_text(ctx)

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=status_menu(),
        disable_web_page_preview=True,
    )


async def cb_status_refresh(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='status:refresh'.
    Re-builds and re-sends the status block.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer(sc("refreshed"), show_alert=False)

    ctx  = db.get_full_user_context(user_id)
    text = _build_status_text(ctx)

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=status_menu(),
    )


async def cb_op_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle callback_data='op:cancel'.
    Set the cancel flag so the engine loop stops after the current iteration.
    """
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer(sc("cancelling..."), show_alert=False)
    states.request_cancel(user_id)
    await query.edit_message_text(
        f"⛔ <b>{sc('Operation cancellation requested.')}</b>\n"
        f"{sc('It will stop after the current step.')}",
        parse_mode=ParseMode.HTML,
    )


# ── Handler Registration ──────────────────────────────────────

def register(app: Application) -> None:
    """
    Attach all start.py handlers to the Application instance.

    Parameters
    ----------
    app : Application — The running PTB Application.
    """
    # Commands
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("myplan", cmd_myplan))
    app.add_handler(CommandHandler("status", cmd_status))

    # Callback queries
    app.add_handler(CallbackQueryHandler(cb_menu_back,       pattern="^menu:back$"))
    app.add_handler(CallbackQueryHandler(cb_menu_scrape,     pattern="^menu:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_menu_add,        pattern="^menu:add$"))
    app.add_handler(CallbackQueryHandler(cb_menu_premium,    pattern="^menu:premium$"))
    app.add_handler(CallbackQueryHandler(cb_premium_myplan,  pattern="^premium:myplan$"))
    app.add_handler(CallbackQueryHandler(cb_status_refresh,  pattern="^status:refresh$"))
    app.add_handler(CallbackQueryHandler(cb_op_cancel,       pattern="^op:cancel$"))
