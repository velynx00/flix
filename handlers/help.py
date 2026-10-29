from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from keyboards.menus import help_menu, back_btn
from utils.text import sc
import io
from utils.banner import generate_banner
from telegram import InputFile

async def _send_new_banner(q, text, title, reply_markup):
    try: await q.message.delete()
    except: pass
    
    dp_bytes = None
    try:
        photos = await q.get_bot().get_user_profile_photos(q.from_user.id, limit=1)
        if photos.total_count:
            f = await q.get_bot().get_file(photos.photos[0][-1].file_id)
            buf = io.BytesIO()
            await f.download_to_memory(buf)
            dp_bytes = buf.getvalue()
    except: pass
    
    banner = await generate_banner(dp_bytes, title=title)
    await q.get_bot().send_photo(
        chat_id=q.message.chat_id,
        photo=InputFile(banner, filename="help_banner.png"),
        caption=text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
        has_spoiler=True
    )

async def cb_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>❓ {sc('ᴠᴇʟʏɴ ɴᴏx ʜᴇʟᴘ ᴄᴇɴᴛᴇʀ')}</b>\n\n"
        f"{sc('ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ʜᴇʟᴘ ᴍᴇɴᴜ. ᴄʜᴏᴏꜱᴇ ᴀ ɢᴜɪᴅᴇ ʙᴇʟᴏᴡ ᴛᴏ ʟᴇᴀʀɴ.')}\n\n"
        f"<b>⧩ {sc('ᴀᴠᴀɪʟᴀʙʟᴇ ɢᴜɪᴅᴇꜱ')} ⧩</b>"
    )
    await _send_new_banner(q, text, "HELP CENTER", help_menu())

async def cb_help_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>🔑 {sc('ʜᴏᴡ ᴛᴏ ɢᴇᴛ ᴀᴘɪ ɪᴅ & ʜᴀꜱʜ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1.</b> {sc('ɢᴏ ᴛᴏ')} <code>my.telegram.org</code>\n"
        f"<b>2.</b> {sc('ʟᴏɢɪɴ ᴡɪᴛʜ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ.')}\n"
        f"<b>3.</b> {sc('ᴄʟɪᴄᴋ ᴏɴ')} <b>API development tools</b>.\n"
        f"<b>4.</b> {sc('ᴄʀᴇᴀᴛᴇ ᴀ ɴᴇᴡ ᴀᴘᴘ (ɴᴀᴍᴇ ᴄᴀɴ ʙᴇ ᴀɴʏᴛʜɪɴɢ).')}\n"
        f"<b>5.</b> {sc('ᴄᴏᴘʏ ʏᴏᴜʀ')} <b>App api_id</b> {sc('ᴀɴᴅ')} <b>App api_hash</b>.\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"⚠️ <i>{sc('ᴋᴇᴇᴘ ᴛʜᴇꜱᴇ ᴄᴏᴅᴇꜱ ꜱᴀꜰᴇ. ᴅᴏ ɴᴏᴛ ꜱʜᴀʀᴇ ᴛʜᴇᴍ.')}</i>"
    )
    await _send_new_banner(q, text, "API GENERATION", back_btn())

async def cb_help_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>📥 {sc('ꜱᴄʀᴀᴘɪɴɢ ɢᴜɪᴅᴇ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1.</b> {sc('ᴘʀᴇꜱꜱ')} <b>{sc('ꜱᴄʀᴀᴘᴇ')}</b> {sc('ʙᴜᴛᴛᴏɴ.')}\n"
        f"<b>2.</b> {sc('ꜱᴇɴᴅ ᴛʜᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ')} (e.g. <code>@publicgroup</code>).\n"
        f"<b>3.</b> {sc('ᴇɴᴛᴇʀ ᴛʜᴇ ʟɪᴍɪᴛ')} (1-50).\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<i>{sc('ɴᴏᴛᴇ: ɪꜰ ɴᴏ ᴀᴘɪ ɪꜱ ᴀᴅᴅᴇᴅ, ᴀꜱᴋ ᴏᴡɴᴇʀ.')}</i>"
    )
    await _send_new_banner(q, text, "SCRAPER ENGINE", back_btn())

async def cb_help_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>📤 {sc('ᴀᴅᴅɪɴɢ ɢᴜɪᴅᴇ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1.</b> {sc('ᴘʀᴇꜱꜱ')} <b>{sc('ᴀᴅᴅ')}</b> {sc('ʙᴜᴛᴛᴏɴ.')}\n"
        f"<b>2.</b> {sc('ꜱᴇɴᴅ ᴛʜᴇ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ.')}\n"
        f"<b>3.</b> {sc('ᴇɴᴛᴇʀ ʟɪᴍɪᴛ')} (1-50).\n"
        f"<b>4.</b> {sc('ꜱᴇɴᴅ ᴛʜᴇ ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ')} ({sc('ʏᴏᴜ ᴍᴜꜱᴛ ʙᴇ ᴀᴅᴍɪɴ')}).\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"⚠️ <i>{sc('ʙᴏᴛ ᴀᴅᴅꜱ ᴍᴇᴍʙᴇʀꜱ ᴡɪᴛʜ ᴀ 10ꜱᴇᴄ ᴅᴇʟᴀʏ ᴛᴏ ᴀᴠᴏɪᴅ ʙᴀɴ.')}</i>"
    )
    await _send_new_banner(q, text, "ADDER ENGINE", back_btn())

def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(cb_help_menu, pattern="^menu:help$"))
    app.add_handler(CallbackQueryHandler(cb_help_api, pattern="^help:api$"))
    app.add_handler(CallbackQueryHandler(cb_help_scrape, pattern="^help:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_help_add, pattern="^help:add$"))
