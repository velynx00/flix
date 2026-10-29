import logging, asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from database.db import db
from core.engine import do_scrape
from utils.text import sc

logger = logging.getLogger(__name__)

def clear_all(user_id):
    pass

async def handle_states(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waiting_for = context.user_data.get('waiting_for')
    if not waiting_for: return
    text = update.message.text

    # ── NORMAL SINGLE API FLOW ──
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
            clean_phone = text.replace("++", "+")
            await client.send_code_request(clean_phone)
            context.user_data['client'] = client
            context.user_data['phone'] = clean_phone
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
        except errors.SessionPasswordNeededError:
            context.user_data['waiting_for'] = 'api_2fa'
            await update.message.reply_text("🔐 <b>2FA Password Required:</b>\n\nPlease enter your password:", parse_mode=ParseMode.HTML)
        except Exception as e:
            context.user_data['waiting_for'] = None
            await update.message.reply_text(f"❌ Error: {e}")
                
    elif waiting_for == 'api_2fa':
        client = context.user_data['client']
        try:
            await client.sign_in(password=text)
            db.add_api(context.user_data['api_id'], context.user_data['api_hash'], context.user_data['phone'], client.session.save())
            context.user_data['waiting_for'] = None
            await update.message.reply_text("✅ <b>API Added (2FA)!</b>", parse_mode=ParseMode.HTML)
            await client.disconnect()
        except Exception as e:
            context.user_data['waiting_for'] = None
            await update.message.reply_text(f"❌ Error: {e}")

    # ── BULK SESSION FLOW ──
    elif waiting_for == 'bulk_api_id':
        context.user_data['bulk_api_id'] = text
        context.user_data['waiting_for'] = 'bulk_api_hash'
        await update.message.reply_text(f"<b>{sc('ꜱᴛᴇᴘ 2/3: ᴇɴᴛᴇʀ ᴀᴘɪ ʜᴀꜱʜ')}:</b>", parse_mode=ParseMode.HTML)
        
    elif waiting_for == 'bulk_api_hash':
        context.user_data['bulk_api_hash'] = text
        context.user_data['waiting_for'] = 'bulk_sessions'
        await update.message.reply_text(f"<b>{sc('ꜱᴛᴇᴘ 3/3: ᴘᴀꜱᴛᴇ ꜱᴇꜱꜱɪᴏɴꜱ')}</b>\n\nSend session strings (one per line):", parse_mode=ParseMode.HTML)

    elif waiting_for == 'bulk_sessions':
        sessions = [s.strip() for s in text.split('\n') if s.strip()]
        context.user_data['waiting_for'] = None
        await update.message.reply_text(f"⏳ Checking {len(sessions)} sessions... (Please wait)")

        api_id = int(context.user_data['bulk_api_id'])
        api_hash = context.user_data['bulk_api_hash']
        
        valid_count = 0
        dead_count = 0
        
        for idx, sess_str in enumerate(sessions, 1):
            try:
                client = TelegramClient(StringSession(sess_str), api_id, api_hash)
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    db.add_api(api_id, api_hash, f"Bulk_{me.id}", sess_str)
                    valid_count += 1
                    await update.message.reply_text(f"✅ Valid: {me.first_name} ({me.phone})")
                else:
                    dead_count += 1
                    await update.message.reply_text(f"❌ Dead/Invalid Session ({idx})")
                await client.disconnect()
            except Exception as e:
                dead_count += 1
                await update.message.reply_text(f"❌ Error ({idx}): Invalid Session")
        
        await update.message.reply_text(f"✅ <b>Bulk Import Complete!</b>\n\nValid: {valid_count}\nDead/Invalid: {dead_count}", parse_mode=ParseMode.HTML)

    # ── SCRAPE/ADD FLOW ──
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
            return await update.message.reply_text(f"❌ {sc('ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ')}")
        
        if context.user_data.get('action') == 'add':
            context.user_data['waiting_for'] = 'dest'
            await update.message.reply_text(f"<b>{sc('ꜱᴇɴᴅ ᴛʜᴇ ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ ᴡʜᴇʀᴇ ᴛᴏ ᴀᴅᴅ')}:</b>", parse_mode=ParseMode.HTML)
        else:
            context.user_data['waiting_for'] = None
            apis = db.get_apis()
            if not apis: return await update.message.reply_text("❌ No API configured. Use Setup API.")
            await update.message.reply_text(f"⏳ <b>{sc('ꜱᴄʀᴀᴘɪɴɢ ꜱᴛᴀʀᴛᴇᴅ...')}</b>", parse_mode=ParseMode.HTML)
            asyncio.create_task(do_scrape(update.get_bot(), update.message.chat_id, apis[0], context.user_data['target'], limit))
            
    elif waiting_for == 'dest':
        dest = text
        context.user_data['waiting_for'] = None
        apis = db.get_apis()
        if not apis: return await update.message.reply_text("❌ No API configured.")
        await update.message.reply_text(f"⏳ <b>{sc('ᴀᴅᴅɪɴɢ ꜱᴛᴀʀᴛᴇᴅ...')}</b>", parse_mode=ParseMode.HTML)
        asyncio.create_task(do_scrape(update.get_bot(), update.message.chat_id, apis[0], context.user_data['target'], context.user_data['limit'], dest))

def register(app: Application) -> None:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_states))
