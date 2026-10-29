from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
from utils.text import sc

def _kb(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(rows)

def main_menu() -> InlineKeyboardMarkup:
    return _kb([
        [
            InlineKeyboardButton(f"⚡ {sc('scrape')}", callback_data="menu:scrape"),
            InlineKeyboardButton(f"🔥 {sc('add')}",   callback_data="menu:add"),
        ],
        [
            InlineKeyboardButton(f"💎 {sc('premium')}", callback_data="menu:premium"),
            InlineKeyboardButton(f"❓ {sc('help')}",   callback_data="menu:help"),
        ],
        [
            InlineKeyboardButton(f"📢 {sc('updates')}", url=config.UPDATE_CHANNEL_URL),
        ],
    ])

def help_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"🔑 {sc('get api guide')}",   callback_data="help:api")],
        [InlineKeyboardButton(f"📥 {sc('scrape guide')}",    callback_data="help:scrape")],
        [InlineKeyboardButton(f"📤 {sc('add guide')}",       callback_data="help:add")],
        [InlineKeyboardButton(f"↩ {sc('back')}",             callback_data="menu:back")],
    ])

def scrape_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"⟢ {sc('start scrape')}", callback_data="scrape:start")],
        [InlineKeyboardButton(f"↩ {sc('back')}",          callback_data="menu:back")],
    ])

def add_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"✦ {sc('start adding')}", callback_data="add:start")],
        [InlineKeyboardButton(f"↩ {sc('back')}",          callback_data="menu:back")],
    ])

def premium_menu() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(
            f"💬 {sc('contact owner')} (@Velynx007)",
            url="https://t.me/Velynx007"
        )],
        [InlineKeyboardButton(f"↩ {sc('back')}", callback_data="menu:back")],
    ])

def admin_panel() -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(f"📊 {sc('stats')}",          callback_data="admin:stats")],
        [
            InlineKeyboardButton(f"🔑 {sc('add session')}",  callback_data="admin:addapi"),
            InlineKeyboardButton(f"🗑 {sc('revoke')}",       callback_data="admin:revoke"),
        ],
        [InlineKeyboardButton(f"😈 {sc('generate dark dp')}", callback_data="admin:dp")],
        [InlineKeyboardButton(f"↩ {sc('back')}",              callback_data="menu:back")],
    ])

def back_btn() -> InlineKeyboardMarkup:
    return _kb([[InlineKeyboardButton(f"↩ {sc('back')}", callback_data="menu:back")]])
