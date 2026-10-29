import io, asyncio, logging
from typing import Optional
from telegram import Update, InputFile, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import config
from database.db import db
from keyboards.menus import main_menu, premium_menu, back_btn
from utils.banner import generate_banner, generate_static_banner
from utils.text import sc, escape_html, BOOT_FRAMES

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  SAFE EDIT HELPERS
# ──────────────────────────────────────────────

async def safe_edit_media(q, text, title, reply_markup=None, use_static=False):
    if use_static:
        banner = generate_static_banner(title)
    else:
        dp_bytes = None
        try:
            photos = await q.get_bot().get_user_profile_photos(q.from_user.id, limit=1)
            if photos.total_count:
                f   = await q.get_bot().get_file(photos.photos[0][-1].file_id)
                buf = io.BytesIO()
                await f.download_to_memory(buf)
                dp_bytes = buf.getvalue()
        except: pass
        banner = generate_banner(dp_bytes, title)

    media = InputMediaPhoto(
        media=InputFile(banner, filename="menu_banner.png"),
        caption=text, parse_mode=ParseMode.HTML
    )
    try:
        await q.edit_message_media(media=media, reply_markup=reply_markup)
    except Exception as e:
        logger.warning(f"Media edit error: {e}")
        try: await q.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except: pass

async def safe_edit(query, text, reply_markup=None):
    try:
        if query.message.photo:
            await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"Edit error: {e}")

# ──────────────────────────────────────────────
#  TEXT BUILDERS
# ──────────────────────────────────────────────

def _build_welcome(user_id: int, user_name: str) -> str:
    return (
        f"<blockquote>"
        f"🕷️  <b>{sc('ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ')}  ·  {sc('ᴀᴅᴠᴀɴᴄᴇᴅ ꜱʏꜱᴛᴇᴍ')}</b>"
        f"</blockquote>\n"
        f"<b>╔══════════════════════╗</b>\n"
        f"<b>  👋 {sc('ʜᴇʏ')}, <a href='tg://user?id={user_id}'>{escape_html(user_name)}</a></b>\n"
        f"<b>  ⚡ {sc('ᴛʜᴇ ᴜʟᴛɪᴍᴀᴛᴇ ꜱᴄʀᴀᴘᴇʀ ✦ ᴀᴅᴅᴇʀ')}</b>\n"
        f"<b>╚══════════════════════╝</b>\n\n"
        f"<b>▸ {sc('ꜱᴄʀᴀᴘᴇ ᴍᴇᴍʙᴇʀꜱ')}</b>  <i>→ extract active users</i>\n"
        f"<b>▸ {sc('ᴀᴅᴅ ᴍᴇᴍʙᴇʀꜱ')}</b>     <i>→ inject to your group</i>\n"
        f"<b>▸ {sc('ᴜᴘʟᴏᴀᴅ ᴄꜱᴠ')}</b>      <i>→ add from file</i>\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🛡 <b>{sc('ꜱᴇᴄᴜʀᴇ')}  ·  {sc('ᴇɴᴄʀʏᴘᴛᴇᴅ')}  ·  {sc('ᴘʀɪᴠᴀᴛᴇ')}</b>\n"
        f"<code>/myplan</code>  <b>→ check your plan</b>"
    )

def _build_boot_frame(frame_idx: int, user_name: str) -> str:
    bar = BOOT_FRAMES[frame_idx]
    if frame_idx < len(BOOT_FRAMES) - 1:
        status = sc("ɪɴɪᴛɪᴀʟɪᴢɪɴɢ...")
    else:
        status = sc("ꜱʏꜱᴛᴇᴍ ʀᴇᴀᴅʏ ✓")
    return (
        f"<b>{sc('ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ')} — {sc('ʙᴏᴏᴛ ꜱᴇǫᴜᴇɴᴄᴇ')}</b>\n\n"
        f"{bar}\n\n"
        f"<b>{status}</b>"
    )

# ──────────────────────────────────────────────
#  DP FETCH
# ──────────────────────────────────────────────

async def _fetch_user_dp(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> Optional[bytes]:
    try:
        photos = await context.bot.get_user_profile_photos(user_id=user_id, limit=1)
        if photos.total_count == 0: return None
        tg_file = await context.bot.get_file(photos.photos[0][-1].file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        return buf.getvalue()
    except: return None

# ──────────────────────────────────────────────
#  /start — ANIMATED BOOT → WELCOME
# ──────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers import states
    user = update.effective_user
    db.upsert_user(user.id, user.username, user.full_name)
    states.clear_all(user.id)

    # Step 1 — send initial boot frame (plain text, fast)
    boot_msg = await update.message.reply_html(
        _build_boot_frame(0, user.full_name)
    )

    # Step 2 — animate the boot bar (frames 1-10) while fetching DP
    dp_task = asyncio.create_task(_fetch_user_dp(context, user.id))

    for i in range(1, len(BOOT_FRAMES)):
        await asyncio.sleep(0.22)
        try:
            await boot_msg.edit_text(
                _build_boot_frame(i, user.full_name),
                parse_mode=ParseMode.HTML
            )
        except: pass

    dp_bytes = await dp_task

    # Step 3 — replace boot message with banner + welcome
    welcome_text = _build_welcome(user.id, user.full_name)
    try:
        banner = generate_banner(dp_bytes, title="SYSTEM OVERRIDE")
        await boot_msg.delete()
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=InputFile(banner, filename="velyn_nox.png"),
            has_spoiler=False,
            caption=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(),
        )
    except Exception as e:
        logger.error(f"Banner error: {e}")
        try: await boot_msg.edit_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=main_menu())
        except: await update.message.reply_html(welcome_text, reply_markup=main_menu())

# ──────────────────────────────────────────────
#  /myplan
# ──────────────────────────────────────────────

async def cmd_myplan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if uid == config.OWNER_ID:
        plan_line = f"👑 <b>{sc('ᴏᴡɴᴇʀ ᴘʟᴀɴ')} — {sc('ʟɪꜰᴇᴛɪᴍᴇ')}</b>"
    elif db.is_premium(uid):
        plan_line = f"💎 <b>{sc('ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ')} — {sc('ᴀᴄᴛɪᴠᴇ')}</b>"
    else:
        plan_line = f"🔓 <b>{sc('ꜰʀᴇᴇ ᴘʟᴀɴ')} — {sc('ᴜᴘɢʀᴀᴅᴇ ᴀᴠᴀɪʟᴀʙʟᴇ')}</b>"

    text = (
        f"<b>╔═══════════════════╗</b>\n"
        f"<b>   📊 {sc('ʏᴏᴜʀ ᴘʟᴀɴ ꜱᴛᴀᴛᴜꜱ')}</b>\n"
        f"<b>╚═══════════════════╝</b>\n\n"
        f"{plan_line}\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"💬 {sc('ᴄᴏɴᴛᴀᴄᴛ')} <a href='https://t.me/Velynx007'>@Velynx007</a> {sc('ᴛᴏ ᴜᴘɢʀᴀᴅᴇ.')}"
    )
    await update.message.reply_html(text, reply_markup=back_btn())

# ──────────────────────────────────────────────
#  CALLBACK HANDLERS
# ──────────────────────────────────────────────

async def cb_menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers import states
    q = update.callback_query
    await q.answer()
    states.clear_all(q.from_user.id)
    await safe_edit_media(
        q,
        _build_welcome(q.from_user.id, q.from_user.full_name),
        "SYSTEM OVERRIDE",
        main_menu(),
        use_static=False
    )

async def cb_menu_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    is_owner = (q.from_user.id == config.OWNER_ID)
    uid      = q.from_user.id
    is_prem  = db.is_premium(uid)

    if is_owner:
        badge = f"👑 {sc('ᴏᴡɴᴇʀ — ʟɪꜰᴇᴛɪᴍᴇ')}"
    elif is_prem:
        badge = f"💎 {sc('ᴘʀᴇᴍɪᴜᴍ — ᴀᴄᴛɪᴠᴇ')}"
    else:
        badge = f"🔓 {sc('ꜰʀᴇᴇ — ᴜᴘɢʀᴀᴅᴇ ᴀᴠᴀɪʟᴀʙʟᴇ')}"

    text = (
        f"<b>💎 {sc('ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ ᴘʀᴇᴍɪᴜᴍ')} 💎</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>{sc('ʏᴏᴜʀ ꜱᴛᴀᴛᴜꜱ')}:</b> {badge}\n\n"
        f"<b>{sc('ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛꜱ')}</b>\n"
        f"▸ ♾️  {sc('ᴜɴʟɪᴍɪᴛᴇᴅ ꜱᴄʀᴀᴘɪɴɢ')}\n"
        f"▸ ♾️  {sc('ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴅᴅɪɴɢ')}\n"
        f"▸ ⚡  {sc('ɴᴏ ᴅᴀɪʟʏ ʟɪᴍɪᴛꜱ')}\n"
        f"▸ 🔑  {sc('ᴍᴜʟᴛɪ-ꜱᴇꜱꜱɪᴏɴ ꜱᴜᴘᴘᴏʀᴛ')}\n"
        f"▸ 🎯  {sc('ᴘʀɪᴏʀɪᴛʏ ꜱᴜᴘᴘᴏʀᴛ')}\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🛒 <b>{sc('ᴄᴏɴᴛᴀᴄᴛ')}:</b> <a href='https://t.me/Velynx007'>@Velynx007</a>"
    )
    await safe_edit_media(q, text, "PREMIUM ACCESS", premium_menu(is_owner), use_static=True)

async def cb_setup_api(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers import states
    q = update.callback_query
    await q.answer()
    states.clear_all(q.from_user.id)
    context.user_data['waiting_for'] = 'api_id'
    text = (
        f"<b>🔑 {sc('ꜱᴇꜱꜱɪᴏɴ ꜱᴇᴛᴜᴘ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"<b>{sc('ꜱᴛᴇᴘ')} 1/3 ▸</b> {sc('ᴇɴᴛᴇʀ ᴀᴘɪ ɪᴅ')}\n\n"
        f"<i>Get it from my.telegram.org → API development tools</i>"
    )
    await safe_edit(q, text, back_btn())

def register(app: Application) -> None:
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("myplan",  cmd_myplan))
    app.add_handler(CallbackQueryHandler(cb_menu_back,    pattern="^menu:back$"))
    app.add_handler(CallbackQueryHandler(cb_menu_premium, pattern="^menu:premium$"))
    app.add_handler(CallbackQueryHandler(cb_setup_api,    pattern="^setup:api$"))
