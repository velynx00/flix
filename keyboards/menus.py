from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
from utils.text import sc, LABEL_CANCEL, LABEL_BACK, LABEL_YES, LABEL_NO, LABEL_EXPORT, LABEL_MYPLAN, LABEL_GRANT, LABEL_REVOKE_P, LABEL_STATS, LABEL_BCAST, LABEL_ADMIN, LABEL_REVOKE

def _kb(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(rows)

def main_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"⚡ {sc('ꜱᴄʀᴀᴘᴇ')}", callback_data="menu:scrape", style="primary"),
            InlineKeyboardButton(f"🔥 {sc('ᴀᴅᴅ')}", callback_data="menu:add", style="success"),
        ],
        [
            InlineKeyboardButton(f"💎 {sc('ᴘʀᴇᴍɪᴜᴍ')}", callback_data="menu:premium", style="primary"),
            InlineKeyboardButton(f"📢 {sc('ᴜᴘᴅᴀᴛᴇꜱ')}", url=config.UPDATE_CHANNEL_URL, style="danger"),
        ],
    ])

def scrape_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"⟢ {sc('ꜱᴛᴀʀᴛ ꜱᴄʀᴀᴘᴇ')}", callback_data="scrape:start", style="success")],
        [
            InlineKeyboardButton(f"📄 {LABEL_EXPORT}", callback_data="scrape:export", style="primary"),
            InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back", style="danger"),
        ],
    ])

def add_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"✦ {sc('ꜱᴛᴀʀᴛ ᴀᴅᴅɪɴɢ')}", callback_data="add:start", style="success")],
        [InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back", style="danger")],
    ])

def premium_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"★ {sc('ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ')}", callback_data="premium:upgrade", style="success")],
        [InlineKeyboardButton(f"📋 {LABEL_MYPLAN}", callback_data="premium:myplan", style="primary")],
        [
            InlineKeyboardButton(f"⚡ {sc('ᴜᴘᴅᴀᴛᴇꜱ')}", url=config.UPDATE_CHANNEL_URL, style="danger"),
            InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back", style="primary"),
        ],
    ]
    if is_owner:
        rows.insert(0, [InlineKeyboardButton(f"🛡 {LABEL_ADMIN}", callback_data="admin:panel", style="danger")])
    return _kb(rows)

def admin_panel() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"📊 {LABEL_STATS}", callback_data="admin:stats", style="primary")],
        [
            InlineKeyboardButton(f"🔑 {sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}", callback_data="admin:addapi", style="success"),  # <-- NAYA BUTTON
            InlineKeyboardButton(f"🗑 {LABEL_REVOKE}", callback_data="admin:revoke_session", style="danger"),
        ],
        [
            InlineKeyboardButton(f"✅ {LABEL_GRANT}", callback_data="admin:grant", style="success"),
            InlineKeyboardButton(f"❌ {LABEL_REVOKE_P}", callback_data="admin:revoke_premium", style="danger"),
        ],
        [InlineKeyboardButton(f"📢 {LABEL_BCAST}", callback_data="admin:broadcast", style="primary")],
        [InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back", style="danger")],
    ])

def plan_selector() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"⚡ {sc('ᴛʀɪᴀʟ')} (1 day)", callback_data="plan:trial", style="primary"),
            InlineKeyboardButton(f"📅 {sc('ᴡᴇᴇᴋʟʏ')} (7 days)", callback_data="plan:weekly", style="primary"),
        ],
        [
            InlineKeyboardButton(f"🗓 {sc('ᴍᴏɴᴛʜʟʏ')} (30 days)", callback_data="plan:monthly", style="primary"),
            InlineKeyboardButton(f"♾ {sc('ʏᴇᴀʀʟʏ')} (365 days)", callback_data="plan:yearly", style="primary"),
        ],
        [InlineKeyboardButton(f"↩ {LABEL_CANCEL}", callback_data="admin:panel", style="danger")],
    ])

def confirm_action(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"✅ {LABEL_YES}", callback_data=yes_data, style="success"),
            InlineKeyboardButton(f"❌ {LABEL_NO}", callback_data=no_data, style="danger"),
        ],
    ])

def session_menu(has_session: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"🔑 {sc('ꜱᴇᴛᴜᴘ ꜱᴇꜱꜱɪᴏɴ')}", callback_data="session:setup", style="success")]]
    if has_session:
        rows.append([InlineKeyboardButton(f"🗑 {LABEL_REVOKE}", callback_data="session:revoke", style="danger")])
    rows.append([InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back", style="danger")])
    return _kb(rows)

def api_choice_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"🔧 {sc('ᴜꜱᴇ ᴍʏ ᴏᴡɴ ᴀᴘɪ')}", callback_data="api:custom", style="primary")],
        [InlineKeyboardButton(f"⚡ {sc('ᴜꜱᴇ ᴅᴇꜰᴀᴜʟᴛ ᴀᴘɪ')}", callback_data="api:default", style="success")],
        [InlineKeyboardButton(f"↩ {LABEL_CANCEL}", callback_data="menu:back", style="danger")],
    ])

def cancel_operation() -> InlineKeyboardMarkup:
    return _kb([[InlineKeyboardButton(f"⛔ {sc('ꜱᴛᴏᴘ ᴏᴘᴇʀᴀᴛɪᴏɴ')}", callback_data="op:cancel", style="danger")]])

def status_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"🔄 {sc('ʀᴇꜰʀᴇꜱʜ')}", callback_data="status:refresh", style="primary"),
            InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back", style="danger"),
        ],
    ])

def otp_resend_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"📲 {sc('ʀᴇꜱᴇɴᴅ ᴄᴏᴅᴇ')}", callback_data="otp:resend", style="primary"),
            InlineKeyboardButton(f"↩ {LABEL_CANCEL}", callback_data="otp:cancel", style="danger"),
        ],
    ])
def back_btn() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"↩ {LABEL_BACK}", callback_data="menu:back", style="danger")]
    ])
