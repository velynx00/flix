import asyncio
import csv
import os
import logging
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest

logger = logging.getLogger(__name__)

async def do_scrape(bot, chat_id, api_row, target, limit, dest=None):
    """
    Main function to handle both Scraping and Adding.
    If 'dest' is provided, it adds members. Otherwise, it scrapes them.
    """
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
        await bot.send_message(chat_id, f"✅ Connected to: <b>{entity.title}</b>\nStarting process...", parse_mode="HTML")
        
        count = 0
        members = []

        # ── ADDING LOGIC ──
        if dest:
            dest_entity = await client.get_entity(dest)
            async for user in client.iter_participants(entity):
                if user.bot or user.deleted:
                    continue
                
                try:
                    await client(InviteToChannelRequest(channel=dest_entity, users=[user.id]))
                    count += 1
                    await bot.send_message(chat_id, f"➕ Added: {user.first_name}")
                    await asyncio.sleep(10) # 10 sec delay to avoid ban
                except errors.FloodWaitError as e:
                    await bot.send_message(chat_id, f"⚠️ FloodWait: Sleeping for {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                except errors.UserPrivacyRestrictedError:
                    logger.warning(f"Skipped {user.id} due to privacy.")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to add {user.id}: {e}")
                    continue

                if count >= limit:
                    break
            
            await bot.send_message(chat_id, f"✅ Task Done. Processed {count} members.")

        # ── SCRAPING LOGIC ──
        else:
            async for user in client.iter_participants(entity):
                if user.bot or user.deleted:
                    continue
                
                members.append({
                    "ID": user.id, 
                    "Name": user.first_name, 
                    "Username": user.username
                })
                count += 1
                
                if count >= limit:
                    break
            
            if members:
                filename = f"scraped_{chat_id}_{count}.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=["ID", "Name", "Username"])
                    writer.writeheader()
                    writer.writerows(members)
                
                await bot.send_document(
                    chat_id, 
                    open(filename, 'rb'), 
                    caption=f"✅ Scraped {count} members successfully."
                )
                os.remove(filename)
            else:
                await bot.send_message(chat_id, "❌ No members found or all were skipped.")

    except Exception as e:
        await bot.send_message(chat_id, f"❌ Error: {str(e)}")
        logger.error(f"Engine Error: {e}")
    finally:
        await client.disconnect()