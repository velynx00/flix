import io, logging
from typing import Optional
from telegram import Update, InputFile, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import config
import database.db as db
from keyboards.menus import main_menu, premium_menu, scrape_menu, add_menu, back_btn
from utils.banner import generate_banner
from utils.text import sc, escape_html
from handlers import states

logger = logging.getLogger(__name__)

# FIXED: Smooth Media Edit (No delete, no wait)
async def safe_edit_media(q, text, title, reply_markup=None):
    dp_bytes = None
    try:
        photos = await q.get_bot().get_user_profile_photos(q.from_user.id, limit=1)
        if photos.total_count:
            f = await q.get_bot().get_file(photos.photos[0][-1].file_id)
            buf = io.BytesIO()
            await f.download_to_memory(buf)
            dp_bytes = buf.getvalue()
    except: pass
    
    banner = generate_banner(dp_bytes, title=title)
    media = InputMediaPhoto(media=InputFile(banner, filename="menu_banner.png"), caption=text, parse_mode=ParseMode.HTML)
    
    try:
        # Ye purane message ko hi naye photo me badal dega bina delete kiye
        await q.edit_message_media(media=media, reply_markup=reply_markup)
    except Exception as e:
        logger.warning(f"Media edit error: {e}")
        try:
            await q.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except: pass

def _build_welcome(user_id: int, user_name: str) -> str:
    return (
        f"<blockquote>🕷️ <b>{sc('ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ')}</b></blockquote>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"👋 <b>Hey</b> <a href='tg://user?id={user_id}'><b>{escape_html(user_name)}</b></a><b>!</b>\n"
        f"⚡ <b>{sc('ᴛʜᴇ ᴜʟᴛɪᴍᴀᴛᴇ ᴛᴇʟᴇɢʀᴀᴍ ꜱᴄʀᴀᴘᴇʀ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1️⃣ {sc('ꜱᴄʀᴀᴘᴇ ᴍᴇᴍʙᴇʀꜱ')}</b>\n"
        f"<b>2️⃣ {sc('ᴀᴅᴅ ᴍᴇᴍʙᴇʀꜱ')}</b>\n"
        f"<b>3️⃣ {sc('ᴄʜᴇᴄᴋ ꜱᴛᴀᴛᴜꜱ')} : <code>/myplan</code></b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🛡 <b>{sc('ꜱᴇᴄᴜʀᴇ & ᴇɴᴄʀʏᴘᴛᴇᴅ')}</b>\n"
        f"🚀 <b>{sc('ᴘᴏᴡᴇʀᴇᴅ ʙʏ ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ')}</b>"
    )

async def _fetch_user_dp(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> Optional[bytes]:
    try:
        photos = await context.bot.get_user_profile_photos(user_id=user_id, limit=1)
        if photos.total_count == 0: return None
        file_id = photos.photos[0][-1].file_id
        tg_file = await context.bot.get_file(file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        return buf.getvalue()
    except: return None

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.upsert_user(user.id, user.username, user.full_name)
    states.clear_all(user.id)

    dp_bytes = await _fetch_user_dp(context, user.id)
    welcome_text = _build_welcome(user.id, user.full_name)

    try:
        banner = generate_banner(dp_bytes, title="SYSTEM OVERRIDE")
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=InputFile(banner, filename="velyn_nox.png"),
            has_spoiler=True,
            caption=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(),
        )
    except Exception as e:
        logger.error(f"Banner error: {e}")
        await update.message.reply_html(welcome_text, reply_markup=main_menu())

async def cmd_myplan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💎 <b>Owner Plan: Lifetime</b>", parse_mode=ParseMode.HTML, reply_markup=back_btn())

async def cb_menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    states.clear_all(q.from_user.id)
    await safe_edit_media(q, _build_welcome(q.from_user.id, q.from_user.full_name), "SYSTEM OVERRIDE", main_menu())

async def cb_menu_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    is_owner = (q.from_user.id == config.OWNER_ID)
    
    text = (
        f"<b>💎 {sc('ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ ᴘʀᴇᴍɪᴜᴍ')} 💎</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🔥 <b>{sc('ᴜɴʟᴏᴄᴋ ᴛʜᴇ ᴜʟᴛɪᴍᴀᴛᴇ ᴘᴏᴡᴇʀ')}</b>\n\n"
        f"<b>{sc('ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛꜱ')}:</b>\n"
        f"▸ {sc('ᴜɴʟɪᴍɪᴛᴇᴅ ꜱᴄʀᴀᴘɪɴɢ')}\n"
        f"▸ {sc('ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴅᴅɪɴɢ')}\n"
        f"▸ {sc('ɴᴏ ᴅᴀɪʟʏ ʟɪᴍɪᴛꜱ')}\n"
        f"▸ {sc('ᴘʀɪᴏʀɪᴛʏ ꜱᴜᴘᴘᴏʀᴛ')}\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🛒 <b>{sc('ᴛᴏ ᴘᴜʀᴄʜᴀꜱᴇ, ᴄᴏɴᴛᴀᴄᴛ')}:</b> <a href='https://t.me/Velynx007'><b>@Velynx007</b></a>"
    )
    await safe_edit_media(q, text, "PREMIUM ACCESS", premium_menu(is_owner))

def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("myplan", cmd_myplan))
    app.add_handler(CallbackQueryHandler(cb_menu_back, pattern="^menu:back$"))
    app.add_handler(CallbackQueryHandler(cb_menu_premium, pattern="^menu:premium$"))
