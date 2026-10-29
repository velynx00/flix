import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
import config
import database.db as db
from keyboards.menus import scrape_menu, add_menu, back_btn
from utils.text import sc

logger = logging.getLogger(__name__)

def safe_edit(q, text, reply_markup=None):
    try:
        if q.message and q.message.photo:
            return q.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            return q.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except: pass

async def cb_menu_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not db.has_session(q.from_user.id):
        return await q.answer("Session Required! Go to /admin to add API.", show_alert=True)
    
    text = f"<b>⟢ {sc('ꜱᴄʀᴀᴘᴇʀ ᴇɴɢɪɴᴇ')} ⟢</b>\n\n{sc('ᴇxᴛʀᴀᴄᴛ ᴍᴇᴍʙᴇʀꜱ ꜰʀᴏᴍ ᴀ ɢʀᴏᴜᴘ.')}"
    await safe_edit(q, text, scrape_menu())

async def cb_menu_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not db.has_session(q.from_user.id):
        return await q.answer("Session Required! Go to /admin to add API.", show_alert=True)
        
    text = f"<b>✦ {sc('ᴀᴅᴅᴇʀ ᴇɴɢɪɴᴇ')} ✦</b>\n\n{sc('ɪɴᴊᴇᴄᴛ ᴍᴇᴍʙᴇʀꜱ ɪɴᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ.')}"
    await safe_edit(q, text, add_menu())

async def cb_scrape_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    context.user_data['action'] = 'scrape'
    context.user_data['waiting_for'] = 'target' # State set
    
    text = f"<b>{sc('ꜱᴛᴀʀᴛ ꜱᴄʀᴀᴘᴇ')}</b>\n\n<b>{sc('ꜱᴇɴᴅ ᴛʜᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ ᴏʀ ᴜꜱᴇʀɴᴀᴍᴇ')}:</b>"
    await safe_edit(q, text, back_btn())

async def cb_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    context.user_data['action'] = 'add'
    context.user_data['waiting_for'] = 'target' # State set
    
    text = f"<b>{sc('ꜱᴛᴀʀᴛ ᴀᴅᴅ')}</b>\n\n<b>{sc('ꜱᴇɴᴅ ᴛʜᴇ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ')}:</b>"
    await safe_edit(q, text, back_btn())

def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(cb_menu_scrape, pattern="^menu:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_menu_add, pattern="^menu:add$"))
    app.add_handler(CallbackQueryHandler(cb_scrape_start, pattern="^scrape:start$"))
    app.add_handler(CallbackQueryHandler(cb_add_start, pattern="^add:start$"))