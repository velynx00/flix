import io, os
from PIL import Image, ImageDraw, ImageFilter
import aiohttp
from utils.text import sc

BG = "#050000"
GRID_COLOR = "#2A0000"
RED_NEON = "#FF0033"

FONT_CANDIDATES = [
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/system/fonts/Roboto-Bold.ttf",
]
def _font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

async def _fetch_avatar(url: str) -> bytes | None:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=10) as r:
                if r.status == 200: return await r.read()
    except Exception: return None

async def generate_banner(avatar_bytes, title="VELYN NOX PREMIUM"):
    W, H = 1024, 500
    img = Image.new("RGB", (W, H), _hex(BG))
    draw = ImageDraw.Draw(img)
    
    # Cyberpunk Grid
    for x in range(0, W, 40): draw.line([(x, 0), (x, H)], fill=(*_hex(GRID_COLOR), 100), width=1)
    for y in range(0, H, 40): draw.line([(0, y), (W, y)], fill=(*_hex(GRID_COLOR), 100), width=1)
        
    # Center Glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W//2 - 250, H//2 - 250, W//2 + 250, H//2 + 250], fill=(*_hex(RED_NEON), 80))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Tech Corners
    draw.line([(50, 50), (200, 50)], fill=_hex(RED_NEON), width=3)
    draw.line([(50, 50), (50, 200)], fill=_hex(RED_NEON), width=3)
    draw.line([(W-50, 50), (W-200, 50)], fill=_hex(RED_NEON), width=3)
    draw.line([(W-50, 50), (W-50, 200)], fill=_hex(RED_NEON), width=3)
    
    # Dynamic Title
    title_text = sc(title.upper())
    draw.text((70, 60), title_text, font=_font(28), fill=_hex(RED_NEON))
    draw.text((W-400, H-80), "R O O T  A C C E S S", font=_font(20), fill=_hex(RED_NEON))

    # Avatar
    asize = 220
    ax, ay = (W - asize) // 2, (H - asize) // 2
    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((asize, asize), Image.LANCZOS)
            mask = Image.new("L", (asize, asize), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, asize, asize], fill=255)
            img.paste(av, (ax, ay), mask)
        except: pass

    # Rings
    draw.ellipse([ax-10, ay-10, ax+asize+10, ay+asize+10], outline=_hex(RED_NEON), width=4)
    
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
