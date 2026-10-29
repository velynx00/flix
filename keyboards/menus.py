# ============================================================
# keyboards/menus.py — All Inline Keyboards for Velyn Nox Premium
# ============================================================

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
    return _kb([
        [
            InlineKeyboardButton(
                f"⟢ {LABEL_SCRAPE.upper()}",
                callback_data="menu:scrape",
                style="primary",
            ),
            InlineKeyboardButton(
                f"✦ {LABEL_ADD.upper()}",
                callback_data="menu:add",
                style="success",
            ),
        ],
        [
            InlineKeyboardButton(
                f"★ {LABEL_PREMIUM.upper()}",
                callback_data="menu:premium",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚡ {LABEL_UPDATES.upper()}",
                url=config.UPDATE_CHANNEL_URL,
                style="danger",
            ),
        ],
    ])


# ── Scraper Menu ──────────────────────────────────────────────

def scrape_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"⟢ {sc('start scrape')}",
                callback_data="scrape:start",
                style="success",
            ),
        ],
        [
            InlineKeyboardButton(
                f"📄 {LABEL_EXPORT}",
                callback_data="scrape:export",
                style="primary",
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
                style="danger",
            ),
        ],
    ])


# ── Add Menu ──────────────────────────────────────────────────

def add_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"✦ {sc('start adding')}",
                callback_data="add:start",
                style="success",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
                style="danger",
            ),
        ],
    ])


# ── Premium Menu ──────────────────────────────────────────────

def premium_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"★ {sc('upgrade to premium')}",
                callback_data="premium:upgrade",
                style="success",
            ),
        ],
        [
            InlineKeyboardButton(
                f"📋 {LABEL_MYPLAN}",
                callback_data="premium:myplan",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚡ {LABEL_UPDATES}",
                url=config.UPDATE_CHANNEL_URL,
                style="danger",
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
                style="primary",
            ),
        ],
    ]
    if is_owner:
        rows.insert(0, [
            InlineKeyboardButton(
                f"🛡 {LABEL_ADMIN}",
                callback_data="admin:panel",
                style="danger",
            ),
        ])
    return _kb(rows)


# ── Admin Panel ───────────────────────────────────────────────

def admin_panel() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"📊 {LABEL_STATS}",
                callback_data="admin:stats",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                f"✅ {LABEL_GRANT}",
                callback_data="admin:grant",
                style="success",
            ),
            InlineKeyboardButton(
                f"❌ {LABEL_REVOKE_P}",
                callback_data="admin:revoke_premium",
                style="danger",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🔑 {LABEL_REVOKE}",
                callback_data="admin:revoke_session",
                style="danger",
            ),
        ],
        [
            InlineKeyboardButton(
                f"📢 {LABEL_BCAST}",
                callback_data="admin:broadcast",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
                style="danger",
            ),
        ],
    ])


# ── Premium Plan Selector ─────────────────────────────────────

def plan_selector() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"⚡ {sc('trial')} (1 day)",
                callback_data="plan:trial",
                style="primary",
            ),
            InlineKeyboardButton(
                f"📅 {sc('weekly')} (7 days)",
                callback_data="plan:weekly",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🗓 {sc('monthly')} (30 days)",
                callback_data="plan:monthly",
                style="primary",
            ),
            InlineKeyboardButton(
                f"♾ {sc('yearly')} (365 days)",
                callback_data="plan:yearly",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_CANCEL}",
                callback_data="admin:panel",
                style="danger",
            ),
        ],
    ])


# ── Confirmation Dialog ───────────────────────────────────────

def confirm_action(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"✅ {LABEL_YES}",  
                callback_data=yes_data, 
                style="success"
            ),
            InlineKeyboardButton(
                f"❌ {LABEL_NO}",   
                callback_data=no_data,  
                style="danger"
            ),
        ],
    ])


# ── Session Setup ─────────────────────────────────────────────

def session_menu(has_session: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"🔑 {sc('setup session')}",
                callback_data="session:setup",
                style="success",
            ),
        ],
    ]
    if has_session:
        rows.append([
            InlineKeyboardButton(
                f"🗑 {LABEL_REVOKE}",
                callback_data="session:revoke",
                style="danger",
            ),
        ])
    rows.append([
        InlineKeyboardButton(
            f"↩ {LABEL_BACK}", 
            callback_data="menu:back",
            style="danger"
        ),
    ])
    return _kb(rows)


# ── API Credentials Input ─────────────────────────────────────

def api_choice_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"🔧 {sc('use my own api')}",
                callback_data="api:custom",
                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚡ {sc('use default api')}",
                callback_data="api:default",
                style="success",
            ),
        ],
        [
            InlineKeyboardButton(
                f"↩ {LABEL_CANCEL}",
                callback_data="menu:back",
                style="danger",
            ),
        ],
    ])


# ── Cancel / Stop Running Operation ──────────────────────────

def cancel_operation() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"⛔ {sc('stop operation')}",
                callback_data="op:cancel",
                style="danger",
            ),
        ],
    ])


# ── Status / My Plan ─────────────────────────────────────────

def status_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"🔄 {sc('refresh')}",
                callback_data="status:refresh",
                style="primary",
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_BACK}",
                callback_data="menu:back",
                style="danger",
            ),
        ],
    ])


# ── Session OTP Input ─────────────────────────────────────────

def otp_resend_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(
                f"📲 {sc('resend code')}",
                callback_data="otp:resend",
                style="primary",
            ),
            InlineKeyboardButton(
                f"↩ {LABEL_CANCEL}",
                callback_data="otp:cancel",
                style="danger",
            ),
        ],
    ])
