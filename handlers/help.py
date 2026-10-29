from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from keyboards.menus import help_menu, back_btn
from utils.text import sc
from handlers.start import safe_edit_media, safe_edit

async def cb_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>❓ {sc('ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ ʜᴇʟᴘ ᴄᴇɴᴛᴇʀ')}</b>\n\n"
        f"{sc('ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ʜᴇʟᴘ ᴍᴇɴᴜ. ᴄʜᴏᴏꜱᴇ ᴀ ɢᴜɪᴅᴇ ʙᴇʟᴏᴡ ᴛᴏ ʟᴇᴀʀɴ.')}\n\n"
        f"<b>⧩ {sc('ᴀᴠᴀɪʟᴀʙʟᴇ ɢᴜɪᴅᴇꜱ')} ⧩</b>"
    )
    await safe_edit_media(q, text, "HELP CENTER", help_menu(), use_static=True)

async def cb_help_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    text = (
        f"<b>🔑 {sc('ʜᴏᴡ ᴛᴏ ɢᴇᴛ ᴀᴘɪ ɪᴅ & ʜᴀꜱʜ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>1.</b> {sc('ɢᴏ ᴛᴏ')} <code>my.telegram.org</code>\n"
        f"<b>2.</b> {sc('ʟᴏɢɪɴ ᴡɪᴛʜ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ.')}\n"
        f"<b>3.</b> {sc('ᴄʟɪᴄᴋ ᴏɴ')} <b>API development tools</b>.\n"
        f"<b>4.</b> {sc('ᴄʀᴇᴀᴛᴇ ᴀ ɴᴇᴡ ᴀᴘᴘ.')}\n"
        f"<b>5.</b> {sc('ᴄᴏᴘʏ ʏᴏᴜʀ')} <b>App api_id</b> {sc('ᴀɴᴅ')} <b>App api_hash</b>.\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"⚠️ <i>{sc('ᴋᴇᴇᴘ ᴛʜᴇꜱᴇ ᴄᴏᴅᴇꜱ ꜱᴀꜰᴇ.')}</i>"
    )
    await safe_edit(q, text, back_btn())

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
    await safe_edit(q, text, back_btn())

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
        f"⚠️ <i>{sc('ʙᴏᴛ ᴀᴅᴅꜱ ᴍᴇᴍʙᴇʀꜱ ᴡɪᴛʜ ᴀ 10ꜱᴇᴄ ᴅᴇʟᴀʏ.')}</i>"
    )
    await safe_edit(q, text, back_btn())

def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(cb_help_menu, pattern="^menu:help$"))
    app.add_handler(CallbackQueryHandler(cb_help_api, pattern="^help:api$"))
    app.add_handler(CallbackQueryHandler(cb_help_scrape, pattern="^help:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_help_add, pattern="^help:add$"))
