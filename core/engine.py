import asyncio
import csv
import logging
import os

from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest

import config

logger = logging.getLogger(__name__)


async def do_scrape(
    bot,
    chat_id: int,
    api_row: dict,
    target: str,
    limit: int,
    dest: str | None = None,
) -> None:
    """
    Core engine: connect Telethon, scrape members from `target`.
    If `dest` is given, add them into `dest` with ADD_DELAY_SECONDS delay.
    Otherwise, save to CSV and send to `chat_id`.
    """
    try:
        client = TelegramClient(
            StringSession(api_row["session_string"]),
            int(api_row["api_id"]),
            api_row["api_hash"],
        )
        await client.connect()
    except Exception as e:
        await bot.send_message(
            chat_id,
            f"❌ <b>Failed to connect API session:</b>\n<code>{e}</code>",
            parse_mode="HTML",
        )
        return

    try:
        entity = await client.get_entity(target)
        await bot.send_message(
            chat_id,
            f"✅ <b>Connected to:</b> <code>{entity.title}</code>\n"
            f"⏳ Starting process...",
            parse_mode="HTML",
        )

        count = 0

        # ── ADD MODE ────────────────────────────────────────────
        if dest:
            dest_entity = await client.get_entity(dest)

            async for user in client.iter_participants(entity):
                if user.bot or user.deleted:
                    continue
                try:
                    await client(InviteToChannelRequest(
                        channel=dest_entity,
                        users=[user.id],
                    ))
                    count += 1
                    name = user.first_name or "Unknown"
                    await bot.send_message(
                        chat_id,
                        f"➕ Added: <b>{name}</b> [{count}/{limit}]",
                        parse_mode="HTML",
                    )
                    await asyncio.sleep(config.ADD_DELAY_SECONDS)

                except errors.FloodWaitError as e:
                    wait = e.seconds
                    logger.warning(f"FloodWait: {wait}s")
                    await bot.send_message(
                        chat_id,
                        f"⚠️ <b>FloodWait:</b> sleeping {wait}s...",
                        parse_mode="HTML",
                    )
                    await asyncio.sleep(wait)

                except errors.UserPrivacyRestrictedError:
                    continue  # user has privacy settings blocking adds

                except Exception as e:
                    logger.warning(f"Add error for {user.id}: {e}")
                    continue

                if count >= limit:
                    break

            await bot.send_message(
                chat_id,
                f"✅ <b>Task done.</b> Added <code>{count}</code> members.",
                parse_mode="HTML",
            )

        # ── SCRAPE ONLY MODE ────────────────────────────────────
        else:
            members = []

            async for user in client.iter_participants(entity):
                if user.bot or user.deleted:
                    continue
                members.append({
                    "ID":       user.id,
                    "Name":     user.first_name or "",
                    "Username": user.username or "",
                })
                count += 1
                if count >= limit:
                    break

            if members:
                filename = f"scraped_{chat_id}_{count}.csv"
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["ID", "Name", "Username"])
                    writer.writeheader()
                    writer.writerows(members)
                with open(filename, "rb") as f:
                    await bot.send_document(
                        chat_id,
                        document=f,
                        filename=filename,
                        caption=f"✅ <b>Scraped</b> <code>{count}</code> members.",
                        parse_mode="HTML",
                    )
                os.remove(filename)
            else:
                await bot.send_message(chat_id, "❌ <b>No members found.</b>", parse_mode="HTML")

    except Exception as e:
        logger.error(f"do_scrape error: {e}")
        await bot.send_message(
            chat_id,
            f"❌ <b>Engine error:</b> <code>{e}</code>",
            parse_mode="HTML",
        )

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
