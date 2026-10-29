SC_MAP = {'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ','j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ'}

def sc(text: str) -> str:
    if not text: return ""
    return "".join(SC_MAP.get(c.lower(), c) for c in str(text))

def esc(s) -> str:
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

# Dono naam kaam karenge taaki koi error na aaye
escape_html = esc
