import io, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from utils.text import sc

BG         = (5, 0, 10)
GRID_COLOR = (42, 0, 0)
RED_NEON   = (255, 0, 51)
RED_DARK   = (139, 0, 0)
RED_DIM    = (80, 0, 0)

SECTION_THEMES = {
    "SYSTEM OVERRIDE": {"neon": (255,   0,  51), "grid": ( 42,  0,   0), "sub": (139,   0,   0)},
    "PREMIUM ACCESS":  {"neon": (255, 180,   0), "grid": ( 50, 35,   0), "sub": (180, 120,   0)},
    "HELP CENTER":     {"neon": (  0, 180, 255), "grid": (  0, 30,  50), "sub": (  0, 100, 180)},
    "API GENERATION":  {"neon": (  0, 255, 120), "grid": (  0, 40,  15), "sub": (  0, 160,  80)},
    "SCRAPER ENGINE":  {"neon": (255,  80,   0), "grid": ( 50, 20,   0), "sub": (180,  50,   0)},
    "ADDER ENGINE":    {"neon": (180,   0, 255), "grid": ( 30,  0,  50), "sub": (120,   0, 180)},
}
DEFAULT_THEME = {"neon": (255, 0, 51), "grid": (42, 0, 0), "sub": (139, 0, 0)}

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

def generate_banner(avatar_bytes: bytes | None, title: str = "SYSTEM OVERRIDE") -> io.BytesIO:
    W, H = 1024, 500
    resample = _resample()

    theme = SECTION_THEMES.get(title.upper(), DEFAULT_THEME)
    NEON  = theme["neon"]
    GRID  = theme["grid"]
    SUB   = theme["sub"]

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 40): draw.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 40): draw.line([(0, y), (W, y)], fill=GRID, width=1)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([W//2-260, H//2-260, W//2+260, H//2+260], fill=(*NEON, 70))
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

    for y in range(0, H, 8):
        draw.line([(0, y), (W, y)], fill=(15, 0, 0), width=1)

    draw.text((72, 55), sc(title.upper()), font=_font(30), fill=NEON)
    draw.text((W-380, H-75), "R O O T   A C C E S S", font=_font(20), fill=SUB)
    draw.text((72, H-55), "N O X   S Y N D I C A T E  //  v2.0", font=_font(16), fill=RED_DIM)

    asize = 220
    ax    = (W - asize) // 2
    ay    = (H - asize) // 2
    if avatar_bytes:
        try:
            av   = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            av   = av.resize((asize, asize), resample)
            mask = Image.new("L", (asize, asize), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, asize, asize], fill=255)
            img.paste(av, (ax, ay), mask)
        except Exception:
            pass

    draw = ImageDraw.Draw(img)
    draw.ellipse([ax-12,  ay-12,  ax+asize+12,  ay+asize+12], outline=NEON, width=4)
    draw.ellipse([ax-22,  ay-22,  ax+asize+22,  ay+asize+22], outline=RED_DIM, width=1)

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
    cols  = int(W / (hex_r * 1.5)) + 3
    rows  = int(H / (hex_r * math.sqrt(3))) + 3
    for row in range(-1, rows):
        for col in range(-1, cols):
            hx = col * hex_r * 1.5
            hy = row * hex_r * math.sqrt(3) + (col % 2) * hex_r * math.sqrt(3) / 2
            pts = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                pts.append((hx + hex_r * math.cos(angle), hy + hex_r * math.sin(angle)))
            draw.polygon(pts, outline=(18, 0, 0), fill=None)

    for _ in range(350):
        sx = rng.randint(0, W)
        sy = rng.randint(0, H)
        sw = rng.randint(1, 8)
        sh = rng.randint(1, 4)
        draw.rectangle([sx, sy, sx+sw, sy+sh], fill=(rng.randint(60, 180), 0, 0))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([cx-350, cy-280, cx+350, cy+280], fill=(200,  0,  0, 110))
    gd.ellipse([cx-160, cy-130, cx+160, cy+130], fill=(255, 20,  0, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    img  = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    def crack_branch(d, ox, oy, angle, depth):
        if depth == 0: return
        length = rng.randint(30, 90) * (depth / 5)
        ex     = ox + length * math.cos(math.radians(angle))
        ey     = oy + length * math.sin(math.radians(angle))
        alpha  = max(20, int(80 * depth / 5))
        d.line([(ox, oy), (ex, ey)], fill=(alpha*2, 0, 0), width=max(1, depth-1))
        if rng.random() < 0.4: crack_branch(d, ex, ey, angle + rng.randint(20, 60), depth-1)
        if rng.random() < 0.4: crack_branch(d, ex, ey, angle - rng.randint(20, 60), depth-1)
        crack_branch(d, ex, ey, angle + rng.randint(-15, 15), depth-1)

    for _ in range(28): crack_branch(draw, cx, cy, rng.randint(0, 360), 5)

    ew, eh = 480, 230
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd     = ImageDraw.Draw(shadow)
    sd.ellipse([cx-ew//2-15, cy-eh//2-15, cx+ew//2+15, cy+eh//2+15], fill=(255, 0, 0, 50))
    shadow = shadow.filter(ImageFilter.GaussianBlur(25))
    img    = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    draw   = ImageDraw.Draw(img)
    draw.ellipse([cx-ew//2, cy-eh//2, cx+ew//2, cy+eh//2], fill=(0, 0, 0), outline=(200, 0, 0), width=10)

    iris_rings = [(360, 160, (220, 0, 0), 5), (280, 120, (255, 30, 0), 3), (200, 85, (180, 0, 0), 2), (130, 55, (255, 0, 0), 4)]
    for rw, rh, col, lw in iris_rings:
        draw.ellipse([cx-rw//2, cy-rh//2, cx+rw//2, cy+rh//2], outline=col, width=lw)

    iris_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    igd       = ImageDraw.Draw(iris_glow)
    igd.ellipse([cx-200, cy-90, cx+200, cy+90], fill=(255, 0, 0, 60))
    iris_glow = iris_glow.filter(ImageFilter.GaussianBlur(18))
    img       = Image.alpha_composite(img.convert("RGBA"), iris_glow).convert("RGB")
    draw      = ImageDraw.Draw(img)

    ph, pw = 180, 52
    draw.polygon([(cx, cy-ph//2), (cx+pw, cy), (cx, cy+ph//2), (cx-pw, cy)], fill=(255, 0, 0))
    draw.polygon([(cx, cy-(ph-40)//2), (cx+pw//2, cy), (cx, cy+(ph-40)//2), (cx-pw//2, cy)], fill=(255, 80, 80))
    draw.ellipse([cx-22, cy-22, cx+22, cy+22], fill=(255, 200, 200))

    spike_count = 22
    for i in range(spike_count):
        t      = i / spike_count
        angle  = t * 2 * math.pi
        ex_pt  = cx + (ew//2) * math.cos(angle)
        ey_pt  = cy + (eh//2) * math.sin(angle)
        norm_x = math.cos(angle)
        norm_y = math.sin(angle)
        length = rng.randint(18, 55)
        draw.line([(ex_pt, ey_pt), (ex_pt+norm_x*length, ey_pt+norm_y*length)], fill=(200, 0, 0), width=rng.randint(1, 3))

    dy_start = cy + eh // 2
    for _ in range(28):
        x = rng.randint(cx - ew//2 + 30, cx + ew//2 - 30)
        length = rng.randint(40, 320)
        width  = rng.randint(2, 8)
        draw.line([(x, dy_start), (x, dy_start + length)], fill=(140, 0, 0), width=width)
        br = width + rng.randint(2, 6)
        draw.ellipse([x-br, dy_start+length-br, x+br, dy_start+length+br*2], fill=(100, 0, 0))

    dy_top = cy - eh // 2
    for _ in range(14):
        x = rng.randint(cx - ew//2 + 40, cx + ew//2 - 40)
        length = rng.randint(20, 100)
        width  = rng.randint(2, 5)
        draw.line([(x, dy_top), (x, dy_top - length)], fill=(100, 0, 0), width=width)
        br = width + rng.randint(1, 4)
        draw.ellipse([x-br, dy_top-length-br*2, x+br, dy_top-length+br], fill=(80, 0, 0))

    def lightning_vein(d, ox, oy, tx, ty, depth):
        segments = [(ox, oy, tx, ty)]
        for _ in range(depth):
            next_segs = []
            for (ax2, ay2, bx, by) in segments:
                dist = math.hypot(bx - ax2, by - ay2)
                if dist < 8:
                    next_segs.append((ax2, ay2, bx, by))
                    continue
                mx   = (ax2 + bx) / 2 + rng.uniform(-0.4, 0.4) * dist
                my   = (ay2 + by) / 2 + rng.uniform(-0.4, 0.4) * dist
                next_segs.append((ax2, ay2, mx, my))
                next_segs.append((mx, my, bx, by))
                if rng.random() < 0.2:
                    next_segs.append((mx, my, mx + rng.uniform(-0.6, 0.6) * dist, my + rng.uniform(-0.6, 0.6) * dist))
            segments = next_segs
        bright = rng.randint(120, 220)
        for (ax2, ay2, bx, by) in segments:
            d.line([(ax2, ay2), (bx, by)], fill=(bright, 0, 0), width=1)

    for _ in range(10): lightning_vein(draw, rng.randint(0, W), rng.randint(0, H), rng.randint(0, W), rng.randint(0, H), depth=5)

    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scd  = ImageDraw.Draw(scan)
    for y in range(0, H, rng.randint(3, 6)): scd.line([(0, y), (W, y)], fill=(0, 0, 0, 55), width=1)
    img  = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

    vig  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vid  = ImageDraw.Draw(vig)
    for i in range(18):
        t   = i / 18
        pad = int(t * 520)
        vid.ellipse([pad, pad, W-pad, H-pad], fill=(0, 0, 0, int((1 - t) * 230)))
    vig  = vig.filter(ImageFilter.GaussianBlur(60))
    img  = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")

    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd    = ImageDraw.Draw(bloom)
    bd.ellipse([cx-300, cy-200, cx+300, cy+200], fill=(255, 0, 0, 45))
    bloom = bloom.filter(ImageFilter.GaussianBlur(80))
    img   = Image.alpha_composite(img.convert("RGBA"), bloom).convert("RGB")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=97)
    buf.seek(0)
    return buf
