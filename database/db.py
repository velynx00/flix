# ============================================================
# database/db.py — SQLite Database Layer for Velyn Nox Premium
#
# Tables:
#   users            — Every user who has started the bot.
#   premium          — Premium grants (who, when, until, plan).
#   telethon_sessions— Per-user Telethon string sessions + API creds.
#   operations       — Audit log of every scrape / add operation.
#
# All public functions are synchronous; the bot layer calls them
# from async handlers using run_in_executor where needed or simply
# directly (SQLite I/O is fast enough for bot scale).
# ============================================================

from __future__ import annotations

import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import config

logger = logging.getLogger(__name__)

# ── Internal helpers ──────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """
    Open (or reuse) a SQLite connection to the database file defined
    in config.DATABASE_PATH.  Row factory is set so rows can be
    accessed as both index and key.

    Returns
    -------
    sqlite3.Connection
    """
    conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")   # improves concurrent read perf
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


# Module-level single connection (bot runs in one process)
_conn: sqlite3.Connection = _get_connection()


# ── Schema Initialisation ─────────────────────────────────────

def init_db() -> None:
    """
    Create all required tables if they do not already exist.
    Called once at bot startup from main.py.

    Tables created:
        - users
        - premium
        - telethon_sessions
        - operations
    """
    logger.info("[DB] Initialising database schema …")

    _conn.executescript("""
        -- ── users ─────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY,
            username        TEXT,
            full_name       TEXT,
            joined_at       TEXT    NOT NULL DEFAULT (datetime('now')),
            last_seen       TEXT    NOT NULL DEFAULT (datetime('now')),
            is_banned       INTEGER NOT NULL DEFAULT 0,
            total_scrapes   INTEGER NOT NULL DEFAULT 0,
            total_adds      INTEGER NOT NULL DEFAULT 0
        );

        -- ── premium ────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS premium (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            plan            TEXT    NOT NULL DEFAULT 'monthly',
            granted_by      INTEGER NOT NULL,
            granted_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            expires_at      TEXT    NOT NULL,
            is_active       INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        -- ── telethon_sessions ──────────────────────────────────
        CREATE TABLE IF NOT EXISTS telethon_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL UNIQUE,
            session_string  TEXT    NOT NULL,
            api_id          INTEGER NOT NULL,
            api_hash        TEXT    NOT NULL,
            phone           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            last_used       TEXT    NOT NULL DEFAULT (datetime('now')),
            is_active       INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        -- ── operations ─────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS operations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            op_type         TEXT    NOT NULL,   -- 'scrape' | 'add'
            target_group    TEXT,
            count           INTEGER NOT NULL DEFAULT 0,
            status          TEXT    NOT NULL DEFAULT 'pending',
            started_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            finished_at     TEXT,
            error_msg       TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    _conn.commit()
    logger.info("[DB] Schema ready.")


# ── Users ─────────────────────────────────────────────────────

def upsert_user(
    user_id: int,
    username: Optional[str],
    full_name: str,
) -> None:
    """
    Insert a new user row or update username / full_name and last_seen
    if the user already exists.

    Parameters
    ----------
    user_id   : int           — Telegram user ID.
    username  : str | None    — Telegram @username (may be None).
    full_name : str           — User's display name.
    """
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    _conn.execute(
        """
        INSERT INTO users (user_id, username, full_name, joined_at, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username  = excluded.username,
            full_name = excluded.full_name,
            last_seen = excluded.last_seen
        """,
        (user_id, username, full_name, now, now),
    )
    _conn.commit()


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    """
    Fetch a single user row by Telegram ID.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    sqlite3.Row | None
        The row if found, else None.
    """
    cur = _conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    )
    return cur.fetchone()


def get_all_users() -> list[sqlite3.Row]:
    """
    Fetch every user row — used by the broadcast feature.

    Returns
    -------
    list[sqlite3.Row]
    """
    cur = _conn.execute("SELECT * FROM users WHERE is_banned = 0")
    return cur.fetchall()


def get_user_count() -> int:
    """
    Return the total number of registered (non-banned) users.

    Returns
    -------
    int
    """
    cur = _conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 0")
    return cur.fetchone()[0]


def ban_user(user_id: int) -> None:
    """
    Set is_banned = 1 for the given user.

    Parameters
    ----------
    user_id : int
    """
    _conn.execute(
        "UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,)
    )
    _conn.commit()


def unban_user(user_id: int) -> None:
    """
    Set is_banned = 0 for the given user.

    Parameters
    ----------
    user_id : int
    """
    _conn.execute(
        "UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,)
    )
    _conn.commit()


def is_banned(user_id: int) -> bool:
    """
    Check whether a user is currently banned.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    bool
    """
    row = get_user(user_id)
    if row is None:
        return False
    return bool(row["is_banned"])


def increment_scrape_count(user_id: int, amount: int = 1) -> None:
    """
    Increment the user's total_scrapes counter.

    Parameters
    ----------
    user_id : int
    amount  : int — How much to add (default 1).
    """
    _conn.execute(
        "UPDATE users SET total_scrapes = total_scrapes + ? WHERE user_id = ?",
        (amount, user_id),
    )
    _conn.commit()


def increment_add_count(user_id: int, amount: int = 1) -> None:
    """
    Increment the user's total_adds counter.

    Parameters
    ----------
    user_id : int
    amount  : int — How much to add (default 1).
    """
    _conn.execute(
        "UPDATE users SET total_adds = total_adds + ? WHERE user_id = ?",
        (amount, user_id),
    )
    _conn.commit()


# ── Premium ───────────────────────────────────────────────────

def grant_premium(
    user_id: int,
    plan: str,
    granted_by: int,
    days: Optional[int] = None,
) -> None:
    """
    Grant premium access to a user.

    If the user already has an active premium row it is deactivated
    and a fresh row is inserted (so renewal stacks from today, not from
    the old expiry).

    Parameters
    ----------
    user_id    : int          — Recipient's Telegram ID.
    plan       : str          — Plan name key (e.g. 'monthly').
    granted_by : int          — Admin's Telegram ID performing the grant.
    days       : int | None   — Override duration in days; falls back to
                                config.PLAN_DURATIONS[plan].
    """
    if days is None:
        days = config.PLAN_DURATIONS.get(plan, 30)

    now = datetime.utcnow()
    expires = now + timedelta(days=days)
    now_str     = now.isoformat(sep=" ", timespec="seconds")
    expires_str = expires.isoformat(sep=" ", timespec="seconds")

    # Deactivate any existing active plan first.
    _conn.execute(
        "UPDATE premium SET is_active = 0 WHERE user_id = ? AND is_active = 1",
        (user_id,),
    )

    _conn.execute(
        """
        INSERT INTO premium (user_id, plan, granted_by, granted_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (user_id, plan, granted_by, now_str, expires_str),
    )
    _conn.commit()


def revoke_premium(user_id: int) -> None:
    """
    Deactivate all active premium rows for the given user.

    Parameters
    ----------
    user_id : int
    """
    _conn.execute(
        "UPDATE premium SET is_active = 0 WHERE user_id = ? AND is_active = 1",
        (user_id,),
    )
    _conn.commit()


def is_premium(user_id: int) -> bool:
    """
    Return True if the user has a currently active premium grant that
    has not yet expired.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    bool
    """
    now_str = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    cur = _conn.execute(
        """
        SELECT id FROM premium
        WHERE user_id = ?
          AND is_active = 1
          AND expires_at > ?
        LIMIT 1
        """,
        (user_id, now_str),
    )
    return cur.fetchone() is not None


def get_premium_info(user_id: int) -> Optional[sqlite3.Row]:
    """
    Fetch the most recent active premium row for a user.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    sqlite3.Row | None
    """
    now_str = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    cur = _conn.execute(
        """
        SELECT * FROM premium
        WHERE user_id = ?
          AND is_active = 1
          AND expires_at > ?
        ORDER BY granted_at DESC
        LIMIT 1
        """,
        (user_id, now_str),
    )
    return cur.fetchone()


def get_premium_user_count() -> int:
    """
    Count how many users currently have active premium.

    Returns
    -------
    int
    """
    now_str = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    cur = _conn.execute(
        """
        SELECT COUNT(DISTINCT user_id) FROM premium
        WHERE is_active = 1 AND expires_at > ?
        """,
        (now_str,),
    )
    return cur.fetchone()[0]


# ── Telethon Sessions ─────────────────────────────────────────

def save_session(
    user_id: int,
    session_string: str,
    api_id: int,
    api_hash: str,
    phone: Optional[str] = None,
) -> None:
    """
    Persist a Telethon StringSession for a user.
    If a row for this user already exists, it is fully replaced.

    Parameters
    ----------
    user_id        : int          — Telegram user ID.
    session_string : str          — Telethon StringSession string.
    api_id         : int          — The API ID used for this session.
    api_hash       : str          — The API hash used for this session.
    phone          : str | None   — Phone number associated with the session.
    """
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    _conn.execute(
        """
        INSERT INTO telethon_sessions
            (user_id, session_string, api_id, api_hash, phone, created_at, last_used, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            session_string = excluded.session_string,
            api_id         = excluded.api_id,
            api_hash       = excluded.api_hash,
            phone          = excluded.phone,
            last_used      = excluded.last_used,
            is_active      = 1
        """,
        (user_id, session_string, api_id, api_hash, phone, now, now),
    )
    _conn.commit()


def get_session(user_id: int) -> Optional[sqlite3.Row]:
    """
    Retrieve the active Telethon session row for a user.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    sqlite3.Row | None
        Row with columns: session_string, api_id, api_hash, phone, etc.
    """
    cur = _conn.execute(
        "SELECT * FROM telethon_sessions WHERE user_id = ? AND is_active = 1",
        (user_id,),
    )
    return cur.fetchone()


def delete_session(user_id: int) -> None:
    """
    Deactivate (not delete) a user's Telethon session.

    Parameters
    ----------
    user_id : int
    """
    _conn.execute(
        "UPDATE telethon_sessions SET is_active = 0 WHERE user_id = ?",
        (user_id,),
    )
    _conn.commit()


def has_session(user_id: int) -> bool:
    """
    Return True if the user has an active stored Telethon session.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    bool
    """
    return get_session(user_id) is not None


def update_session_last_used(user_id: int) -> None:
    """
    Refresh the last_used timestamp on a session row.

    Parameters
    ----------
    user_id : int
    """
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    _conn.execute(
        "UPDATE telethon_sessions SET last_used = ? WHERE user_id = ?",
        (now, user_id),
    )
    _conn.commit()


def get_session_count() -> int:
    """
    Count how many users have active Telethon sessions.

    Returns
    -------
    int
    """
    cur = _conn.execute(
        "SELECT COUNT(*) FROM telethon_sessions WHERE is_active = 1"
    )
    return cur.fetchone()[0]


# ── Operations (Audit Log) ────────────────────────────────────

def create_operation(
    user_id: int,
    op_type: str,
    target_group: Optional[str] = None,
) -> int:
    """
    Insert a new operation row with status 'pending' and return its ID.

    Parameters
    ----------
    user_id      : int          — User performing the operation.
    op_type      : str          — 'scrape' or 'add'.
    target_group : str | None   — Target group username / link.

    Returns
    -------
    int
        The newly-created operation row ID.
    """
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    cur = _conn.execute(
        """
        INSERT INTO operations (user_id, op_type, target_group, status, started_at)
        VALUES (?, ?, ?, 'pending', ?)
        """,
        (user_id, op_type, target_group, now),
    )
    _conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def finish_operation(
    op_id: int,
    count: int,
    status: str = "done",
    error_msg: Optional[str] = None,
) -> None:
    """
    Mark an operation as complete and record the result.

    Parameters
    ----------
    op_id     : int          — Operation row ID (from create_operation).
    count     : int          — How many records were scraped / users added.
    status    : str          — 'done', 'partial', or 'error'.
    error_msg : str | None   — Error detail if status != 'done'.
    """
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    _conn.execute(
        """
        UPDATE operations
        SET count       = ?,
            status      = ?,
            finished_at = ?,
            error_msg   = ?
        WHERE id = ?
        """,
        (count, status, now, error_msg, op_id),
    )
    _conn.commit()


def get_recent_operations(user_id: int, limit: int = 5) -> list[sqlite3.Row]:
    """
    Fetch the most recent operations for a given user.

    Parameters
    ----------
    user_id : int
    limit   : int — Maximum rows to return (default 5).

    Returns
    -------
    list[sqlite3.Row]
    """
    cur = _conn.execute(
        """
        SELECT * FROM operations
        WHERE user_id = ?
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    return cur.fetchall()


def get_total_operations() -> int:
    """
    Return the total number of completed operations across all users.

    Returns
    -------
    int
    """
    cur = _conn.execute(
        "SELECT COUNT(*) FROM operations WHERE status = 'done'"
    )
    return cur.fetchone()[0]


# ── Convenience: full user context ───────────────────────────

def get_full_user_context(user_id: int) -> dict:
    """
    Aggregate all relevant data for a user into one dict for display.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    dict with keys:
        user, is_premium, premium_info, has_session, session,
        recent_ops, is_banned
    """
    user          = get_user(user_id)
    prem          = is_premium(user_id)
    prem_info     = get_premium_info(user_id) if prem else None
    sess          = get_session(user_id)
    recent_ops    = get_recent_operations(user_id)
    banned        = is_banned(user_id)

    return {
        "user":         user,
        "is_premium":   prem,
        "premium_info": prem_info,
        "has_session":  sess is not None,
        "session":      sess,
        "recent_ops":   recent_ops,
        "is_banned":    banned,
    }
