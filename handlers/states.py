# ============================================================
# handlers/states.py — Conversation State Machine (NO ConversationHandler)
#
# Instead of python-telegram-bot's ConversationHandler, we use a
# plain in-memory dictionary keyed by user_id to track which
# "step" each user is currently in.  This avoids the complexity
# of ConversationHandler while still being fully stateful.
#
# State lifecycle:
#   set_state(user_id, STATE_*)   — enter a state
#   get_state(user_id)            — query current state
#   clear_state(user_id)          — exit / reset
#   get_data / set_data / clear_data — per-user scratch-pad
# ============================================================

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── State Constants ───────────────────────────────────────────
# Naming convention: MODULE_STEP

# ─── Session / API Setup ─────────────────────────────────────
STATE_SESSION_AWAITING_PHONE      = "session:awaiting_phone"
STATE_SESSION_AWAITING_CODE       = "session:awaiting_code"
STATE_SESSION_AWAITING_PASSWORD   = "session:awaiting_2fa_password"
STATE_SESSION_AWAITING_API_ID     = "session:awaiting_api_id"
STATE_SESSION_AWAITING_API_HASH   = "session:awaiting_api_hash"

# ─── Scrape Flow ─────────────────────────────────────────────
STATE_SCRAPE_AWAITING_GROUP       = "scrape:awaiting_group"

# ─── Add Flow ────────────────────────────────────────────────
STATE_ADD_AWAITING_SOURCE_CSV     = "add:awaiting_source_csv"
STATE_ADD_AWAITING_TARGET_GROUP   = "add:awaiting_target_group"

# ─── Admin Actions ────────────────────────────────────────────
STATE_ADMIN_AWAITING_GRANT_ID     = "admin:awaiting_grant_id"
STATE_ADMIN_AWAITING_REVOKE_ID    = "admin:awaiting_revoke_id"
STATE_ADMIN_AWAITING_SESSION_ID   = "admin:awaiting_session_revoke_id"
STATE_ADMIN_AWAITING_BROADCAST    = "admin:awaiting_broadcast_text"
STATE_ADMIN_GRANT_SELECT_PLAN     = "admin:grant_select_plan"

# ─── Sentinel: no active state ────────────────────────────────
STATE_IDLE = None


# ── In-memory stores ──────────────────────────────────────────
# _states : user_id → state string (or None)
# _data   : user_id → dict of scratch-pad key/value pairs

_states: dict[int, Optional[str]] = {}
_data:   dict[int, dict[str, Any]] = {}


# ── State accessors ───────────────────────────────────────────

def set_state(user_id: int, state: Optional[str]) -> None:
    """
    Transition *user_id* into the given *state*.

    Parameters
    ----------
    user_id : int           — Telegram user ID.
    state   : str | None    — One of the STATE_* constants, or None to clear.
    """
    _states[user_id] = state
    logger.debug(f"[STATE] user={user_id} → {state!r}")


def get_state(user_id: int) -> Optional[str]:
    """
    Return the current state for *user_id*, or None if idle.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    str | None
    """
    return _states.get(user_id, STATE_IDLE)


def clear_state(user_id: int) -> None:
    """
    Reset *user_id* to the idle state.

    Parameters
    ----------
    user_id : int
    """
    _states.pop(user_id, None)
    logger.debug(f"[STATE] user={user_id} → IDLE (cleared)")


def is_idle(user_id: int) -> bool:
    """
    Return True if the user is not in any active state.

    Parameters
    ----------
    user_id : int
    """
    return get_state(user_id) is STATE_IDLE


# ── Scratch-pad data helpers ──────────────────────────────────

def set_data(user_id: int, key: str, value: Any) -> None:
    """
    Store an arbitrary value in the user's scratch-pad dict.

    Parameters
    ----------
    user_id : int
    key     : str — Identifier for the stored value.
    value   : Any — Any pickleable value.
    """
    if user_id not in _data:
        _data[user_id] = {}
    _data[user_id][key] = value


def get_data(user_id: int, key: str, default: Any = None) -> Any:
    """
    Retrieve a value from the user's scratch-pad dict.

    Parameters
    ----------
    user_id : int
    key     : str    — The key to look up.
    default : Any    — Returned if key is absent (default None).

    Returns
    -------
    Any
    """
    return _data.get(user_id, {}).get(key, default)


def clear_data(user_id: int) -> None:
    """
    Wipe the entire scratch-pad for *user_id*.

    Parameters
    ----------
    user_id : int
    """
    _data.pop(user_id, None)


def clear_all(user_id: int) -> None:
    """
    Clear both the state and scratch-pad for *user_id*.
    Call this at the end of any completed or cancelled flow.

    Parameters
    ----------
    user_id : int
    """
    clear_state(user_id)
    clear_data(user_id)


def get_all_data(user_id: int) -> dict[str, Any]:
    """
    Return the full scratch-pad dict for *user_id* (read-only snapshot).

    Parameters
    ----------
    user_id : int

    Returns
    -------
    dict[str, Any]
    """
    return dict(_data.get(user_id, {}))


# ── Operation cancel flag ─────────────────────────────────────
# Separate from the state machine — a boolean flag that the
# engine checks each iteration to honour a mid-flight cancel.

_cancel_flags: dict[int, bool] = {}


def request_cancel(user_id: int) -> None:
    """
    Signal that the user wants to cancel their current operation.

    Parameters
    ----------
    user_id : int
    """
    _cancel_flags[user_id] = True
    logger.info(f"[STATE] Cancel requested for user={user_id}")


def is_cancelled(user_id: int) -> bool:
    """
    Return True if a cancel has been requested for this user.

    Parameters
    ----------
    user_id : int
    """
    return _cancel_flags.get(user_id, False)


def clear_cancel(user_id: int) -> None:
    """
    Reset the cancel flag after the operation has acknowledged it.

    Parameters
    ----------
    user_id : int
    """
    _cancel_flags.pop(user_id, None)
