import io, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from utils.text import sc

BG          = (5, 0, 10)
GRID_COLOR  = (42, 0, 0)
RED_NEON    = (255, 0, 51)
RED_DARK    = (139, 0, 0)
RED_DIM     = (80, 0, 0)

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

def generate_banner(avatar_bytes: bytes | None, title: str = "SYSTEM OVERRIDE") -> io.BytesIO:
    W, H = 1024, 500

    # CRITICAL FIX: Pillow v10+ removed Image.LANCZOS at top level
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Dark red grid
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=GRID_COLOR, width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=GRID_COLOR, width=1)

    # Central radial glow via RGBA overlay
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W // 2 - 260, H // 2 - 260, W // 2 + 260, H // 2 + 260],
               fill=(*RED_NEON, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Tech corner brackets
    sz = 55
    lw = 3
    corners = [(50, 50), (W - 50, 50), (50, H - 50), (W - 50, H - 50)]
    dirs     = [(1, 1),  (-1, 1),       (1, -1),       (-1, -1)]
    for (cx, cy), (dx, dy) in zip(corners, dirs):
        draw.line([(cx, cy), (cx + dx * sz, cy)],          fill=RED_NEON, width=lw)
        draw.line([(cx, cy), (cx, cy + dy * sz)],          fill=RED_NEON, width=lw)
        draw.line([(cx + dx * 10, cy + dy * 10),
                   (cx + dx * (sz - 10), cy + dy * 10)],   fill=RED_DIM,  width=1)

    # Horizontal scan lines (subtle)
    for y in range(0, H, 8):
        draw.line([(0, y), (W, y)], fill=(15, 0, 0), width=1)

    # Title text top-left
    title_str = sc(title.upper())
    draw.text((72, 55), title_str, font=_font(30), fill=RED_NEON)

    # Sub-label bottom-right
    draw.text((W - 380, H - 75), "R O O T   A C C E S S", font=_font(20), fill=RED_DARK)

    # Version tick bottom-left
    draw.text((72, H - 55), "N O X   S Y N D I C A T E  //  v2.0", font=_font(16), fill=RED_DIM)

    # Avatar in center circle
    asize = 220
    ax = (W - asize) // 2
    ay = (H - asize) // 2

    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            av = av.resize((asize, asize), resample)           # uses fixed resample
            mask = Image.new("L", (asize, asize), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, asize, asize], fill=255)
            img.paste(av, (ax, ay), mask)
        except Exception:
            pass  # silently skip if DP broken

    # Circle border around avatar slot
    draw.ellipse(
        [ax - 12, ay - 12, ax + asize + 12, ay + asize + 12],
        outline=RED_NEON, width=4
    )
    # Inner dim ring
    draw.ellipse(
        [ax - 22, ay - 22, ax + asize + 22, ay + asize + 22],
        outline=RED_DIM, width=1
    )

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def generate_scary_dp() -> io.BytesIO:
    W, H = 1024, 1024
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Red glitch static lines
    for _ in range(220):
        x = random.randint(0, W)
        y = random.randint(0, H)
        w = random.randint(10, 240)
        h = random.randint(1, 5)
        color = random.choice([
            (255, 0, 0), (180, 0, 0), (100, 0, 0),
            (60, 0, 0),  (255, 20, 20)
        ])
        draw.rectangle([x, y, x + w, y + h], fill=color)

    # Central demonic glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W // 2 - 320, H // 2 - 210, W // 2 + 320, H // 2 + 210],
               fill=(255, 0, 0, 140))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Menacing eye outer shape
    draw.ellipse(
        [W // 2 - 260, H // 2 - 155, W // 2 + 260, H // 2 + 155],
        fill=(8, 0, 0), outline=(255, 0, 0), width=9
    )

    # Glowing iris ring
    draw.ellipse(
        [W // 2 - 180, H // 2 - 100, W // 2 + 180, H // 2 + 100],
        outline=(200, 0, 0), width=4
    )

    # Slit/diamond pupil
    draw.polygon([
        (W // 2,       H // 2 - 125),
        (W // 2 + 38,  H // 2),
        (W // 2,       H // 2 + 125),
        (W // 2 - 38,  H // 2),
    ], fill=(255, 0, 0))

    # Inner pupil highlight
    draw.polygon([
        (W // 2,       H // 2 - 60),
        (W // 2 + 14,  H // 2),
        (W // 2,       H // 2 + 60),
        (W // 2 - 14,  H // 2),
    ], fill=(255, 80, 80))

    # Blood drips from bottom of eye
    for _ in range(22):
        x = random.randint(W // 2 - 220, W // 2 + 220)
        length = random.randint(60, 280)
        width  = random.randint(2, 7)
        draw.line([(x, H // 2 + 145), (x, H // 2 + 145 + length)],
                  fill=(140, 0, 0), width=width)
        # drip tip
        draw.ellipse([x - width, H // 2 + 145 + length - width,
                      x + width, H // 2 + 145 + length + width * 2],
                     fill=(100, 0, 0))

    # Dark vignette edges
    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-180, -180, W + 180, H + 180], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(160))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(img, black, vignette)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=97)
    buf.seek(0)
    return buf
