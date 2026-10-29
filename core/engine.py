"""
engine.py — core scrape / add logic with real-time progress bars
"""
import asyncio, csv, io, logging, time
from typing import Optional
from telegram import Message
from telegram.constants import ParseMode
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError, UserPrivacyRestrictedError, UserAlreadyParticipantError,
    PeerFloodError, InputUserDeactivatedError, UserBannedInChannelError,
)
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import UserStatusOnline, UserStatusRecently
import config
from database.db import db
from utils.text import sc, progress_bar

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  CONSTANTS
# ──────────────────────────────────────────────

EDIT_INTERVAL  = 5      # edit status msg every N members
FLOOD_PAUSE    = 65     # seconds to wait after FloodWait
ADD_DELAY_MIN  = 30     # min seconds between adds
ADD_DELAY_MAX  = 45     # max seconds between adds

# ──────────────────────────────────────────────
#  PROGRESS UI HELPERS
# ──────────────────────────────────────────────

def _scrape_status(done: int, total: int, skipped: int) -> str:
    bar = progress_bar(done, total)
    return (
        f"<b>🔍 {sc('ꜱᴄʀᴀᴘɪɴɢ ᴍᴇᴍʙᴇʀꜱ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>{bar}</b>\n\n"
        f"<b>✅ {sc('ꜰᴇᴛᴄʜᴇᴅ')}:</b>  <code>{done}</code>\n"
        f"<b>⏭ {sc('ꜱᴋɪᴘᴘᴇᴅ')}:</b>  <code>{skipped}</code>\n"
        f"<b>🎯 {sc('ᴛᴀʀɢᴇᴛ')}:</b>   <code>{total}</code>"
    )

def _add_status(done: int, total: int, ok: int, fail: int, flood: int) -> str:
    bar = progress_bar(done, total)
    return (
        f"<b>⚡ {sc('ᴀᴅᴅɪɴɢ ᴍᴇᴍʙᴇʀꜱ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>{bar}</b>\n\n"
        f"<b>✅ {sc('ᴀᴅᴅᴇᴅ')}:</b>    <code>{ok}</code>\n"
        f"<b>❌ {sc('ꜰᴀɪʟᴇᴅ')}:</b>   <code>{fail}</code>\n"
        f"<b>🌊 {sc('ꜰʟᴏᴏᴅ ʜɪᴛꜱ')}:</b> <code>{flood}</code>\n"
        f"<b>🎯 {sc('ᴛᴀʀɢᴇᴛ')}:</b>  <code>{total}</code>"
    )

async def _safe_edit(msg: Message, text: str) -> None:
    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.debug(f"Status edit: {e}")

# ──────────────────────────────────────────────
#  SCRAPE
# ──────────────────────────────────────────────

async def do_scrape(
    client: TelegramClient,
    source_link: str,
    limit: int,
    status_msg: Message,
    only_active: bool = False,
) -> list[dict]:
    """
    Scrape up to `limit` members from source_link.
    Edits status_msg with live progress every EDIT_INTERVAL members.
    Returns list of dicts: {id, username, first_name, last_name, phone}
    """
    results = []
    skipped = 0
    last_edit = 0

    try:
        entity = await client.get_entity(source_link)
    except Exception as e:
        await _safe_edit(status_msg, f"<b>❌ {sc('ᴄᴀɴɴᴏᴛ ꜰɪɴᴅ ɢʀᴏᴜᴘ')}</b>\n<code>{e}</code>")
        return []

    await _safe_edit(status_msg, _scrape_status(0, limit, 0))

    async for member in client.iter_participants(entity, limit=limit):
        if member.bot or member.deleted:
            skipped += 1
            continue
        if only_active:
            st = member.status
            if not isinstance(st, (UserStatusOnline, UserStatusRecently)):
                skipped += 1
                continue

        results.append({
            "id":         str(member.id),
            "username":   member.username or "",
            "first_name": member.first_name or "",
            "last_name":  member.last_name or "",
            "phone":      member.phone or "",
        })

        done = len(results)
        if done % EDIT_INTERVAL == 0 or done == limit:
            now = time.monotonic()
            if now - last_edit > 1.5:          # debounce Telegram rate limit
                await _safe_edit(status_msg, _scrape_status(done, limit, skipped))
                last_edit = now

        if done >= limit:
            break

    return results


async def do_scrape_to_csv(
    client: TelegramClient,
    source_link: str,
    limit: int,
    status_msg: Message,
    only_active: bool = False,
) -> Optional[bytes]:
    """Returns CSV bytes ready to send as file, or None on failure."""
    members = await do_scrape(client, source_link, limit, status_msg, only_active)
    if not members:
        return None

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id","username","first_name","last_name","phone"])
    writer.writeheader()
    writer.writerows(members)
    return buf.getvalue().encode()

# ──────────────────────────────────────────────
#  ADD FROM LIST
# ──────────────────────────────────────────────

async def add_from_list(
    client: TelegramClient,
    target_link: str,
    members: list[dict],
    status_msg: Message,
    delay_min: int = ADD_DELAY_MIN,
    delay_max: int = ADD_DELAY_MAX,
) -> dict:
    """
    Add members (list of dicts with 'id' and optionally 'username') to target.
    Returns summary dict.
    """
    ok, fail, flood_hits = 0, 0, 0
    total = len(members)
    last_edit = 0

    try:
        target = await client.get_entity(target_link)
    except Exception as e:
        await _safe_edit(status_msg, f"<b>❌ {sc('ᴄᴀɴɴᴏᴛ ꜰɪɴᴅ ᴛᴀʀɢᴇᴛ')}</b>\n<code>{e}</code>")
        return {"ok": 0, "fail": 0, "flood": 0, "total": total}

    await _safe_edit(status_msg, _add_status(0, total, 0, 0, 0))

    for i, m in enumerate(members, 1):
        try:
            uid = int(m["id"])
            if m.get("username"):
                user = await client.get_entity(m["username"])
            else:
                user = await client.get_entity(uid)

            await client(InviteToChannelRequest(target, [user]))
            ok += 1

        except FloodWaitError as e:
            flood_hits += 1
            wait = min(e.seconds + 5, FLOOD_PAUSE)
            await _safe_edit(
                status_msg,
                _add_status(i, total, ok, fail, flood_hits)
                + f"\n\n<b>🌊 {sc('ꜰʟᴏᴏᴅ ᴡᴀɪᴛ')}: {wait}s</b>"
            )
            await asyncio.sleep(wait)
            continue

        except (UserPrivacyRestrictedError, InputUserDeactivatedError, UserBannedInChannelError):
            fail += 1
        except UserAlreadyParticipantError:
            pass        # already in group — not a failure
        except PeerFloodError:
            flood_hits += 1
            await asyncio.sleep(FLOOD_PAUSE)
        except Exception as e:
            fail += 1
            logger.warning(f"Add {m.get('username',m['id'])}: {e}")

        done = ok + fail
        now = time.monotonic()
        if done % EDIT_INTERVAL == 0 and now - last_edit > 2:
            await _safe_edit(status_msg, _add_status(done, total, ok, fail, flood_hits))
            last_edit = now

        # polite delay
        import random
        await asyncio.sleep(random.uniform(delay_min, delay_max))

    return {"ok": ok, "fail": fail, "flood": flood_hits, "total": total}


async def add_from_csv(
    client: TelegramClient,
    target_link: str,
    csv_bytes: bytes,
    status_msg: Message,
    delay_min: int = ADD_DELAY_MIN,
    delay_max: int = ADD_DELAY_MAX,
) -> dict:
    """Parse CSV bytes and call add_from_list."""
    try:
        text = csv_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        members = list(reader)
        if not members:
            await _safe_edit(status_msg, f"<b>❌ {sc('ᴄꜱᴠ ɪꜱ ᴇᴍᴘᴛʏ')}</b>")
            return {"ok": 0, "fail": 0, "flood": 0, "total": 0}
    except Exception as e:
        await _safe_edit(status_msg, f"<b>❌ {sc('ᴄꜱᴠ ᴘᴀʀꜱᴇ ᴇʀʀᴏʀ')}</b>\n<code>{e}</code>")
        return {"ok": 0, "fail": 0, "flood": 0, "total": 0}

    return await add_from_list(client, target_link, members, status_msg, delay_min, delay_max)


def format_add_result(res: dict) -> str:
    """Final summary message after add_from_list / add_from_csv."""
    bar = progress_bar(res["ok"], res["total"])
    return (
        f"<b>✅ {sc('ᴀᴅᴅ ᴄᴏᴍᴘʟᴇᴛᴇ')}</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>{bar}</b>\n\n"
        f"<b>✅ {sc('ꜱᴜᴄᴄᴇꜱꜱ')}:</b>    <code>{res['ok']}</code>\n"
        f"<b>❌ {sc('ꜰᴀɪʟᴇᴅ')}:</b>    <code>{res['fail']}</code>\n"
        f"<b>🌊 {sc('ꜰʟᴏᴏᴅ ʜɪᴛꜱ')}:</b>  <code>{res['flood']}</code>\n"
        f"<b>🎯 {sc('ᴛᴏᴛᴀʟ ᴛʀɪᴇᴅ')}:</b> <code>{res['total']}</code>"
    )
