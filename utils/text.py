SC_MAP = {
    'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ',
    'i':'ɪ','j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ',
    'q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x',
    'y':'ʏ','z':'ᴢ'
}

def sc(text: str) -> str:
    if not text: return ""
    return "".join(SC_MAP.get(c.lower(), c) for c in str(text))

def esc(s) -> str:
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

escape_html = esc

# ── PROGRESS BAR ──
def progress_bar(current: int, total: int, length: int = 10) -> str:
    if total == 0: return "░" * length
    filled = int(length * current / total)
    bar = "█" * filled + "░" * (length - filled)
    pct = int(100 * current / total)
    return f"[{bar}] {pct}%"

# ── ANIMATED BOOT FRAMES ──
BOOT_FRAMES = [
    "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛",
    "🟥⬛⬛⬛⬛⬛⬛⬛⬛⬛",
    "🟥🟥⬛⬛⬛⬛⬛⬛⬛⬛",
    "🟥🟥🟥⬛⬛⬛⬛⬛⬛⬛",
    "🟥🟥🟥🟥⬛⬛⬛⬛⬛⬛",
    "🟥🟥🟥🟥🟥⬛⬛⬛⬛⬛",
    "🟥🟥🟥🟥🟥🟥⬛⬛⬛⬛",
    "🟥🟥🟥🟥🟥🟥🟥⬛⬛⬛",
    "🟥🟥🟥🟥🟥🟥🟥🟥⬛⬛",
    "🟥🟥🟥🟥🟥🟥🟥🟥🟥⬛",
    "🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥",
]

SPINNER = ["◐", "◓", "◑", "◒"]
PULSE   = ["▪", "▫", "▪", "▫"]
