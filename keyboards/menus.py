from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
from utils.text import sc

def _kb(rows):
    return InlineKeyboardMarkup(rows)

def main_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"🔍 {sc('ꜱᴄʀᴀᴘᴇ ᴍᴇᴍʙᴇʀꜱ')}",  callback_data="menu:scrape"),
            InlineKeyboardButton(f"⚡ {sc('ᴀᴅᴅ ᴍᴇᴍʙᴇʀꜱ')}",        callback_data="menu:add"),
        ],
        [
            InlineKeyboardButton(f"💎 {sc('ᴘʀᴇᴍɪᴜᴍ')}",             callback_data="menu:premium"),
            InlineKeyboardButton(f"❓ {sc('ʜᴇʟᴘ')}",                 callback_data="menu:help"),
        ],
        [
            InlineKeyboardButton(f"🔑 {sc('ꜱᴇᴛᴜᴘ ᴀᴘɪ')}",           callback_data="setup:api"),
            InlineKeyboardButton(f"📢 {sc('ᴜᴘᴅᴀᴛᴇꜱ')}",             url=config.UPDATE_CHANNEL_URL),
        ],
    ])

def help_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"🔑 {sc('ɢᴇᴛ ᴀᴘɪ ɢᴜɪᴅᴇ')}",   callback_data="help:api")],
        [InlineKeyboardButton(f"📥 {sc('ꜱᴄʀᴀᴘᴇ ɢᴜɪᴅᴇ')}",    callback_data="help:scrape")],
        [InlineKeyboardButton(f"📤 {sc('ᴀᴅᴅ ɢᴜɪᴅᴇ')}",        callback_data="help:add")],
        [InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",              callback_data="menu:back")],
    ])

def scrape_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"⟢ {sc('ꜱᴛᴀʀᴛ ꜱᴄʀᴀᴘᴇ')}",    callback_data="scrape:start")],
        [InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",              callback_data="menu:back")],
    ])

def scrape_options_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"👥 {sc('ᴀʟʟ ᴍᴇᴍʙᴇʀꜱ')}",  callback_data="scrape:all"),
            InlineKeyboardButton(f"🟢 {sc('ᴀᴄᴛɪᴠᴇ ᴏɴʟʏ')}",   callback_data="scrape:active"),
        ],
        [InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",              callback_data="menu:back")],
    ])

def add_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"✦ {sc('ꜱᴛᴀʀᴛ ᴀᴅᴅɪɴɢ')}",     callback_data="add:start")],
        [InlineKeyboardButton(f"📁 {sc('ᴜᴘʟᴏᴀᴅ ᴄꜱᴠ')}",       callback_data="add:csv")],
        [InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",              callback_data="menu:back")],
    ])

def premium_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if not is_owner:
        rows.append([InlineKeyboardButton(f"🛒 {sc('ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ')}",  url="https://t.me/Velynx007")])
    rows.append([InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",              callback_data="menu:back")])
    return _kb(rows)

def admin_panel() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"📊 {sc('ꜱᴛᴀᴛꜱ')}",                    callback_data="admin:stats")],
        [
            InlineKeyboardButton(f"🔑 {sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}",           callback_data="admin:addapi"),
            InlineKeyboardButton(f"🗑 {sc('ʀᴇᴠᴏᴋᴇ')}",                 callback_data="admin:revoke"),
        ],
        [InlineKeyboardButton(f"📦 {sc('ʙᴜʟᴋ ꜱᴇꜱꜱɪᴏɴꜱ')}",           callback_data="admin:bulk")],
        [InlineKeyboardButton(f"😈 {sc('ɢᴇɴᴇʀᴀᴛᴇ ᴅᴀʀᴋ ᴅᴘ')}",         callback_data="admin:dp")],
        [InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",                      callback_data="menu:back")],
    ])

def confirm_menu(action: str) -> InlineKeyboardMarkup:
    return _kb([[
        InlineKeyboardButton(f"✅ {sc('ᴄᴏɴꜰɪʀᴍ')}",  callback_data=f"confirm:{action}"),
        InlineKeyboardButton(f"❌ {sc('ᴄᴀɴᴄᴇʟ')}",   callback_data="menu:back"),
    ]])

def session_menu(sessions: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"📱 +{s}", callback_data=f"session:select:{s}")]
        for s in sessions
    ]
    rows.append([
        InlineKeyboardButton(f"➕ {sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}",  callback_data="setup:api"),
        InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",          callback_data="menu:back"),
    ])
    return _kb(rows)

def back_btn(label: str = "◀  ʙᴀᴄᴋ") -> InlineKeyboardMarkup:
    return _kb([[InlineKeyboardButton(label, callback_data="menu:back")]])
