from __future__ import annotations

import io
import logging
from typing import Optional

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import config
import database.db as db
from keyboards.menus import main_menu, premium_menu, scrape_menu, add_menu, session_menu, status_menu, back_btn
from utils.banner import generate_banner
from utils.text import sc, escape_html
from handlers import states

logger = logging.getLogger(__name__)

# FIX: Smart Edit Function (Photo ya Text dono handle karega)
async def safe_edit(query, text, reply_markup=None):
    try:
        if query.message.photo or query.message.document:
            await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup, disable_web_page_preview=True)
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"Edit error: {e}")

def _build_welcome(user_id: int, user_name: str) -> str:
    return (
        f"<blockquote>🕷️ <b>{sc('ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴠᴇʟʏɴ ɴᴏx')}</b></blockquote>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"👋 <b>Hey</b> <a href='tg://user?id={user_id}'><b>{escape_html(user_name)}</b></a><b>!</b>\n"
        f"⚡ <b>{sc('ᴛʜᴇ ᴜʟᴛɪᴍᴀᴛᴇ ᴛᴇʟᴇɢʀᴀᴍ ꜱᴄʀᴀᴘᴇʀ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1️⃣ {sc('ꜱᴄʀᴀᴘᴇ ᴍᴇᴍʙᴇʀꜱ')}</b>\n"
        f"<b>2️⃣ {sc('ᴀᴅᴅ ᴍᴇᴍʙᴇʀꜱ')}</b>\n"
        f"<b>3️⃣ {sc('ᴄʜᴇᴄᴋ ꜱᴛᴀᴛᴜꜱ')} : <code>/myplan</code></b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🛡 <b>{sc('ꜱᴇᴄᴜʀᴇ & ᴇɴᴄʀʏᴘᴛᴇᴅ')}</b>\n"
        f"🚀 <b>{sc('ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴠᴇʟʏɴ ɴᴏx')}</b>"
    )

def _build_status_text(ctx: dict) -> str:
    user       = ctx["user"]
    prem       = ctx["is_premium"]
    prem_info  = ctx["premium_info"]
    has_sess   = ctx["has_session"]
    recent_ops = ctx["recent_ops"]

    lines = [
        f"<b>⧩ {sc('Account Status')} ⧩</b>\n",
        f"👤 <b>{sc('User')}:</b> {escape_html(user['full_name'])}",
        f"🆔 <b>{sc('ID')}:</b> <code>{user['user_id']}</code>",
        "",
    ]

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

    sess_label = sc("active") if has_sess else sc("not configured")
    lines += [
        f"🔑 <b>{sc('Session')}:</b> {sess_label}",
        "",
    ]

    lines += [
        f"📤 <b>{sc('Total Scrapes')}:</b> {user['total_scrapes']}",
        f"📥 <b>{sc('Total Adds')}:</b> {user['total_adds']}",
        "",
    ]

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


async def _fetch_user_dp(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> Optional[bytes]:
    try:
        photos = await context.bot.get_user_profile_photos(user_id=user_id, limit=1)
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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user     = update.effective_user
    chat     = update.effective_chat
    user_id  = user.id
    username = user.username
    name     = user.full_name

    db.upsert_user(user_id, username, name)
    states.clear_all(user_id)

    dp_bytes = await _fetch_user_dp(context, user_id)
    try:
        banner_path = generate_banner(dp_bytes)
    except Exception as exc:
        logger.error(f"[START] Banner generation failed: {exc}")
        banner_path = None

    welcome_text = _build_welcome(user_id, name)

    if banner_path:
        try:
            with open(banner_path, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat.id,
                    photo=InputFile(f, filename="velyn_nox.png"),
                    has_spoiler=True,
                    caption=welcome_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=main_menu(),
                )
        except Exception as exc:
            logger.warning(f"[START] Could not send banner: {exc}")
            await update.message.reply_html(welcome_text, reply_markup=main_menu(), disable_web_page_preview=True)
    else:
        await update.message.reply_html(welcome_text, reply_markup=main_menu(), disable_web_page_preview=True)


async def cmd_myplan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    ctx     = db.get_full_user_context(user_id)
    text    = _build_status_text(ctx)

    await update.message.reply_html(text, reply_markup=status_menu(), disable_web_page_preview=True)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_myplan(update, context)


async def cb_menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    user_id = query.from_user.id
    name    = query.from_user.full_name

    await query.answer()
    states.clear_all(user_id)
    await safe_edit(query, _build_welcome(user_id, name), main_menu())


async def cb_menu_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        await safe_edit(query, text, session_menu(has_session=False))
        return

    text = (
        f"<b>⟢ {sc('Scraper Engine')} ⟢</b>\n\n"
        f"{sc('Extract every member from any public group.')}\n\n"
        f"▸ <b>{sc('Free tier')}</b>: {config.FREE_SCRAPE_LIMIT} {sc('members')}\n"
        f"▸ <b>{sc('Premium')}</b>: {sc('unlimited')}\n\n"
        f"<b>{sc('Tap Start Scrape and send the group link.')}</b>"
    )
    await safe_edit(query, text, scrape_menu())


async def cb_menu_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        await safe_edit(query, text, session_menu(has_session=False))
        return

    text = (
        f"<b>✦ {sc('Member Injector')} ✦</b>\n\n"
        f"{sc('Inject members from a scraped CSV into your group.')}\n\n"
        f"▸ <b>{sc('Free tier')}</b>: {config.FREE_ADD_LIMIT} {sc('members')}\n"
        f"▸ <b>{sc('Premium')}</b>: {sc('unlimited')}\n"
        f"▸ <b>{sc('Delay')}</b>: {config.ADD_DELAY_SECONDS}s {sc('per member')}\n\n"
        f"<b>{sc('Tap Start Adding to proceed.')}</b>"
    )
    await safe_edit(query, text, add_menu())


async def cb_scrape_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'scrape'
    context.user_data['waiting_for'] = 'target'
    text = (
        f"<b>{sc('ᴇxᴛʀᴀᴄᴛɪᴏɴ ᴘʀᴏᴛᴏᴄᴏʟ')}</b>\n\n"
        f"<b>{sc('ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ɢʀᴏᴜᴘ ʟɪɴᴋ ᴏʀ ᴜꜱᴇʀɴᴀᴍᴇ ʙᴇʟᴏᴡ.')}</b>"
    )
    await safe_edit(query, text, back_btn())


async def cb_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'add'
    context.user_data['waiting_for'] = 'target'
    text = (
        f"<b>{sc('ɪɴᴊᴇᴄᴛɪᴏɴ ᴘʀᴏᴛᴏᴄᴏʟ')}</b>\n\n"
        f"<b>{sc('ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ɢʀᴏᴜᴘ ʟɪɴᴋ ᴏʀ ᴜꜱᴇʀɴᴀᴍᴇ ʙᴇʟᴏᴡ.')}</b>"
    )
    await safe_edit(query, text, back_btn())


async def cb_menu_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    await safe_edit(query, text, premium_menu(is_owner=is_owner))


async def cb_premium_myplan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    ctx  = db.get_full_user_context(user_id)
    text = _build_status_text(ctx)
    await safe_edit(query, text, status_menu())


async def cb_status_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer(sc("refreshed"), show_alert=False)

    ctx  = db.get_full_user_context(user_id)
    text = _build_status_text(ctx)
    await safe_edit(query, text, status_menu())


async def cb_op_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    user_id = query.from_user.id
    await query.answer(sc("cancelling..."), show_alert=False)
    states.request_cancel(user_id)
    text = (
        f"⛔ <b>{sc('Operation cancellation requested.')}</b>\n"
        f"{sc('It will stop after the current step.')}"
    )
    await safe_edit(query, text)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("myplan", cmd_myplan))
    app.add_handler(CommandHandler("status", cmd_status))

    app.add_handler(CallbackQueryHandler(cb_menu_back,       pattern="^menu:back$"))
    app.add_handler(CallbackQueryHandler(cb_menu_scrape,     pattern="^menu:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_menu_add,        pattern="^menu:add$"))
    app.add_handler(CallbackQueryHandler(cb_scrape_start,    pattern="^scrape:start$"))
    app.add_handler(CallbackQueryHandler(cb_add_start,       pattern="^add:start$"))
    app.add_handler(CallbackQueryHandler(cb_menu_premium,    pattern="^menu:premium$"))
    app.add_handler(CallbackQueryHandler(cb_premium_myplan,  pattern="^premium:myplan$"))
    app.add_handler(CallbackQueryHandler(cb_status_refresh,  pattern="^status:refresh$"))
    app.add_handler(CallbackQueryHandler(cb_op_cancel,       pattern="^op:cancel$"))