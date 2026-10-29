from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
import config
import database.db as db
from keyboards.menus import scrape_menu, add_menu, back_btn
from utils.text import sc
from handlers.start import safe_edit_media, safe_edit

# Premium check function
def is_premium_or_owner(user_id):
    return user_id == config.OWNER_ID or db.is_premium(user_id)

async def cb_menu_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    
    # Premium Check
    if not is_premium_or_owner(q.from_user.id):
        return await q.answer("⚠️ Premium Required! Contact @Velynx007 to purchase.", show_alert=True)

    text = (
        f"<b>⟢ {sc('ꜱᴄʀᴀᴘᴇʀ ᴇɴɢɪɴᴇ')} ⟢</b>\n\n"
        f"{sc('ᴇxᴛʀᴀᴄᴛ ᴍᴇᴍʙᴇʀꜱ ꜰʀᴏᴍ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ.')}\n\n"
        f"<b>{sc('ʟɪᴍɪᴛ')}:</b> 50 {sc('ᴍᴇᴍʙᴇʀꜱ ᴘᴇʀ ꜱᴇꜱꜱɪᴏɴ.')}\n"
        f"<b>{sc('ᴘʀᴇꜱꜱ ꜱᴛᴀʀᴛ ꜱᴄʀᴀᴘᴇ ᴛᴏ ʙᴇɢɪɴ.')}</b>"
    )
    await safe_edit_media(q, text, "SCRAPER ENGINE", scrape_menu(), use_static=True)

async def cb_menu_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    
    # Premium Check
    if not is_premium_or_owner(q.from_user.id):
        return await q.answer("⚠️ Premium Required! Contact @Velynx007 to purchase.", show_alert=True)

    text = (
        f"<b>✦ {sc('ᴀᴅᴅᴇʀ ᴇɴɢɪɴᴇ')} ✦</b>\n\n"
        f"{sc('ɪɴᴊᴇᴄᴛ ᴍᴇᴍʙᴇʀꜱ ɪɴᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ꜰʀᴏᴍ ᴀ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ.')}\n\n"
        f"<b>{sc('ʟɪᴍɪᴛ')}:</b> 50 {sc('ᴍᴇᴍʙᴇʀꜱ ᴘᴇʀ ꜱᴇꜱꜱɪᴏɴ.')}\n"
        f"<b>{sc('ᴘʀᴇꜱꜱ ꜱᴛᴀʀᴛ ᴀᴅᴅɪɴɢ ᴛᴏ ʙᴇɢɪɴ.')}</b>"
    )
    await safe_edit_media(q, text, "ADDER ENGINE", add_menu(), use_static=True)

async def cb_scrape_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not is_premium_or_owner(q.from_user.id):
        return await q.answer("⚠️ Premium Required!", show_alert=True)
        
    context.user_data['action'] = 'scrape'
    context.user_data['waiting_for'] = 'target'
    text = f"<b>{sc('ꜱᴛᴀʀᴛ ꜱᴄʀᴀᴘᴇ')}</b>\n\n<b>{sc('ꜱᴇɴᴅ ᴛʜᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ ᴏʀ ᴜꜱᴇʀɴᴀᴍᴇ')}:</b>"
    await safe_edit(q, text, back_btn())

async def cb_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not is_premium_or_owner(q.from_user.id):
        return await q.answer("⚠️ Premium Required!", show_alert=True)
        
    context.user_data['action'] = 'add'
    context.user_data['waiting_for'] = 'target'
    text = f"<b>{sc('ꜱᴛᴀʀᴛ ᴀᴅᴅ')}</b>\n\n<b>{sc('ꜱᴇɴᴅ ᴛʜᴇ ꜱᴏᴜʀᴄᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ')}:</b>"
    await safe_edit(q, text, back_btn())

def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(cb_menu_scrape, pattern="^menu:scrape$"))
    app.add_handler(CallbackQueryHandler(cb_menu_add, pattern="^menu:add$"))
    app.add_handler(CallbackQueryHandler(cb_scrape_start, pattern="^scrape:start$"))
    app.add_handler(CallbackQueryHandler(cb_add_start, pattern="^add:start$"))
