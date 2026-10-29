import io, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from utils.text import sc

# ── PALETTE (flix2-style: pure reds, no purple tint) ──
BG         = (5, 0, 0)
GRID_COLOR = (22, 0, 0)
RED_DARK   = (90, 0, 0)
RED_DIM    = (55, 0, 0)

# ── SECTION THEMES — flix2 colours, flix1 accent layer kept ──
SECTION_THEMES = {
    "SYSTEM OVERRIDE": {"neon": (150, 0, 0),   "grid": (28, 0, 0),   "sub": (88, 0, 0),   "accent": (220, 30, 30)},
    "PREMIUM ACCESS":  {"neon": (180, 80, 0),  "grid": (38, 16, 0),  "sub": (115, 48, 0), "accent": (255, 160, 20)},
    "HELP CENTER":     {"neon": (0, 100, 150),  "grid": (0, 20, 30),  "sub": (0, 58, 88),  "accent": (40, 180, 240)},
    "API GENERATION":  {"neon": (0, 150, 70),   "grid": (0, 30, 12),  "sub": (0, 88, 40),  "accent": (60, 230, 120)},
    "SCRAPER ENGINE":  {"neon": (180, 40, 0),   "grid": (38, 10, 0),  "sub": (108, 22, 0), "accent": (245, 90, 30)},
    "ADDER ENGINE":    {"neon": (120, 0, 180),  "grid": (24, 0, 38),  "sub": (68, 0, 108), "accent": (190, 70, 245)},
}
DEFAULT_THEME = {"neon": (150, 0, 0), "grid": (28, 0, 0), "sub": (88, 0, 0), "accent": (220, 30, 30)}

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/system/fonts/Roboto-Bold.ttf",
]
FONT_LIGHT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

def _font(size: int, light=False) -> ImageFont.ImageFont:
    candidates = FONT_LIGHT_CANDIDATES if light else FONT_CANDIDATES
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _resample():
    try:    return Image.Resampling.LANCZOS
    except: return Image.LANCZOS

def _add_noise(img, W, H, intensity=6):
    rng = random.Random(42)
    px  = img.load()
    for _ in range(W * H // 50):
        x, y = rng.randint(0, W-1), rng.randint(0, H-1)
        r, g, b = px[x, y]
        d = rng.randint(-intensity, intensity)
        px[x, y] = (max(0, min(255, r+d)), g, b)
    return img

def _draw_hexgrid(draw, W, H, col, size=40):
    h3 = size * math.sqrt(3)
    for row in range(-1, int(H / h3) + 3):
        for cn in range(-1, int(W / (size * 1.5)) + 3):
            cx = cn * size * 1.5
            cy = row * h3 + (cn % 2) * h3 / 2
            pts = [
                (cx + size * math.cos(math.radians(60*i - 30)),
                 cy + size * math.sin(math.radians(60*i - 30)))
                for i in range(6)
            ]
            draw.polygon(pts, outline=col, fill=None)

def _draw_base_theme(W, H, theme):
    NEON = theme["neon"]
    GRID = theme["grid"]
    SUB  = theme["sub"]
    ACC  = theme["accent"]

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Hex grid
    _draw_hexgrid(draw, W, H, GRID_COLOR)

    # Fine scan lines
    for y in range(0, H, 4):
        draw.line([(0, y), (W, y)], fill=(10, 0, 0), width=1)

    # Central glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([W//2-270, H//2-270, W//2+270, H//2+270], fill=(*NEON, 50))
    gd.ellipse([W//2-130, H//2-130, W//2+130, H//2+130], fill=(*ACC,  28))
    glow = glow.filter(ImageFilter.GaussianBlur(95))
    img  = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Top / bottom accent bars
    draw.rectangle([0, 0,   W, 5],   fill=NEON)
    draw.rectangle([0, 0,   W, 1],   fill=ACC)
    draw.rectangle([0, H-5, W, H],   fill=SUB)

    # Corner L-brackets
    sz, lw = 62, 3
    corners = [(50, 50), (W-50, 50), (50, H-50), (W-50, H-50)]
    dirs    = [(1,1),    (-1,1),     (1,-1),     (-1,-1)]
    for (cx, cy), (dx, dy) in zip(corners, dirs):
        draw.line([(cx, cy), (cx+dx*sz, cy)],           fill=NEON, width=lw)
        draw.line([(cx, cy), (cx, cy+dy*sz)],           fill=NEON, width=lw)
        draw.line([(cx+dx*12, cy+dy*12), (cx+dx*(sz-12), cy+dy*12)], fill=SUB, width=1)
        draw.line([(cx+dx*12, cy+dy*12), (cx+dx*12, cy+dy*(sz-12))], fill=SUB, width=1)
        draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=ACC)

    # Side accent lines
    draw.line([(7, 0), (7, H)],     fill=(*NEON, 55), width=1)
    draw.line([(W-7, 0), (W-7, H)], fill=(*NEON, 55), width=1)

    img  = _add_noise(img, W, H, 5)
    draw = ImageDraw.Draw(img)
    return img, draw, NEON, SUB, ACC


def generate_banner(avatar_bytes: bytes | None, title: str = "SYSTEM OVERRIDE") -> io.BytesIO:
    W, H = 1024, 512
    theme = SECTION_THEMES.get(title.upper(), DEFAULT_THEME)
    img, draw, NEON, SUB, ACC = _draw_base_theme(W, H, theme)

    draw.text((80, 60), sc(title.upper()),          font=_font(28), fill=NEON)
    draw.text((80, 94), "■ ■ ■",                    font=_font(12), fill=SUB)
    draw.text((80, H-46), "N O X   S Y N D I C A T E  //  v2.0", font=_font(15), fill=(*RED_DIM, 200))
    draw.text((W-330, H-46), "R O O T   A C C E S S",             font=_font(15), fill=SUB)

    # Avatar
    asize = 235
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
    # 3-ring avatar frame
    draw.ellipse([ax-13,  ay-13,  ax+asize+13,  ay+asize+13],  outline=NEON, width=4)
    draw.ellipse([ax-24,  ay-24,  ax+asize+24,  ay+asize+24],  outline=SUB,  width=1)
    draw.ellipse([ax-36,  ay-36,  ax+asize+36,  ay+asize+36],  outline=(*ACC, 55), width=1)

    # Orbit dots around avatar
    for angle_deg in range(0, 360, 45):
        angle = math.radians(angle_deg)
        r  = asize // 2 + 50
        px = W // 2 + int(r * math.cos(angle))
        py = H // 2 + int(r * math.sin(angle))
        dot_col = ACC if angle_deg % 90 == 0 else SUB
        draw.ellipse([px-3, py-3, px+3, py+3], fill=dot_col)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def generate_static_banner(title: str = "SCRAPER ENGINE") -> io.BytesIO:
    W, H = 1024, 512
    theme = SECTION_THEMES.get(title.upper(), DEFAULT_THEME)
    img, draw, NEON, SUB, ACC = _draw_base_theme(W, H, theme)

    title_text = sc(title.upper())
    # Shadow + main title
    draw.text((W//2+3, H//2-38), title_text, font=_font(70), fill=(*SUB, 180), anchor="mm")
    draw.text((W//2,   H//2-35), title_text, font=_font(70), fill=NEON,        anchor="mm")

    draw.text((W//2, H//2+50), sc("NOX SYNDICATE // v2.0"), font=_font(26), fill=SUB, anchor="mm")

    # Divider
    draw.line([(W//2-170, H//2+10), (W//2+170, H//2+10)], fill=ACC, width=1)

    draw.text((80, 60),     sc("SECURE PROTOCOL"),                    font=_font(18), fill=SUB)
    draw.text((80, H-46),   "N O X   S Y N D I C A T E  //  v2.0",  font=_font(15), fill=(*RED_DIM, 200))
    draw.text((W-330, H-46), "R O O T   A C C E S S",                font=_font(15), fill=SUB)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def generate_scary_dp() -> io.BytesIO:
    W, H   = 1024, 1024
    cx, cy = W // 2, H // 2
    rng    = random.Random()

    img  = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    hex_r = 38
    for row in range(-1, int(H / (hex_r * math.sqrt(3))) + 3):
        for col in range(-1, int(W / (hex_r * 1.5)) + 3):
            hx = col * hex_r * 1.5
            hy = row * hex_r * math.sqrt(3) + (col % 2) * hex_r * math.sqrt(3) / 2
            pts = [(hx + hex_r * math.cos(math.radians(60*i - 30)),
                    hy + hex_r * math.sin(math.radians(60*i - 30))) for i in range(6)]
            draw.polygon(pts, outline=(15, 0, 0), fill=None)

    for _ in range(350):
        sx, sy = rng.randint(0, W), rng.randint(0, H)
        draw.rectangle([sx, sy, sx+rng.randint(1, 8), sy+rng.randint(1, 4)],
                       fill=(rng.randint(40, 120), 0, 0))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([cx-350, cy-280, cx+350, cy+280], fill=(120, 0, 0, 110))
    gd.ellipse([cx-160, cy-130, cx+160, cy+130], fill=(180, 0, 0, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    img  = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    def crack_branch(d, ox, oy, angle, depth):
        if depth == 0: return
        length = rng.randint(30, 90) * (depth / 5)
        ex = ox + length * math.cos(math.radians(angle))
        ey = oy + length * math.sin(math.radians(angle))
        d.line([(ox, oy), (ex, ey)], fill=(max(20, int(60*depth/5))*2, 0, 0), width=max(1, depth-1))
        if rng.random() < 0.4: crack_branch(d, ex, ey, angle + rng.randint(20, 60), depth-1)
        if rng.random() < 0.4: crack_branch(d, ex, ey, angle - rng.randint(20, 60), depth-1)
        crack_branch(d, ex, ey, angle + rng.randint(-15, 15), depth-1)

    for _ in range(28): crack_branch(draw, cx, cy, rng.randint(0, 360), 5)

    ew, eh = 480, 230
    draw.ellipse([cx-ew//2, cy-eh//2, cx+ew//2, cy+eh//2],
                 fill=(0,0,0), outline=(150,0,0), width=10)
    for rw, rh, col, lw in [(360,160,(180,0,0),5),(280,120,(200,0,0),3),(200,85,(150,0,0),2),(130,55,(220,0,0),4)]:
        draw.ellipse([cx-rw//2, cy-rh//2, cx+rw//2, cy+rh//2], outline=col, width=lw)

    ph, pw = 180, 52
    draw.polygon([(cx,cy-ph//2),(cx+pw,cy),(cx,cy+ph//2),(cx-pw,cy)], fill=(200,0,0))
    draw.polygon([(cx,cy-(ph-40)//2),(cx+pw//2,cy),(cx,cy+(ph-40)//2),(cx-pw//2,cy)], fill=(255,50,50))
    draw.ellipse([cx-22, cy-22, cx+22, cy+22], fill=(200,100,100))

    dy_start = cy + eh // 2
    for _ in range(28):
        x = rng.randint(cx - ew//2 + 30, cx + ew//2 - 30)
        length, width = rng.randint(40, 320), rng.randint(2, 8)
        draw.line([(x, dy_start), (x, dy_start + length)], fill=(120,0,0), width=width)
        draw.ellipse([x-width-2, dy_start+length-width-2,
                      x+width+2, dy_start+length+width*2], fill=(80,0,0))

    scan = Image.new("RGBA", (W, H), (0,0,0,0))
    scd  = ImageDraw.Draw(scan)
    for y in range(0, H, rng.randint(3,6)):
        scd.line([(0,y),(W,y)], fill=(0,0,0,55), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

    bloom = Image.new("RGBA", (W, H), (0,0,0,0))
    bd    = ImageDraw.Draw(bloom)
    bd.ellipse([cx-300, cy-200, cx+300, cy+200], fill=(150,0,0,45))
    img   = Image.alpha_composite(img.convert("RGBA"), bloom.filter(ImageFilter.GaussianBlur(80))).convert("RGB")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=97)
    buf.seek(0)
    return buf
