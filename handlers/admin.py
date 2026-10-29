from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import config
from keyboards.menus import admin_panel
from utils.text import sc, esc
from handlers.start import safe_edit

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != config.OWNER_ID: return
    text = f"<b>🛡 {sc('ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ')}</b>"
    await update.message.reply_html(text, reply_markup=admin_panel())

async def cb_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID: return
    text = f"<b>🛡 {sc('ɴᴏx ꜱʏɴᴅɪᴄᴀᴛᴇ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ')}</b>"
    await safe_edit(q, text, admin_panel())

async def cb_admin_addapi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID: return
    context.user_data['waiting_for'] = 'api_id'
    text = f"<b>{sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}</b>\n\n<b>{sc('ꜱᴛᴇᴘ 1/3: ᴇɴᴛᴇʀ ᴀᴘɪ ɪᴅ')}</b>"
    await safe_edit(q, text)

async def cb_admin_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.OWNER_ID: return
    context.user_data['waiting_for'] = 'bulk_api_id'
    text = f"<b>{sc('ʙᴜʟᴋ ꜱᴇꜱꜱɪᴏɴꜱ')}</b>\n\n<b>{sc('ꜱᴛᴇᴘ 1/3: ᴇɴᴛᴇʀ ᴀᴘɪ ɪᴅ')}</b>"
    await safe_edit(q, text)

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != config.OWNER_ID: return
    if not context.args:
        await update.message.reply_text("Usage: <code>/info &lt;user_id&gt;</code>", parse_mode=ParseMode.HTML)
        return
    try:
        target_id = int(context.args[0])
        try:
            user = await context.bot.get_chat(target_id)
            name = esc(user.full_name)
            username = f"@{user.username}" if user.username else "No Username"
        except Exception:
            name = "Click to View Profile"
            username = "Hidden/Unknown"
        
        mention = f'<a href="tg://user?id={target_id}">{name}</a>'
        text = (
            f"<b>👤 {sc('ᴜꜱᴇʀ ɪɴꜰᴏ')}</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>{sc('ɴᴀᴍᴇ')}:</b> {mention}\n"
            f"<b>{sc('ᴜꜱᴇʀɴᴀᴍᴇ')}:</b> {username}\n"
            f"<b>{sc('ɪᴅ')}:</b> <code>{target_id}</code>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
            f"<i>{sc('ᴄʟɪᴄᴋ ᴛʜᴇ ɴᴀᴍᴇ ᴛᴏ ᴏᴘᴇɴ ᴘʀᴏꜰɪʟᴇ')}</i>"
        )
        await update.message.reply_html(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def register(app: Application) -> None:
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CallbackQueryHandler(cb_admin_panel, pattern="^admin:panel$"))
    app.add_handler(CallbackQueryHandler(cb_admin_addapi, pattern="^admin:addapi$"))
    app.add_handler(CallbackQueryHandler(cb_admin_bulk, pattern="^admin:bulk$"))
