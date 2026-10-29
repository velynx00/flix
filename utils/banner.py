import io, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from utils.text import sc

BG = "#050000"
GRID_COLOR = "#2A0000"
RED_NEON = "#FF0033"

FONT_CANDIDATES = [
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/system/fonts/Roboto-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def _font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p): 
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

def generate_banner(avatar_bytes, title="SYSTEM OVERRIDE"):
    W, H = 1024, 500
    img = Image.new("RGB", (W, H), _hex(BG))
    draw = ImageDraw.Draw(img)
    
    for x in range(0, W, 40): draw.line([(x, 0), (x, H)], fill=(*_hex(GRID_COLOR), 100), width=1)
    for y in range(0, H, 40): draw.line([(0, y), (W, y)], fill=(*_hex(GRID_COLOR), 100), width=1)
        
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W//2 - 250, H//2 - 250, W//2 + 250, H//2 + 250], fill=(*_hex(RED_NEON), 80))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGBA")
    draw = ImageDraw.Draw(img)

    draw.line([(50, 50), (200, 50)], fill=_hex(RED_NEON), width=3)
    draw.line([(50, 50), (50, 200)], fill=_hex(RED_NEON), width=3)
    draw.line([(W-50, 50), (W-200, 50)], fill=_hex(RED_NEON), width=3)
    draw.line([(W-50, 50), (W-50, 200)], fill=_hex(RED_NEON), width=3)
    
    title_text = sc(title.upper())
    draw.text((70, 60), title_text, font=_font(28), fill=_hex(RED_NEON))
    draw.text((W-400, H-80), "R O O T  A C C E S S", font=_font(20), fill=_hex(RED_NEON))

    asize = 220
    ax, ay = (W - asize) // 2, (H - asize) // 2
    
    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            try: resample = Image.Resampling.LANCZOS
            except AttributeError: resample = Image.LANCZOS
            
            av = av.resize((asize, asize), resample)
            mask = Image.new("L", (asize, asize), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, asize, asize], fill=255)
            img.paste(av, (ax, ay), mask)
        except Exception: pass

    draw.ellipse([ax-10, ay-10, ax+asize+10, ay+asize+10], outline=_hex(RED_NEON), width=4)
    
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf

# NAYA FUNCTION: Khatarnak DP banane ke liye
def generate_scary_dp():
    W, H = 1024, 1024
    img = Image.new("RGB", (W, H), (0, 0, 0)) # Pure Black
    draw = ImageDraw.Draw(img)

    # Glitch Static (Red aur Dark Red lines)
    for _ in range(200):
        x, y = random.randint(0, W), random.randint(0, H)
        w, h = random.randint(10, 200), random.randint(1, 4)
        color = random.choice([(255, 0, 0), (100, 0, 0), (50, 0, 0)])
        draw.rectangle([x, y, x+w, y+h], fill=color)

    # Center Demonic Glow
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W//2 - 300, H//2 - 200, W//2 + 300, H//2 + 200], fill=(255, 0, 0, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Khatarnak Eye Shape
    draw.ellipse([W//2 - 250, H//2 - 150, W//2 + 250, H//2 + 150], fill=(10, 0, 0), outline=(255, 0, 0), width=8)

    # Slit Pupil (Snake/Demon jaisa)
    draw.polygon([(W//2, H//2 - 120), (W//2 + 35, H//2), (W//2, H//2 + 120), (W//2 - 35, H//2)], fill=(255, 0, 0))

    # Blood Drips
    for _ in range(20):
        x = random.randint(W//2 - 200, W//2 + 200)
        length = random.randint(50, 250)
        draw.line([(x, H//2 + 140), (x, H//2 + 140 + length)], fill=(150, 0, 0), width=random.randint(2, 6))

    # Dark Vignette (Edges ko kaala karna)
    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-200, -200, W+200, H+200], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(150))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(img, black, vignette)
    
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=100)
    buf.seek(0)
    return buf
