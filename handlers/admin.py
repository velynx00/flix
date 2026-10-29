from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import config
from keyboards.menus import admin_panel
from utils.text import sc
from handlers.start import safe_edit

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != config.OWNER_ID: return
    text = f"<b>🛡 {sc('ᴠᴇʟʏɴ ɴᴏx ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ')}</b>"
    await update.message.reply_html(text, reply_markup=admin_panel())

async def cb_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID: return
    text = f"<b>🛡 {sc('ᴠᴇʟʏɴ ɴᴏx ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ')}</b>"
    await safe_edit(q, text, admin_panel())

async def cb_admin_addapi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID: return
    context.user_data['waiting_for'] = 'api_id'
    text = f"<b>{sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}</b>\n\n<b>{sc('ꜱᴛᴇᴘ 1/3: ᴇɴᴛᴇʀ ᴀᴘɪ ɪᴅ')}</b>"
    await safe_edit(q, text)

def register(app: Application) -> None:
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(cb_admin_panel, pattern="^admin:panel$"))
    app.add_handler(CallbackQueryHandler(cb_admin_addapi, pattern="^admin:addapi$"))
