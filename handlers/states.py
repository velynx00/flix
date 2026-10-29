import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telethon import TelegramClient
from telethon.sessions import StringSession
import config
import database.db as db
from core.engine import do_scrape
from utils.text import sc

logger = logging.getLogger(__name__)

async def handle_states(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waiting_for = context.user_data.get('waiting_for')
    if not waiting_for:
        return # Agar koi state nahi hai, toh kuch mat karo

    text = update.message.text

    # ================= API SETUP FLOW =================
    if waiting_for == 'api_id':
        context.user_data['api_id'] = text
        context.user_data['waiting_for'] = 'api_hash'
        await update.message.reply_text(f"<b>{sc('ꜱᴛᴇᴘ 2/3: ᴇɴᴛᴇʀ ᴀᴘɪ ʜᴀꜱʜ')}:</b>", parse_mode=ParseMode.HTML)

    elif waiting_for == 'api_hash':
        context.user_data['api_hash'] = text
        context.user_data['waiting_for'] = 'api_phone'
        await update.message.reply_text(f"<b>{sc('ꜱᴛᴇᴘ 3/3: ᴇɴᴛᴇʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ')} (+91...):</b>", parse_mode=ParseMode.HTML)

    elif waiting_for == 'api_phone':
        client = TelegramClient(StringSession(), int(context.user_data['api_id']), context.user_data['api_hash'])
        await client.connect()
        try:
            await client.send_code_request(text)
            context.user_data['client'] = client
            context.user_data['phone'] = text
            context.user_data['waiting_for'] = 'api_otp'
            await update.message.reply_text(f"<b>{sc('ᴇɴᴛᴇʀ ᴛʜᴇ ᴏᴛᴘ ᴄᴏᴅᴇ')}:</b>", parse_mode=ParseMode.HTML)
        except Exception as e:
            context.user_data['waiting_for'] = None
            await update.message.reply_text(f"❌ Error: {e}")

    elif waiting_for == 'api_otp':
        client = context.user_data['client']
        try:
            await client.sign_in(context.user_data['phone'], text.replace(" ", ""))
            db.add_api(context.user_data['api_id'], context.user_data['api_hash'], context.user_data['phone'], client.session.save())
            context.user_data['waiting_for'] = None
            await update.message.reply_text("✅ <b>API Added Successfully!</b>", parse_mode=ParseMode.HTML)
            await client.disconnect()
        except Exception as e:
            if "SessionPasswordNeeded" in str(e):
                context.user_data['waiting_for'] = 'api_2fa'
                await update.message.reply_text("🔐 <b>2FA Password Required:</b>", parse_mode=ParseMode.HTML)
            else:
                context.user_data['waiting_for'] = None
                await update.message.reply_text(f"❌ Error: {e}")

    elif waiting_for == 'api_2fa':
        client = context.user_data['client']
        try:
            await client.sign_in(password=text)
            db.add_api(context.user_data['api_id'], context.user_data['api_hash'], context.user_data['phone'], client.session.save())
            context.user_data['waiting_for'] = None
            await update.message.reply_text("✅ <b>API Added Successfully (2FA)!</b>", parse_mode=ParseMode.HTML)
            await client.disconnect()
        except Exception as e:
            context.user_data['waiting_for'] = None
            await update.message.reply_text(f"❌ Error: {e}")

    # ================= SCRAPE / ADD FLOW =================
    elif waiting_for == 'target':
        context.user_data['target'] = text
        context.user_data['waiting_for'] = 'limit'
        await update.message.reply_text(f"<b>{sc('ᴇɴᴛᴇʀ ʟɪᴍɪᴛ')} (1-50):</b>", parse_mode=ParseMode.HTML)

    elif waiting_for == 'limit':
        try:
            limit = int(text)
            if limit > 50: limit = 50
            context.user_data['limit'] = limit
        except:
            return await update.message.reply_text(f"❌ {sc('ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ. ᴛʀʏ ᴀɢᴀɪɴ.')}")

        action = context.user_data.get('action')
        if action == 'add':
            context.user_data['waiting_for'] = 'dest'
            await update.message.reply_text(f"<b>{sc('ꜱᴇɴᴅ ᴛʜᴇ ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ ᴡʜᴇʀᴇ ᴛᴏ ᴀᴅᴅ')}:</b>", parse_mode=ParseMode.HTML)
        else:
            context.user_data['waiting_for'] = None
            apis = db.get_apis()
            if not apis: return await update.message.reply_text("❌ No API configured.")
            
            await update.message.reply_text(f"⏳ <b>{sc('ꜱᴄʀᴀᴘɪɴɢ ꜱᴛᴀʀᴛᴇᴅ...')}</b>", parse_mode=ParseMode.HTML)
            # Background task
            import asyncio
            asyncio.create_task(do_scrape(update.get_bot(), update.message.chat_id, apis[0], context.user_data['target'], limit))

    elif waiting_for == 'dest':
        dest = text
        context.user_data['waiting_for'] = None
        apis = db.get_apis()
        if not apis: return await update.message.reply_text("❌ No API configured.")
        
        await update.message.reply_text(f"⏳ <b>{sc('ᴀᴅᴅɪɴɢ ꜱᴛᴀʀᴛᴇᴅ...')}</b>", parse_mode=ParseMode.HTML)
        import asyncio
        asyncio.create_task(do_scrape(update.get_bot(), update.message.chat_id, apis[0], context.user_data['target'], context.user_data['limit'], dest))

def register(app: Application) -> None:
    # Sabse aakhri me register hona chahiye
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_states))