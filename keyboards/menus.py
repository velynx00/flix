from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.text import sc

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🔍 {sc('ꜱᴄʀᴀᴘᴇ ᴍᴇᴍʙᴇʀꜱ')}",   callback_data="action:scrape"),
            InlineKeyboardButton(f"⚡ {sc('ᴀᴅᴅ ᴍᴇᴍʙᴇʀꜱ')}",         callback_data="action:add"),
        ],
        [
            InlineKeyboardButton(f"📂 {sc('ᴜᴘʟᴏᴀᴅ ᴄꜱᴠ')}",          callback_data="action:upload"),
            InlineKeyboardButton(f"🔑 {sc('ᴍʏ ꜱᴇꜱꜱɪᴏɴꜱ')}",         callback_data="action:sessions"),
        ],
        [
            InlineKeyboardButton(f"💎 {sc('ᴘʀᴇᴍɪᴜᴍ')}",              callback_data="menu:premium"),
            InlineKeyboardButton(f"📊 {sc('ᴍʏ ᴘʟᴀɴ')}",              callback_data="menu:plan"),
        ],
        [
            InlineKeyboardButton(f"⚙️ {sc('ꜱᴇᴛᴛɪɴɢꜱ')}",             callback_data="menu:settings"),
            InlineKeyboardButton(f"ℹ️ {sc('ʜᴇʟᴘ')}",                  callback_data="menu:help"),
        ],
    ])

def premium_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if not is_owner:
        rows.append([
            InlineKeyboardButton(f"🛒 {sc('ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ')}",          url="https://t.me/Velynx007"),
        ])
    rows.append([
        InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",                     callback_data="menu:back"),
    ])
    return InlineKeyboardMarkup(rows)

def back_btn(label: str = "◀  ʙᴀᴄᴋ") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data="menu:back")
    ]])

def confirm_menu(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ {sc('ᴄᴏɴꜰɪʀᴍ')}",  callback_data=f"confirm:{action}"),
        InlineKeyboardButton(f"❌ {sc('ᴄᴀɴᴄᴇʟ')}",  callback_data="menu:back"),
    ]])

def session_menu(sessions: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"📱 +{sess}", callback_data=f"session:select:{sess}")]
        for sess in sessions
    ]
    rows.append([
        InlineKeyboardButton(f"➕ {sc('ᴀᴅᴅ ꜱᴇꜱꜱɪᴏɴ')}",     callback_data="setup:api"),
        InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",               callback_data="menu:back"),
    ])
    return InlineKeyboardMarkup(rows)

def scrape_options_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👥 {sc('ᴀʟʟ ᴍᴇᴍʙᴇʀꜱ')}",      callback_data="scrape:all"),
            InlineKeyboardButton(f"🟢 {sc('ᴀᴄᴛɪᴠᴇ ᴏɴʟʏ')}",       callback_data="scrape:active"),
        ],
        [InlineKeyboardButton(f"◀  {sc('ʙᴀᴄᴋ')}",                  callback_data="menu:back")],
    ])
