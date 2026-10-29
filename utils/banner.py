import io, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from utils.text import sc

BG         = (5, 0, 0)
GRID_COLOR = (25, 0, 0)
RED_DARK   = (100, 0, 0)
RED_DIM    = (60, 0, 0)

SECTION_THEMES = {
    "SYSTEM OVERRIDE": {"neon": (150, 0, 0), "grid": (30, 0, 0), "sub": (90, 0, 0)},
    "PREMIUM ACCESS":  {"neon": (180, 80, 0), "grid": (40, 15, 0), "sub": (120, 50, 0)},
    "HELP CENTER":     {"neon": (0, 100, 150), "grid": (0, 20, 30), "sub": (0, 60, 90)},
    "API GENERATION":  {"neon": (0, 150, 70), "grid": (0, 30, 10), "sub": (0, 90, 40)},
    "SCRAPER ENGINE":  {"neon": (180, 40, 0), "grid": (40, 10, 0), "sub": (110, 20, 0)},
    "ADDER ENGINE":    {"neon": (120, 0, 180), "grid": (25, 0, 40), "sub": (70, 0, 110)},
}
DEFAULT_THEME = {"neon": (150, 0, 0), "grid": (30, 0, 0), "sub": (90, 0, 0)}

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/system/fonts/Roboto-Bold.ttf",
]

def _font(size: int) -> ImageFont.ImageFont:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _resample():
    try:
        return Image.Resampling.LANCZOS
    except AttributeError:
        return Image.LANCZOS

def _draw_base_theme(W, H, theme):
    NEON, GRID, SUB = theme["neon"], theme["grid"], theme["sub"]
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    
    for x in range(0, W, 40): draw.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 40): draw.line([(0, y), (W, y)], fill=GRID, width=1)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([W//2-260, H//2-260, W//2+260, H//2+260], fill=(*NEON, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img  = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    sz, lw = 55, 3
    corners = [(50, 50), (W-50, 50), (50, H-50), (W-50, H-50)]
    dirs    = [(1,  1),  (-1,  1),   (1,  -1),   (-1,  -1)]
    for (cx, cy), (dx, dy) in zip(corners, dirs):
        draw.line([(cx, cy), (cx+dx*sz, cy)], fill=NEON, width=lw)
        draw.line([(cx, cy), (cx, cy+dy*sz)], fill=NEON, width=lw)
        draw.line([(cx+dx*10, cy+dy*10), (cx+dx*(sz-10), cy+dy*10)], fill=SUB,  width=1)

    for y in range(0, H, 8): draw.line([(0, y), (W, y)], fill=(10, 0, 0), width=1)
    return img, draw, NEON, SUB

def generate_banner(avatar_bytes: bytes | None, title: str = "SYSTEM OVERRIDE") -> io.BytesIO:
    W, H = 1024, 500
    theme = SECTION_THEMES.get(title.upper(), DEFAULT_THEME)
    img, draw, NEON, SUB = _draw_base_theme(W, H, theme)
    
    draw.text((72, 55), sc(title.upper()), font=_font(30), fill=NEON)
    draw.text((W-380, H-75), "R O O T   A C C E S S", font=_font(20), fill=SUB)
    draw.text((72, H-55), "N O X   S Y N D I C A T E  //  v2.0", font=_font(16), fill=RED_DIM)

    asize = 220
    ax, ay = (W - asize) // 2, (H - asize) // 2
    if avatar_bytes:
        try:
            av   = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            av   = av.resize((asize, asize), _resample())
            mask = Image.new("L", (asize, asize), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, asize, asize], fill=255)
            img.paste(av, (ax, ay), mask)
        except: pass

    draw = ImageDraw.Draw(img)
    draw.ellipse([ax-12,  ay-12,  ax+asize+12,  ay+asize+12], outline=NEON, width=4)
    draw.ellipse([ax-22,  ay-22,  ax+asize+22,  ay+asize+22], outline=RED_DIM, width=1)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf

# NAYA STATIC BANNER (Bina DP ke, bada text)
def generate_static_banner(title: str = "SCRAPER ENGINE") -> io.BytesIO:
    W, H = 1024, 500
    theme = SECTION_THEMES.get(title.upper(), DEFAULT_THEME)
    img, draw, NEON, SUB = _draw_base_theme(W, H, theme)
    
    # Bada center text
    title_text = sc(title.upper())
    draw.text((W//2, H//2 - 30), title_text, font=_font(80), fill=NEON, anchor="mm")
    draw.text((W//2, H//2 + 40), sc("NOX SYNDICATE"), font=_font(30), fill=SUB, anchor="mm")
    
    draw.text((72, 55), sc("SECURE PROTOCOL"), font=_font(20), fill=SUB)
    draw.text((W-350, H-75), "R O O T   A C C E S S", font=_font(20), fill=SUB)
    draw.text((72, H-55), "N O X   S Y N D I C A T E  //  v2.0", font=_font(16), fill=RED_DIM)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
