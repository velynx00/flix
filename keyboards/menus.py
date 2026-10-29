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
            InlineKeyboardButton(f"❓ {sc('ʜᴇʟᴘ')}", callback_data="menu:help", style="danger"),
        ],
        [
            InlineKeyboardButton(f"📢 {sc('ᴜᴘᴅᴀᴛᴇꜱ')}", url=config.UPDATE_CHANNEL_URL, style="primary"),
        ],
    ])

def help_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"🔑 {sc('ɢᴇᴛ ᴀᴘɪ ɢᴜɪᴅᴇ')}", callback_data="help:api", style="primary")],
        [InlineKeyboardButton(f"📥 {sc('ꜱᴄʀᴀᴘᴇ ɢᴜɪᴅᴇ')}", callback_data="help:scrape", style="success")],
        [InlineKeyboardButton(f"📤 {sc('ᴀᴅᴅ ɢᴜɪᴅᴇ')}", callback_data="help:add", style="success")],
        [InlineKeyboardButton(f"↩ {sc('ʙᴀᴄᴋ')}", callback_data="menu:back", style="danger")],
    ])

def scrape_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"⟢ {sc('ꜱᴛᴀʀᴛ ꜱᴄʀᴀᴘᴇ')}", callback_data="scrape:start", style="success")],
        [InlineKeyboardButton(f"↩ {sc('ʙᴀᴄᴋ')}", callback_data="menu:back", style="danger")],
    ])

def add_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"✦ {sc('ꜱᴛᴀʀᴛ ᴀᴅᴅɪɴɢ')}", callback_data="add:start", style="success")],
        [InlineKeyboardButton(f"↩ {sc('ʙᴀᴄᴋ')}", callback_data="menu:back", style="danger")],
    ])

def premium_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"💬 {sc('ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ')} (@Velynx007)", url="https://t.me/Velynx007", style="primary")],
        [InlineKeyboardButton(f"↩ {sc('ʙᴀᴄᴋ')}", callback_data="menu:back", style="danger")],
    ]
    return _kb(rows)

def admin_panel() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"📊 {sc('ꜱᴛᴀᴛꜱ')}", callback_data="admin:stats", style="primary")],
        [
            InlineKeyboardButton(f"🔑 {sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}", callback_data="admin:addapi", style="success"),
            InlineKeyboardButton(f"🗑 {sc('ʀᴇᴠᴏᴋᴇ')}", callback_data="admin:revoke", style="danger"),
        ],
        [InlineKeyboardButton(f"↩ {sc('ʙᴀᴄᴋ')}", callback_data="menu:back", style="danger")],
    ])

def back_btn() -> InlineKeyboardMarkup:
    return _kb([[InlineKeyboardButton(f"↩ {sc('ʙᴀᴄᴋ')}", callback_data="menu:back", style="danger")]])
