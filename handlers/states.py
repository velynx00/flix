import logging, asyncio, csv, io
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from database.db import db
from core.engine import do_scrape, add_from_csv
from utils.text import sc

logger = logging.getLogger(__name__)

def clear_all(user_id): pass

async def handle_states(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waiting_for = context.user_data.get('waiting_for')
    if not waiting_for: return
    
    text = update.message.text if update.message.text else ""
    document = update.message.document

    if waiting_for == 'api_id':
        context.user_data['api_id'] = text
        context.user_data['waiting_for'] = 'api_hash'
        await update.message.reply_text(f"<b>{sc('ꜱᴛᴇᴘ 2/3: ᴇɴᴛᴇʀ ᴀᴘɪ ʜᴀꜱʜ')}:</b>", parse_mode=ParseMode.HTML)
    elif waiting_for == 'api_hash':
        context.user_data['api_hash'] = text
        context.user_data['waiting_for'] = 'api_phone'
        await update.message.reply_text(f"<b>{sc('ꜱᴛᴇᴘ 3/3: ᴇɴᴛᴇʀ ᴘʜᴏɴᴇ')} (+91...):</b>", parse_mode=ParseMode.HTML)
    elif waiting_for == 'api_phone':
        client = TelegramClient(StringSession(), int(context.user_data['api_id']), context.user_data['api_hash'])
        await client.connect()
        try:
            clean_phone = text.replace("++", "+")
            await client.send_code_request(clean_phone)
            context.user_data['client'] = client
            context.user_data['phone'] = clean_phone
            context.user_data['waiting_for'] = 'api_otp'
            await update.message.reply_text(f"<b>{sc('ᴇɴᴛᴇʀ ᴛʜᴇ ᴏᴛᴘ')}:</b>", parse_mode=ParseMode.HTML)
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
            await update.message.reply_text("🔐 <b>2FA Password Required:</b>", parse_mode=ParseMode.HTML)
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

    # ── BULK SESSION FLOW (SMART FIX) ──
    elif waiting_for == 'bulk_sessions':
        if not document: return await update.message.reply_text("❌ Please send a valid `.txt` file.")
        
        apis = db.get_apis()
        if not apis:
            return await update.message.reply_text("❌ Add at least one single API first to get API ID/Hash.")
            
        api_id = int(apis[0]['api_id'])
        api_hash = apis[0]['api_hash']
        
        await update.message.reply_text(f"📥 Downloading & Checking file...")
        
        try:
            file = await context.bot.get_file(document.file_id)
            content = (await file.download_as_bytearray()).decode('utf-8')
            sessions = [s.strip() for s in content.split('\n') if s.strip()]
            context.user_data['waiting_for'] = None
            
            valid, dead = 0, 0
            for idx, sess in enumerate(sessions, 1):
                try:
                    client = TelegramClient(StringSession(sess), api_id, api_hash)
                    await client.connect()
                    if await client.is_user_authorized():
                        me = await client.get_me()
                        db.add_api(api_id, api_hash, me.phone or f"Bulk_{me.id}", sess)
                        valid += 1
                        await update.message.reply_text(f"✅ Valid: {me.first_name} (+{me.phone})")
                    else:
                        dead += 1
                        await update.message.reply_text(f"❌ Dead Session ({idx})")
                    await client.disconnect()
                except Exception:
                    dead += 1
                    await update.message.reply_text(f"❌ Invalid Session ({idx})")
            
            await update.message.reply_text(f"✅ <b>Bulk Complete!</b>\nValid: {valid}\nDead: {dead}", parse_mode=ParseMode.HTML)
        except Exception as e:
            context.user_data['waiting_for'] = None
            await update.message.reply_text(f"❌ File Error: {e}")

    # ── ADD FROM CSV FLOW ──
    elif waiting_for == 'csv_file':
        if not document: return await update.message.reply_text("❌ Please send a `.csv` file.")
        
        await update.message.reply_text("📥 Processing CSV...")
        try:
            file = await context.bot.get_file(document.file_id)
            content = (await file.download_as_bytearray()).decode('utf-8')
            
            reader = csv.DictReader(io.StringIO(content))
            user_ids = [int(row['ID']) for row in reader if 'ID' in row]
            
            if not user_ids:
                context.user_data['waiting_for'] = None
                return await update.message.reply_text("❌ No IDs found in CSV.")
                
            context.user_data['csv_ids'] = user_ids
            context.user_data['waiting_for'] = 'dest'
            
            await update.message.reply_text(f"✅ Found {len(user_ids)} members in CSV.\n\n<b>Send Destination Group Link:</b>", parse_mode=ParseMode.HTML)
            
        except Exception as e:
            context.user_data['waiting_for'] = None
            await update.message.reply_text(f"❌ CSV Error: {e}")

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
            if not apis: return await update.message.reply_text("❌ No API configured.")
            await update.message.reply_text(f"⏳ <b>{sc('ꜱᴄʀᴀᴘɪɴɢ ꜱᴛᴀʀᴛᴇᴅ...')}</b>", parse_mode=ParseMode.HTML)
            asyncio.create_task(do_scrape(update.get_bot(), update.message.chat_id, apis[0], context.user_data['target'], limit))
            
    elif waiting_for == 'dest':
        dest = text
        context.user_data['waiting_for'] = None
        apis = db.get_apis()
        if not apis: return await update.message.reply_text("❌ No API configured.")
        
        if context.user_data.get('action') == 'add_csv':
            csv_ids = context.user_data.get('csv_ids', [])
            await update.message.reply_text(f"⏳ <b>{sc('ᴀᴅᴅɪɴɢ ꜰʀᴏᴍ ᴄꜱᴠ ꜱᴛᴀʀᴛᴇᴅ...')}</b>", parse_mode=ParseMode.HTML)
            asyncio.create_task(add_from_csv(update.get_bot(), update.message.chat_id, apis[0], csv_ids, dest))
        else:
            await update.message.reply_text(f"⏳ <b>{sc('ᴀᴅᴅɪɴɢ ꜱᴛᴀʀᴛᴇᴅ...')}</b>", parse_mode=ParseMode.HTML)
            asyncio.create_task(do_scrape(update.get_bot(), update.message.chat_id, apis[0], context.user_data['target'], context.user_data['limit'], dest))

def register(app: Application) -> None:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_states))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_states))
