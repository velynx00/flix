import asyncio, csv, os, logging
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import UserStatusOnline, UserStatusRecently

logger = logging.getLogger(__name__)

async def do_scrape(bot, chat_id, api_row, target, limit, dest=None):
    try:
        client = TelegramClient(
            StringSession(api_row['session_string']), 
            int(api_row['api_id']), 
            api_row['api_hash']
        )
        await client.connect()
    except Exception as e:
        return await bot.send_message(chat_id, f"❌ Failed to connect API session: {e}")

    try:
        entity = await client.get_entity(target)
        await bot.send_message(chat_id, f"✅ Connected to: <b>{entity.title}</b>\nSearching for Active Members...", parse_mode="HTML")
        
        count = 0
        members = []

        if dest:
            dest_entity = await client.get_entity(dest)
            async for user in client.iter_participants(entity):
                if user.bot or user.deleted: continue
                
                # FILTER: Sirf Online ya Recently Active members
                if not isinstance(user.status, (UserStatusOnline, UserStatusRecently)):
                    continue
                
                try:
                    await client(InviteToChannelRequest(channel=dest_entity, users=[user.id]))
                    count += 1
                    await bot.send_message(chat_id, f"➕ Added Active User: {user.first_name}")
                    await asyncio.sleep(10) 
                except errors.FloodWaitError as e:
                    await bot.send_message(chat_id, f"⚠️ FloodWait: {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                except Exception:
                    continue
                if count >= limit: break
            await bot.send_message(chat_id, f"✅ Task Done. Added {count} active members.")
        else:
            async for user in client.iter_participants(entity):
                if user.bot or user.deleted: continue
                
                # FILTER: Sirf Online ya Recently Active members
                if not isinstance(user.status, (UserStatusOnline, UserStatusRecently)):
                    continue
                
                members.append({"ID": user.id, "Name": user.first_name, "Username": user.username})
                count += 1
                if count >= limit: break
            
            if members:
                filename = f"scraped_{chat_id}_{count}.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=["ID", "Name", "Username"])
                    writer.writeheader()
                    writer.writerows(members)
                await bot.send_document(chat_id, open(filename, 'rb'), caption=f"✅ Scraped {count} active members.")
                os.remove(filename)
            else:
                await bot.send_message(chat_id, "❌ No active members found.")

    except Exception as e:
        await bot.send_message(chat_id, f"❌ Error: {str(e)}")
    finally:
        await client.disconnect()
