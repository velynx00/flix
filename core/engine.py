# ============================================================
# core/engine.py — Telethon Scrape & Add Engine
#
# All Telethon I/O is async.  The engine never blocks the PTB
# event loop — heavy work runs in the same asyncio loop since
# Telethon is async-native.
#
# Public surface:
#   build_client(session_row)   → TelegramClient (not started)
#   scrape_members(...)         → AsyncGenerator[dict, None]
#   add_members(...)            → AsyncGenerator[dict, None]
#   export_to_csv(members, path)→ str (file path)
# ============================================================

from __future__ import annotations

import asyncio
import csv
import logging
import os
import re
import tempfile
import time
from typing import AsyncGenerator, Optional

from telethon import TelegramClient, errors, functions, types
from telethon.sessions import StringSession

import config
from handlers import states

logger = logging.getLogger(__name__)


# ── Telethon client factory ───────────────────────────────────

def build_client(
    session_string: str,
    api_id: int,
    api_hash: str,
) -> TelegramClient:
    """
    Construct a Telethon TelegramClient from a StringSession.

    The client is NOT connected here — callers must use it as
    an async context manager (``async with client:``) or manually
    call ``await client.connect()``.

    Parameters
    ----------
    session_string : str  — Telethon StringSession string.
    api_id         : int  — API ID (user's own or default).
    api_hash       : str  — API hash (user's own or default).

    Returns
    -------
    TelegramClient
        A configured but disconnected client instance.
    """
    return TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash,
        # Device / app metadata that blends in with real clients
        device_model     = "Samsung Galaxy S24",
        system_version   = "Android 14",
        app_version      = "10.3.2",
        lang_code        = "en",
        system_lang_code = "en-US",
    )


# ── Group resolver ────────────────────────────────────────────

async def resolve_group(
    client: TelegramClient,
    group_input: str,
) -> Optional[types.Channel]:
    """
    Resolve a group link, username, or invite hash to a Telethon entity.

    Handles:
        • Public username   : ``@groupname`` / ``groupname``
        • t.me link         : ``https://t.me/groupname``
        • t.me/joinchat    : private invite links

    Parameters
    ----------
    client      : TelegramClient
    group_input : str  — Raw user-supplied group string.

    Returns
    -------
    types.Channel | None
        The resolved entity, or None on failure.
    """
    group_input = group_input.strip()

    # Strip https://t.me/ prefix
    if "t.me/" in group_input:
        group_input = group_input.split("t.me/")[-1].strip("/")

    # Attempt resolution
    try:
        entity = await client.get_entity(group_input)
        if isinstance(entity, (types.Channel, types.Chat)):
            return entity
        logger.warning(f"[ENGINE] Resolved entity is not a group: {type(entity)}")
        return None
    except errors.UsernameNotOccupiedError:
        logger.error(f"[ENGINE] Username not found: {group_input}")
        return None
    except errors.InviteHashInvalidError:
        logger.error(f"[ENGINE] Invalid invite hash: {group_input}")
        return None
    except Exception as exc:
        logger.error(f"[ENGINE] resolve_group error: {exc}")
        return None


# ── Member scraper ────────────────────────────────────────────

async def scrape_members(
    session_string: str,
    api_id: int,
    api_hash: str,
    group_input: str,
    limit: Optional[int] = None,
    user_id: int = 0,
) -> AsyncGenerator[dict, None]:
    """
    Asynchronously yield member dicts scraped from *group_input*.

    Each yielded dict has keys:
        user_id, username, first_name, last_name,
        phone, is_bot, is_premium, access_hash

    The generator honours the cancel flag (states.is_cancelled)
    so the user can abort mid-scrape.

    Parameters
    ----------
    session_string : str          — Telethon StringSession.
    api_id         : int          — API ID.
    api_hash       : str          — API hash.
    group_input    : str          — Group username / link.
    limit          : int | None   — Max members to scrape; None = all.
    user_id        : int          — Operator's Telegram ID (for cancel check).

    Yields
    ------
    dict
        One dict per member scraped.
    """
    client = build_client(session_string, api_id, api_hash)

    async with client:
        group = await resolve_group(client, group_input)
        if group is None:
            logger.error("[ENGINE] scrape_members: could not resolve group")
            return

        logger.info(
            f"[ENGINE] Starting scrape of '{group_input}' "
            f"limit={limit} for user={user_id}"
        )

        count = 0

        # Telethon's iter_participants is the primary scrape method.
        # It pages through the full member list automatically.
        async for participant in client.iter_participants(
            group,
            aggressive=False,   # aggressive=True triggers flood more easily
        ):
            # Honour cancel flag
            if user_id and states.is_cancelled(user_id):
                logger.info(f"[ENGINE] Scrape cancelled by user={user_id}")
                return

            # Honour limit
            if limit is not None and count >= limit:
                return

            # Skip deleted accounts and bots
            if participant.deleted:
                continue

            # Build the record
            member: dict = {
                "user_id":     participant.id,
                "username":    participant.username or "",
                "first_name":  participant.first_name or "",
                "last_name":   participant.last_name  or "",
                "phone":       participant.phone      or "",
                "is_bot":      int(participant.bot),
                "is_premium":  int(getattr(participant, "premium", False)),
                "access_hash": participant.access_hash or 0,
            }

            count += 1
            yield member

        logger.info(f"[ENGINE] Scrape complete — {count} members yielded")


# ── Member adder ──────────────────────────────────────────────

async def add_members(
    session_string: str,
    api_id: int,
    api_hash: str,
    target_group_input: str,
    members: list[dict],
    delay: int = config.ADD_DELAY_SECONDS,
    user_id: int = 0,
) -> AsyncGenerator[dict, None]:
    """
    Asynchronously attempt to add each member dict to *target_group_input*
    and yield a status dict for each attempt.

    Each yielded dict has keys:
        index, user_id, username, status, error

    Status values:
        'added'     — successfully added
        'skipped'   — privacy restriction / already a member / flood
        'error'     — unexpected error (logged)
        'cancelled' — user requested abort

    Parameters
    ----------
    session_string      : str   — Telethon StringSession.
    api_id              : int   — API ID.
    api_hash            : str   — API hash.
    target_group_input  : str   — Target group username / link.
    members             : list[dict] — List of member dicts (from scrape).
    delay               : int   — Seconds to wait between each add.
    user_id             : int   — Operator's Telegram ID (for cancel check).

    Yields
    ------
    dict
        Status dict for each add attempt.
    """
    client = build_client(session_string, api_id, api_hash)

    async with client:
        target = await resolve_group(client, target_group_input)
        if target is None:
            logger.error("[ENGINE] add_members: could not resolve target group")
            return

        logger.info(
            f"[ENGINE] Starting add to '{target_group_input}' "
            f"— {len(members)} members, delay={delay}s, user={user_id}"
        )

        for idx, member in enumerate(members):
            # ── Cancel check ──────────────────────────────────
            if user_id and states.is_cancelled(user_id):
                logger.info(f"[ENGINE] Add cancelled by user={user_id}")
                yield {
                    "index":    idx,
                    "user_id":  member["user_id"],
                    "username": member.get("username", ""),
                    "status":   "cancelled",
                    "error":    "",
                }
                return

            username   = member.get("username", "")
            m_user_id  = member["user_id"]
            access_hash= member.get("access_hash", 0)
            status     = "skipped"
            error_msg  = ""

            try:
                # Prefer username resolution; fall back to InputPeerUser
                if username:
                    user_to_add = await client.get_entity(username)
                else:
                    user_to_add = types.InputPeerUser(
                        user_id     = m_user_id,
                        access_hash = access_hash,
                    )

                await client(functions.channels.InviteToChannelRequest(
                    channel = target,
                    users   = [user_to_add],
                ))
                status = "added"
                logger.debug(f"[ENGINE] Added user={m_user_id} (@{username})")

            except errors.FloodWaitError as exc:
                wait_sec = exc.seconds
                logger.warning(f"[ENGINE] FloodWait {wait_sec}s — pausing")
                error_msg = f"flood_wait:{wait_sec}"
                status    = "skipped"
                # Honour the flood wait then continue
                await asyncio.sleep(wait_sec)

            except errors.UserPrivacyRestrictedError:
                error_msg = "privacy_restricted"
                status    = "skipped"

            except errors.UserAlreadyParticipantError:
                error_msg = "already_member"
                status    = "skipped"

            except errors.UserNotMutualContactError:
                error_msg = "not_mutual_contact"
                status    = "skipped"

            except errors.InputUserDeactivatedError:
                error_msg = "account_deleted"
                status    = "skipped"

            except errors.PeerFloodError:
                # Account-level flood; abort the whole run
                logger.error("[ENGINE] PeerFlood — aborting add session")
                error_msg = "peer_flood"
                status    = "skipped"
                yield {
                    "index":    idx,
                    "user_id":  m_user_id,
                    "username": username,
                    "status":   status,
                    "error":    error_msg,
                }
                return

            except Exception as exc:
                logger.error(
                    f"[ENGINE] Unexpected error adding user={m_user_id}: {exc}"
                )
                error_msg = str(exc)[:120]
                status    = "error"

            yield {
                "index":    idx,
                "user_id":  m_user_id,
                "username": username,
                "status":   status,
                "error":    error_msg,
            }

            # ── Inter-add delay ───────────────────────────────
            if status == "added":
                await asyncio.sleep(delay)
            else:
                # Short pause even on skips to avoid hammering Telegram
                await asyncio.sleep(1)

        logger.info("[ENGINE] Add loop complete")


# ── CSV Export ────────────────────────────────────────────────

def export_to_csv(
    members: list[dict],
    output_path: Optional[str] = None,
) -> str:
    """
    Write a list of member dicts to a CSV file.

    Parameters
    ----------
    members     : list[dict]    — Member records from scrape_members.
    output_path : str | None    — Full file path; if None a temp file is created.

    Returns
    -------
    str
        Absolute path to the written CSV file.
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".csv", prefix="velyn_scrape_")
        os.close(fd)

    fieldnames = [
        "user_id", "username", "first_name", "last_name",
        "phone", "is_bot", "is_premium", "access_hash",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(members)

    logger.info(f"[ENGINE] CSV exported → {output_path} ({len(members)} rows)")
    return output_path


def load_from_csv(file_path: str) -> list[dict]:
    """
    Read a previously-exported scrape CSV back into a list of dicts.

    Parameters
    ----------
    file_path : str — Path to the CSV file.

    Returns
    -------
    list[dict]
        List of member dicts with the same keys as scrape_members yields.
    """
    members: list[dict] = []

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Cast numeric fields back to int
            try:
                row["user_id"]     = int(row.get("user_id", 0) or 0)
                row["access_hash"] = int(row.get("access_hash", 0) or 0)
                row["is_bot"]      = int(row.get("is_bot", 0) or 0)
                row["is_premium"]  = int(row.get("is_premium", 0) or 0)
            except ValueError:
                pass
            members.append(dict(row))

    logger.info(f"[ENGINE] CSV loaded ← {file_path} ({len(members)} rows)")
    return members


# ── OTP / Session creation helpers ───────────────────────────

async def create_session_send_code(
    phone: str,
    api_id: int,
    api_hash: str,
) -> tuple[TelegramClient, str]:
    """
    Connect a fresh Telethon client, request an OTP for *phone*, and
    return the client + phone_code_hash for the subsequent sign-in call.

    The client is left CONNECTED; the caller is responsible for
    disconnecting it (or continuing the sign-in flow).

    Parameters
    ----------
    phone    : str — Phone number in international format (+91XXXXXXXXXX).
    api_id   : int
    api_hash : str

    Returns
    -------
    tuple[TelegramClient, str]
        (connected_client, phone_code_hash)

    Raises
    ------
    Various Telethon errors (FloodWaitError, PhoneNumberInvalidError, …).
    """
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    result = await client.send_code_request(phone)
    return client, result.phone_code_hash


async def create_session_sign_in(
    client: TelegramClient,
    phone: str,
    phone_code_hash: str,
    code: str,
    password: Optional[str] = None,
) -> str:
    """
    Complete the sign-in flow and return a StringSession string.

    Parameters
    ----------
    client          : TelegramClient — Connected client from create_session_send_code.
    phone           : str            — Same phone number used in send_code.
    phone_code_hash : str            — Hash returned by send_code_request.
    code            : str            — The OTP code the user received.
    password        : str | None     — 2FA password if the account has one.

    Returns
    -------
    str
        The StringSession string; persist this to DB.

    Raises
    ------
    errors.SessionPasswordNeededError — caller must re-call with password.
    Various other Telethon auth errors.
    """
    try:
        await client.sign_in(
            phone           = phone,
            code            = code,
            phone_code_hash = phone_code_hash,
        )
    except errors.SessionPasswordNeededError:
        if password is None:
            raise
        await client.sign_in(password=password)

    session_str = client.session.save()
    await client.disconnect()
    return session_str
