from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
from utils.text import sc

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
        [InlineKeyboardButton(f"↩ ʙᴀᴄᴋ", callback_data="menu:back", style="danger")],
    ])

def add_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"✦ {sc('ꜱᴛᴀʀᴛ ᴀᴅᴅɪɴɢ')}", callback_data="add:start", style="success")],
        [InlineKeyboardButton(f"↩ ʙᴀᴄᴋ", callback_data="menu:back", style="danger")],
    ])

def premium_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"★ {sc('ᴜᴘɢʀᴀᴅᴇ')}", callback_data="premium:upgrade", style="success")],
        [InlineKeyboardButton(f"↩ ʙᴀᴄᴋ", callback_data="menu:back", style="danger")],
    ]
    if is_owner:
        rows.insert(0, [InlineKeyboardButton(f"🛡 ᴀᴅᴍɪɴ", callback_data="admin:panel", style="danger")])
    return _kb(rows)

def admin_panel() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"📊 ꜱᴛᴀᴛꜱ", callback_data="admin:stats", style="primary")],
        [
            InlineKeyboardButton(f"🔑 ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ", callback_data="admin:addapi", style="success"),
            InlineKeyboardButton(f"🗑 ʀᴇᴠᴏᴋᴇ ꜱᴇꜱꜱɪᴏɴ", callback_data="admin:revoke", style="danger"),
        ],
        [InlineKeyboardButton(f"↩ ʙᴀᴄᴋ", callback_data="menu:back", style="danger")],
    ])

def back_btn() -> InlineKeyboardMarkup:
    return _kb([[InlineKeyboardButton(f"↩ ʙᴀᴄᴋ", callback_data="menu:back", style="danger")]])
