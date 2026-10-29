import asyncio, csv, os, logging
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import UserStatusOnline, UserStatusRecently

logger = logging.getLogger(__name__)

async def do_scrape(bot, chat_id, api_row, target, limit, dest=None):
    client = TelegramClient(StringSession(api_row['session_string']), int(api_row['api_id']), api_row['api_hash'])
    await client.connect()
    try:
        entity = await client.get_entity(target)
        await bot.send_message(chat_id, f"✅ Connected to: <b>{entity.title}</b>", parse_mode="HTML")
        
        count = 0
        members = []

        if dest:
            dest_entity = await client.get_entity(dest)
            skipped = 0
            async for user in client.iter_participants(entity):
                if user.bot or user.deleted: continue
                
                # Only Online or Recently active
                if not isinstance(user.status, (UserStatusOnline, UserStatusRecently)): continue
                
                try:
                    await client(InviteToChannelRequest(channel=dest_entity, users=[user.id]))
                    count += 1
                    await bot.send_message(chat_id, f"➕ Added Active: {user.first_name}")
                    await asyncio.sleep(10) 
                except errors.FloodWaitError as e:
                    await bot.send_message(chat_id, f"⚠️ FloodWait: {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                except errors.UserPrivacyRestrictedError:
                    skipped += 1 # Privacy blocked, chupchap skip karo
                except errors.UserNotMutualContactError:
                    skipped += 1 # Only contacts allowed, skip
                except Exception:
                    skipped += 1
                    
                if count >= limit: break
            
            await bot.send_message(chat_id, f"✅ Task Done. Added {count} members. (Skipped {skipped} private users).")
        else:
            async for user in client.iter_participants(entity):
                if user.bot or user.deleted: continue
                
                # Only Online or Recently active
                if not isinstance(user.status, (UserStatusOnline, UserStatusRecently)): continue
                
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

# CSV se add karna (Privacy restricted users ko silent skip karega)
async def add_from_csv(bot, chat_id, api_row, user_ids, dest_link):
    client = TelegramClient(StringSession(api_row['session_string']), int(api_row['api_id']), api_row['api_hash'])
    await client.connect()
    try:
        dest_entity = await client.get_entity(dest_link)
        count = 0
        skipped = 0
        
        for user_id in user_ids:
            try:
                await client(InviteToChannelRequest(channel=dest_entity, users=[user_id]))
                count += 1
                await bot.send_message(chat_id, f"➕ Added ID: {user_id} ({count}/{len(user_ids)})")
                await asyncio.sleep(10)
            except errors.FloodWaitError as e:
                await bot.send_message(chat_id, f"⚠️ FloodWait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except (errors.UserPrivacyRestrictedError, errors.UserNotMutualContactError):
                skipped += 1 # Chupchap skip
            except Exception:
                skipped += 1
                
        await bot.send_message(chat_id, f"✅ Task Done. Added {count} members from CSV. (Skipped {skipped} private users).")
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Error: {str(e)}")
    finally:
        await client.disconnect()
