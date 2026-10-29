from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import config
from keyboards.menus import admin_panel
from utils.text import sc
from utils.banner import generate_scary_dp
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

# NAYA HANDLER: Khatarnak DP generate karke bhejna
async def cb_admin_dp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer("Generating Dark DP...", show_alert=False)
    if q.from_user.id != config.OWNER_ID: return
    
    try:
        dp_buf = generate_scary_dp()
        await q.message.reply_photo(
            photo=InputFile(dp_buf, filename="dark_dp.jpg"),
            caption="<b>😈 ʏᴏᴜʀ ᴋʜᴀᴛᴀʀɴᴀᴋ ᴅᴘ ɪꜱ ʀᴇᴀᴅʏ!</b>\n\n<i>1. Image ko save karo.\n2. @BotFather me jao.\n3. /setuserpic command do.\n4. Apna bot select karo aur ye image upload kar do.</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await q.message.reply_text(f"❌ Error: {e}")

def register(app: Application) -> None:
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(cb_admin_panel, pattern="^admin:panel$"))
    app.add_handler(CallbackQueryHandler(cb_admin_addapi, pattern="^admin:addapi$"))
    app.add_handler(CallbackQueryHandler(cb_admin_dp, pattern="^admin:dp$"))
