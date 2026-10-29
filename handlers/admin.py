import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import config
from database.db import db
from keyboards.menus import admin_panel
from utils.text import sc

logger = logging.getLogger(__name__)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != config.OWNER_ID:
        return
    text = (
        f"<b>🛡 {sc('ᴠᴇʟʏɴ ɴᴏx ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ')}</b>\n\n"
        f"{sc('ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ, ᴍᴀꜱᴛᴇʀ. ꜱᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ.')}"
    )
    await update.message.reply_html(text, reply_markup=admin_panel())

async def cb_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID:
        return
    text = (
        f"<b>🛡 {sc('ᴠᴇʟʏɴ ɴᴏx ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ')}</b>\n\n"
        f"{sc('ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ, ᴍᴀꜱᴛᴇʀ. ꜱᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ.')}"
    )
    try:
        await q.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=admin_panel())
    except:
        try:
            await q.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_panel())
        except:
            pass

async def cb_admin_addapi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID:
        return
    context.user_data['waiting_for'] = 'api_id'
    text = (
        f"<b>{sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}</b>\n\n"
        f"<b>{sc('ꜱᴛᴇᴘ 1/3: ᴇɴᴛᴇʀ ᴀᴘɪ ɪᴅ')}</b>"
    )
    try:
        await q.message.edit_caption(caption=text, parse_mode=ParseMode.HTML)
    except:
        try:
            await q.message.edit_text(text, parse_mode=ParseMode.HTML)
        except:
            pass

def register(app: Application) -> None:
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(cb_admin_panel, pattern="^admin:panel$"))
    app.add_handler(CallbackQueryHandler(cb_admin_addapi, pattern="^admin:addapi$"))