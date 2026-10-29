import io, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from utils.text import sc

# ── PALETTE ──
BG         = (4, 0, 8)
GRID_COLOR = (18, 0, 22)
RED_DARK   = (90, 0, 0)
RED_DIM    = (55, 0, 0)

SECTION_THEMES = {
    "SYSTEM OVERRIDE": {"neon": (200, 0, 40),   "grid": (35, 0, 10),  "sub": (100, 0, 20),  "accent": (255, 60, 80)},
    "PREMIUM ACCESS":  {"neon": (220, 100, 0),  "grid": (45, 20, 0),  "sub": (140, 60, 0),  "accent": (255, 180, 30)},
    "HELP CENTER":     {"neon": (0, 130, 200),  "grid": (0, 25, 40),  "sub": (0, 70, 110),  "accent": (60, 200, 255)},
    "API GENERATION":  {"neon": (0, 180, 80),   "grid": (0, 35, 15),  "sub": (0, 100, 45),  "accent": (80, 255, 140)},
    "SCRAPER ENGINE":  {"neon": (220, 50, 0),   "grid": (45, 12, 0),  "sub": (130, 25, 0),  "accent": (255, 100, 40)},
    "ADDER ENGINE":    {"neon": (140, 0, 220),  "grid": (28, 0, 45),  "sub": (80, 0, 130),  "accent": (200, 80, 255)},
}
DEFAULT_THEME = {"neon": (200, 0, 40), "grid": (35, 0, 10), "sub": (100, 0, 20), "accent": (255, 60, 80)}

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

def _add_noise(img, W, H, intensity=8):
    rng = random.Random(42)
    px = img.load()
    for _ in range(W * H // 40):
        x, y = rng.randint(0, W-1), rng.randint(0, H-1)
        r, g, b = px[x, y]
        d = rng.randint(-intensity, intensity)
        px[x, y] = (max(0, min(255, r+d)), max(0, min(255, g+d//2)), max(0, min(255, b+d//2)))
    return img

def _draw_hexgrid(draw, W, H, col, size=38):
    """Subtle hexagonal grid overlay"""
    h3 = size * math.sqrt(3)
    cols_n = int(W / (size * 1.5)) + 3
    rows_n = int(H / h3) + 3
    for row in range(-1, rows_n):
        for col_n in range(-1, cols_n):
            cx = col_n * size * 1.5
            cy = row * h3 + (col_n % 2) * h3 / 2
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
        draw.line([(0, y), (W, y)], fill=(8, 0, 10), width=1)

    # Central glow blob
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([W//2-300, H//2-300, W//2+300, H//2+300], fill=(*NEON, 45))
    gd.ellipse([W//2-150, H//2-150, W//2+150, H//2+150], fill=(*ACC, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    img  = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Top bar stripe
    draw.rectangle([0, 0, W, 6], fill=NEON)
    draw.rectangle([0, 0, W, 1], fill=ACC)
    # Bottom bar stripe
    draw.rectangle([0, H-6, W, H], fill=SUB)

    # Corner brackets — more elaborate
    sz, lw = 65, 3
    corners = [(50, 50), (W-50, 50), (50, H-50), (W-50, H-50)]
    dirs    = [(1,1),    (-1,1),     (1,-1),     (-1,-1)]
    for (cx, cy), (dx, dy) in zip(corners, dirs):
        # Outer L
        draw.line([(cx, cy), (cx+dx*sz, cy)],       fill=NEON, width=lw)
        draw.line([(cx, cy), (cx, cy+dy*sz)],       fill=NEON, width=lw)
        # Inner accent tick
        draw.line([(cx+dx*12, cy+dy*12), (cx+dx*(sz-12), cy+dy*12)], fill=SUB, width=1)
        draw.line([(cx+dx*12, cy+dy*12), (cx+dx*12, cy+dy*(sz-12))], fill=SUB, width=1)
        # Corner dot
        draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=ACC)

    # Vertical side accent lines
    draw.line([(8, 0), (8, H)], fill=(*NEON, 60), width=1)
    draw.line([(W-8, 0), (W-8, H)], fill=(*NEON, 60), width=1)

    img = _add_noise(img, W, H, 5)
    draw = ImageDraw.Draw(img)
    return img, draw, NEON, SUB, ACC

def generate_banner(avatar_bytes: bytes | None, title: str = "SYSTEM OVERRIDE") -> io.BytesIO:
    W, H = 1024, 512
    theme = SECTION_THEMES.get(title.upper(), DEFAULT_THEME)
    img, draw, NEON, SUB, ACC = _draw_base_theme(W, H, theme)

    # Title top-left
    draw.text((80, 60), sc(title.upper()),   font=_font(28),       fill=NEON)
    draw.text((80, 96), "■ ■ ■",             font=_font(12),       fill=SUB)

    # Bottom watermark
    draw.text((80, H-48), "N O X   S Y N D I C A T E  //  v3.0", font=_font(15), fill=(*RED_DIM, 200))
    draw.text((W-340, H-48), "R O O T   A C C E S S",             font=_font(15), fill=SUB)

    # Avatar
    asize = 240
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
    # Avatar rings — 3 layers
    draw.ellipse([ax-14, ay-14, ax+asize+14, ay+asize+14], outline=NEON, width=4)
    draw.ellipse([ax-26, ay-26, ax+asize+26, ay+asize+26], outline=SUB,  width=1)
    draw.ellipse([ax-38, ay-38, ax+asize+38, ay+asize+38], outline=(*ACC, 60), width=1)

    # Small hex decorations around avatar
    for angle_deg in range(0, 360, 45):
        angle = math.radians(angle_deg)
        r = asize//2 + 50
        px = W//2 + int(r * math.cos(angle))
        py = H//2 + int(r * math.sin(angle))
        draw.ellipse([px-3, py-3, px+3, py+3], fill=ACC if angle_deg % 90 == 0 else SUB)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def generate_static_banner(title: str = "SCRAPER ENGINE") -> io.BytesIO:
    W, H = 1024, 512
    theme = SECTION_THEMES.get(title.upper(), DEFAULT_THEME)
    img, draw, NEON, SUB, ACC = _draw_base_theme(W, H, theme)

    # Large centered title
    title_text = sc(title.upper())
    # Shadow
    draw.text((W//2+3, H//2-38), title_text, font=_font(72), fill=(*SUB, 180), anchor="mm")
    draw.text((W//2,   H//2-35), title_text, font=_font(72), fill=NEON,        anchor="mm")

    # Subtitle
    draw.text((W//2, H//2+50), sc("NOX SYNDICATE // ADVANCED"), font=_font(26), fill=SUB, anchor="mm")

    # Divider line
    lx = W//2 - 180
    draw.line([(lx, H//2+10), (W//2+180, H//2+10)], fill=ACC, width=1)

    # Header / footer labels
    draw.text((80, 60),    sc("SECURE PROTOCOL"),                  font=_font(18), fill=SUB)
    draw.text((80, H-48),  "N O X   S Y N D I C A T E  //  v3.0", font=_font(15), fill=(*RED_DIM, 200))
    draw.text((W-340, H-48), "R O O T   A C C E S S",             font=_font(15), fill=SUB)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def generate_scary_dp() -> io.BytesIO:
    """Unchanged — scary dp generator"""
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
            pts = [(hx + hex_r * math.cos(math.radians(60 * i - 30)),
                    hy + hex_r * math.sin(math.radians(60 * i - 30))) for i in range(6)]
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
    draw.ellipse([cx-22,cy-22,cx+22,cy+22], fill=(200,100,100))

    dy_start = cy + eh // 2
    for _ in range(28):
        x      = rng.randint(cx - ew//2 + 30, cx + ew//2 - 30)
        length = rng.randint(40, 320)
        width  = rng.randint(2, 8)
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
    img   = Image.alpha_composite(
        img.convert("RGBA"),
        bloom.filter(ImageFilter.GaussianBlur(80))
    ).convert("RGB")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=97)
    buf.seek(0)
    return buf
