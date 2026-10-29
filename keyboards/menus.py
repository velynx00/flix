# ============================================================
# keyboards/menus.py — All Inline Keyboards for Velyn Nox Premium
#
# Every keyboard is a standalone function returning an
# InlineKeyboardMarkup.  Button labels use sc() from utils.text
# so all text is rendered in small-caps Unicode.
# ============================================================

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import config
from utils.text import (
    sc, LABEL_SCRAPE, LABEL_ADD, LABEL_PREMIUM, LABEL_UPDATES,
    LABEL_CANCEL, LABEL_BACK, LABEL_DONE, LABEL_STATUS,
    LABEL_SESSIONS, LABEL_MYPLAN, LABEL_HELP, LABEL_YES, LABEL_NO,
    LABEL_REVOKE, LABEL_EXPORT, LABEL_GRANT, LABEL_REVOKE_P,
    LABEL_STATS, LABEL_BCAST, LABEL_ADMIN,
)


# ── Helper ────────────────────────────────────────────────────

def _kb(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    """Shorthand wrapper around InlineKeyboardMarkup."""
    return InlineKeyboardMarkup(rows)


# ── Main Menu ─────────────────────────────────────────────────

def main_menu() -> InlineKeyboardMarkup:
    """
    The primary menu shown with the /start welcome message.

    Buttons (with Telegram Bot API 9.4-style colour hints via text):
        Row 1 : [Scrape ⟢]  [Add ✦]
        Row 2 : [Premium ★]
        Row 3 : [Updates ⚡]  (URL button)

    Returns
    -------
    InlineKeyboardMarkup
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"⟢ {LABEL_SCRAPE.upper()}",
                callback_data="menu:scrape",
            ),
            InlineKeyboardButton(
                f"✦ {LABEL_ADD.upper()}",
                callback_data="menu:add",
            ),
        ],
        [
            InlineKeyboardButton(
                f"★ {LABEL_PREMIUM.upper()}",
                callback_data="menu:premium",
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚡ {LABEL_UPDATES.upper()}",
                url=config.UPDATE_CHANNEL_URL,
            ),
        ],
    ])


# ── Scraper Menu ──────────────────────────────────────────────

def scrape_menu() -> InlineKeyboardMarkup:
    """
    Menu shown at the start of the scrape flow.

    Options:
        [Start Scrape]  [Export CSV]  [Back]
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"⟢ {sc('start scrape')}",
                callback_data="scrape:start",
            ),
        ],
        [
            InlineKeyboardButton(
                f"📄 {LABEL_EXPORT}",
                callback_data="scrape:export",
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
            ),
        ],
    ])


# ── Add Menu ──────────────────────────────────────────────────

def add_menu() -> InlineKeyboardMarkup:
    """
    Menu shown at the start of the add-members flow.

    Options:
        [Start Adding]  [Back]
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"✦ {sc('start adding')}",
                callback_data="add:start",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
            ),
        ],
    ])


# ── Premium Menu ──────────────────────────────────────────────

def premium_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    """
    Premium information / upgrade menu.

    Parameters
    ----------
    is_owner : bool
        When True, an extra [Admin Panel] shortcut button is added.

    Returns
    -------
    InlineKeyboardMarkup
    """
    rows = [
        [
            InlineKeyboardButton(
                f"★ {sc('upgrade to premium')}",
                callback_data="premium:upgrade",
            ),
        ],
        [
            InlineKeyboardButton(
                f"📋 {LABEL_MYPLAN}",
                callback_data="premium:myplan",
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚡ {LABEL_UPDATES}",
                url=config.UPDATE_CHANNEL_URL,
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
            ),
        ],
    ]
    if is_owner:
        rows.insert(0, [
            InlineKeyboardButton(
                f"🛡 {LABEL_ADMIN}",
                callback_data="admin:panel",
            ),
        ])
    return _kb(rows)


# ── Admin Panel ───────────────────────────────────────────────

def admin_panel() -> InlineKeyboardMarkup:
    """
    The top-level admin panel keyboard.

    Sections:
        Row 1 : [Bot Stats]
        Row 2 : [Grant Premium]  [Revoke Premium]
        Row 3 : [Revoke Session]
        Row 4 : [Broadcast]
        Row 5 : [Back]
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"📊 {LABEL_STATS}",
                callback_data="admin:stats",
            ),
        ],
        [
            InlineKeyboardButton(
                f"✅ {LABEL_GRANT}",
                callback_data="admin:grant",
            ),
            InlineKeyboardButton(
                f"❌ {LABEL_REVOKE_P}",
                callback_data="admin:revoke_premium",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🔑 {LABEL_REVOKE}",
                callback_data="admin:revoke_session",
            ),
        ],
        [
            InlineKeyboardButton(
                f"📢 {LABEL_BCAST}",
                callback_data="admin:broadcast",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
            ),
        ],
    ])


# ── Premium Plan Selector ─────────────────────────────────────

def plan_selector() -> InlineKeyboardMarkup:
    """
    Keyboard for the admin to select which premium plan to grant.

    Plans map to config.PLAN_DURATIONS.
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"⚡ {sc('trial')} (1 day)",
                callback_data="plan:trial",
            ),
            InlineKeyboardButton(
                f"📅 {sc('weekly')} (7 days)",
                callback_data="plan:weekly",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🗓 {sc('monthly')} (30 days)",
                callback_data="plan:monthly",
            ),
            InlineKeyboardButton(
                f"♾ {sc('yearly')} (365 days)",
                callback_data="plan:yearly",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_CANCEL}",
                callback_data="admin:panel",
            ),
        ],
    ])


# ── Confirmation Dialog ───────────────────────────────────────

def confirm_action(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    """
    A generic Yes / No confirmation keyboard.

    Parameters
    ----------
    yes_data : str — callback_data for the confirm button.
    no_data  : str — callback_data for the cancel button.

    Returns
    -------
    InlineKeyboardMarkup
    """
    return _kb([
        [
            InlineKeyboardButton(f"✅ {LABEL_YES}", callback_data=yes_data),
            InlineKeyboardButton(f"❌ {LABEL_NO}",  callback_data=no_data),
        ],
    ])


# ── Session Setup ─────────────────────────────────────────────

def session_menu(has_session: bool) -> InlineKeyboardMarkup:
    """
    Keyboard shown during the Telethon session setup.

    Parameters
    ----------
    has_session : bool
        If True, a [Revoke Session] button is shown in addition to [Setup].

    Returns
    -------
    InlineKeyboardMarkup
    """
    rows = [
        [
            InlineKeyboardButton(
                f"🔑 {sc('setup session')}",
                callback_data="session:setup",
            ),
        ],
    ]
    if has_session:
        rows.append([
            InlineKeyboardButton(
                f"🗑 {LABEL_REVOKE}",
                callback_data="session:revoke",
            ),
        ])
    rows.append([
        InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back"),
    ])
    return _kb(rows)


# ── API Credentials Input ─────────────────────────────────────

def api_choice_menu() -> InlineKeyboardMarkup:
    """
    Let user choose between using their own API creds or the default ones.
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"🔧 {sc('use my own api')}",
                callback_data="api:custom",
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚡ {sc('use default api')}",
                callback_data="api:default",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_CANCEL}",
                callback_data="menu:back",
            ),
        ],
    ])


# ── Cancel / Stop Running Operation ──────────────────────────

def cancel_operation() -> InlineKeyboardMarkup:
    """
    Single-button keyboard shown while a scrape/add is running.
    Lets the user abort mid-operation.
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"⛔ {sc('stop operation')}",
                callback_data="op:cancel",
            ),
        ],
    ])


# ── Status / My Plan ─────────────────────────────────────────

def status_menu() -> InlineKeyboardMarkup:
    """
    Keyboard appended to /status and /myplan replies.
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"🔄 {sc('refresh')}",
                callback_data="status:refresh",
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
            ),
        ],
    ])


# ── Session OTP Input ─────────────────────────────────────────

def otp_resend_menu() -> InlineKeyboardMarkup:
    """
    Shown after the OTP code is requested — lets user resend or cancel.
    """
    return _kb([
        [
            InlineKeyboardButton(
                f"📲 {sc('resend code')}",
                callback_data="otp:resend",
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_CANCEL}",
                callback_data="otp:cancel",
            ),
        ],
    ])
