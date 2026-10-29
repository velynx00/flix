# ============================================================
# utils/banner.py — Pillow Banner Generator for Velyn Nox Premium
#
# Produces a 1024×500 "hacker aesthetic" PNG:
#   • Near-black background (#050000)
#   • Dark-red perspective grid
#   • Circular user DP with red neon ring + corner brackets
#   • "S Y S T E M  C O M P R O M I S E D" headline
#   • "R O O T  A C C E S S" sub-line
#   • Scanline overlay for CRT feel
#
# The file is saved to config.BANNER_OUTPUT_PATH and the
# path is returned so the caller can send it via bot.
# ============================================================

from __future__ import annotations

import io
import logging
import math
import os
import random
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

logger = logging.getLogger(__name__)

# ── Asset directory guard ─────────────────────────────────────

def _ensure_assets_dir() -> None:
    """Create the assets/ directory if it does not exist."""
    os.makedirs(os.path.dirname(config.BANNER_OUTPUT_PATH), exist_ok=True)


# ── Font helpers ──────────────────────────────────────────────

def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """
    Try to load a system TTF font at the requested size.
    Falls back to Pillow's built-in bitmap font if no TTF is available.

    Parameters
    ----------
    size : int  — Point size.
    bold : bool — Whether to prefer a bold variant.

    Returns
    -------
    ImageFont.ImageFont
    """
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "C:/Windows/Fonts/courbd.ttf",   # Windows fallback
        "C:/Windows/Fonts/cour.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    # Ultimate fallback — Pillow default bitmap font (no sizing)
    return ImageFont.load_default()


# ── Drawing sub-routines ──────────────────────────────────────

def _draw_background(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """
    Fill the canvas with the configured background colour and add a
    very subtle radial vignette (darker corners).

    Parameters
    ----------
    draw : ImageDraw.ImageDraw
    w    : int — Canvas width.
    h    : int — Canvas height.
    """
    draw.rectangle([0, 0, w, h], fill=config.BANNER_BG_COLOR)


def _draw_grid(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """
    Render a perspective-style red grid onto the lower half of the image.
    Horizontal lines converge to a vanishing point; vertical lines are
    evenly spaced and fade in opacity toward the horizon.

    Parameters
    ----------
    draw : ImageDraw.ImageDraw
    w    : int — Canvas width.
    h    : int — Canvas height.
    """
    grid_color      = config.BANNER_GRID_COLOR          # "#8B0000"
    horizon_y       = int(h * 0.55)                     # where grid 'starts'
    vanishing_x     = w // 2
    num_h_lines     = 12                                 # horizontal lines
    num_v_lines     = 20                                 # vertical lines

    # ── Horizontal lines ─────────────────────────────────────
    for i in range(num_h_lines):
        t = i / num_h_lines                              # 0.0 → 1.0
        y = int(horizon_y + (h - horizon_y) * (t ** 1.8))
        # alpha fades from 30 (near horizon) to 120 (bottom)
        alpha = int(30 + 90 * t)
        r, g, b = 0x8B, 0x00, 0x00
        color = (r, g, b, alpha)
        draw.line([(0, y), (w, y)], fill=color, width=1)

    # ── Vertical lines (perspective fan) ─────────────────────
    for j in range(num_v_lines + 1):
        t = j / num_v_lines                              # 0.0 → 1.0
        # x-position at the bottom of the canvas
        bottom_x = int(t * w)
        draw.line(
            [(vanishing_x, horizon_y), (bottom_x, h)],
            fill=(0x8B, 0x00, 0x00, 60),
            width=1,
        )


def _draw_scanlines(img: Image.Image, w: int, h: int) -> Image.Image:
    """
    Overlay semi-transparent horizontal scanlines every 4 pixels for
    a CRT monitor aesthetic.

    Parameters
    ----------
    img : Image.Image — The base image (RGBA).
    w   : int
    h   : int

    Returns
    -------
    Image.Image — Composited result.
    """
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw   = ImageDraw.Draw(overlay)
    for y in range(0, h, 4):
        odraw.line([(0, y), (w, y)], fill=(0, 0, 0, 35), width=1)
    return Image.alpha_composite(img, overlay)


def _draw_neon_ring(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    color: str = "#FF0000",
    glow_passes: int = 6,
) -> None:
    """
    Draw a circular neon-glow ring by layering multiple concentric
    circles with decreasing opacity and increasing radius.

    Parameters
    ----------
    draw        : ImageDraw.ImageDraw
    cx          : int   — Centre X.
    cy          : int   — Centre Y.
    radius      : int   — Visible ring radius.
    color       : str   — Hex colour of the neon ring.
    glow_passes : int   — How many glow halos to render.
    """
    r, g, b = (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )
    # outer glow halos
    for i in range(glow_passes, 0, -1):
        glow_r  = radius + i * 3
        alpha   = int(15 * (glow_passes - i + 1))
        bbox    = [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r]
        draw.ellipse(bbox, outline=(r, g, b, alpha), width=2)

    # solid ring
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.ellipse(bbox, outline=(r, g, b, 255), width=3)


def _draw_corner_brackets(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    size: int,
    arm: int = 20,
    color: str = "#FF0000",
) -> None:
    """
    Draw four L-shaped corner brackets around a centred square region.
    Creates a 'targeted' / 'locked-on' hacker HUD effect.

    Parameters
    ----------
    draw  : ImageDraw.ImageDraw
    cx    : int   — Centre X of the bracketed area.
    cy    : int   — Centre Y.
    size  : int   — Half-width/height of the bracketed area.
    arm   : int   — Length of each bracket arm.
    color : str   — Bracket colour (hex).
    """
    r, g, b = (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )
    c    = (r, g, b, 220)
    left, top     = cx - size, cy - size
    right, bottom = cx + size, cy + size

    # top-left
    draw.line([(left, top), (left + arm, top)],           fill=c, width=2)
    draw.line([(left, top), (left, top + arm)],           fill=c, width=2)
    # top-right
    draw.line([(right, top), (right - arm, top)],         fill=c, width=2)
    draw.line([(right, top), (right, top + arm)],         fill=c, width=2)
    # bottom-left
    draw.line([(left, bottom), (left + arm, bottom)],     fill=c, width=2)
    draw.line([(left, bottom), (left, bottom - arm)],     fill=c, width=2)
    # bottom-right
    draw.line([(right, bottom), (right - arm, bottom)],   fill=c, width=2)
    draw.line([(right, bottom), (right, bottom - arm)],   fill=c, width=2)


def _paste_dp(
    base: Image.Image,
    dp_bytes: Optional[bytes],
    cx: int,
    cy: int,
    radius: int,
) -> None:
    """
    Paste a circular-cropped user DP into the base image.
    If no DP bytes are supplied, a placeholder filled circle is drawn.

    Parameters
    ----------
    base     : Image.Image    — The base RGBA canvas.
    dp_bytes : bytes | None   — Raw bytes of the user's profile photo.
    cx       : int            — Centre X for the DP circle.
    cy       : int            — Centre Y for the DP circle.
    radius   : int            — Radius of the circular crop.
    """
    diameter = radius * 2

    if dp_bytes is not None:
        try:
            dp_img = Image.open(io.BytesIO(dp_bytes)).convert("RGBA")
            dp_img = dp_img.resize((diameter, diameter), Image.LANCZOS)
        except Exception:
            dp_img = None
    else:
        dp_img = None

    if dp_img is None:
        # Placeholder: dark circle with a silhouette fill
        placeholder = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
        pd = ImageDraw.Draw(placeholder)
        pd.ellipse([0, 0, diameter, diameter], fill=(30, 0, 0, 255))
        # simple head silhouette
        pd.ellipse(
            [diameter // 3, diameter // 8, 2 * diameter // 3, diameter // 2],
            fill=(80, 0, 0, 255),
        )
        dp_img = placeholder

    # circular mask
    mask = Image.new("L", (diameter, diameter), 0)
    md   = ImageDraw.Draw(mask)
    md.ellipse([0, 0, diameter, diameter], fill=255)

    dp_img.putalpha(mask)
    base.paste(dp_img, (cx - radius, cy - radius), dp_img)


def _centered_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple,
    w: int,
    shadow: bool = True,
) -> None:
    """
    Render text centred horizontally at vertical position *y*.
    Optionally adds a dark drop-shadow for legibility.

    Parameters
    ----------
    draw   : ImageDraw.ImageDraw
    y      : int                 — Top-Y of the text.
    text   : str                 — The string to render.
    font   : ImageFont.ImageFont
    fill   : tuple               — RGBA colour tuple.
    w      : int                 — Canvas width (used for centering).
    shadow : bool                — Whether to draw a shadow (default True).
    """
    try:
        bbox   = draw.textbbox((0, 0), text, font=font)
        tw     = bbox[2] - bbox[0]
    except AttributeError:
        # Older Pillow — textsize fallback
        tw, _  = draw.textsize(text, font=font)  # type: ignore[arg-type]
    x = (w - tw) // 2

    if shadow:
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=font, fill=fill)


# ── Public API ────────────────────────────────────────────────

def generate_banner(dp_bytes: Optional[bytes] = None) -> str:
    """
    Generate the Velyn Nox Premium hacker-aesthetic banner and save it.

    Parameters
    ----------
    dp_bytes : bytes | None
        Raw bytes of the user's Telegram profile photo.
        Pass None to render the placeholder silhouette.

    Returns
    -------
    str
        Absolute path to the saved PNG file.
    """
    _ensure_assets_dir()

    w = config.BANNER_WIDTH   # 1024
    h = config.BANNER_HEIGHT  # 500

    # ── Step 1: Base RGBA canvas ──────────────────────────────
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # ── Step 2: Background fill ───────────────────────────────
    _draw_background(draw, w, h)

    # ── Step 3: Red perspective grid ─────────────────────────
    _draw_grid(draw, w, h)

    # ── Step 4: Paste DP (centred, upper third) ───────────────
    dp_cx     = w // 2
    dp_cy     = int(h * 0.38)
    dp_radius = 80
    _paste_dp(img, dp_bytes, dp_cx, dp_cy, dp_radius)

    # Re-acquire draw handle after paste
    draw = ImageDraw.Draw(img)

    # ── Step 5: Neon ring around DP ───────────────────────────
    _draw_neon_ring(draw, dp_cx, dp_cy, dp_radius + 6,
                    color=config.BANNER_NEON_COLOR, glow_passes=8)

    # ── Step 6: Corner brackets ───────────────────────────────
    _draw_corner_brackets(draw, dp_cx, dp_cy, dp_radius + 22,
                          arm=24, color=config.BANNER_NEON_COLOR)

    # ── Step 7: Typography ────────────────────────────────────
    font_large  = _load_font(52, bold=True)
    font_medium = _load_font(30, bold=True)
    font_small  = _load_font(18)

    # Headline — "S Y S T E M  C O M P R O M I S E D"
    headline = "S Y S T E M  C O M P R O M I S E D"
    _centered_text(
        draw, y=int(h * 0.72),
        text=headline,
        font=font_large,
        fill=(255, 0, 0, 255),
        w=w,
        shadow=True,
    )

    # Sub-line — "R O O T  A C C E S S"
    subline = "R O O T  A C C E S S"
    _centered_text(
        draw, y=int(h * 0.84),
        text=subline,
        font=font_medium,
        fill=(180, 0, 0, 230),
        w=w,
        shadow=True,
    )

    # Top-left watermark
    draw.text(
        (14, 12),
        f"[ VELYN NOX PREMIUM v{config.VERSION} ]",
        font=font_small,
        fill=(120, 0, 0, 180),
    )

    # Top-right timestamp-style label
    ts_label = "ACCESS: GRANTED"
    try:
        ts_bbox = draw.textbbox((0, 0), ts_label, font=font_small)
        ts_w    = ts_bbox[2] - ts_bbox[0]
    except AttributeError:
        ts_w, _ = draw.textsize(ts_label, font=font_small)  # type: ignore[arg-type]
    draw.text(
        (w - ts_w - 14, 12),
        ts_label,
        font=font_small,
        fill=(120, 0, 0, 180),
    )

    # ── Step 8: Scanline CRT overlay ─────────────────────────
    img = _draw_scanlines(img, w, h)

    # ── Step 9: Slight blur on entire image for glow bleed ───
    # We composite the original sharp layer over a blurred copy.
    blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
    img     = Image.blend(img, blurred, alpha=0.15)

    # ── Step 10: Save ─────────────────────────────────────────
    out_path = os.path.abspath(config.BANNER_OUTPUT_PATH)
    img.convert("RGB").save(out_path, format="PNG", optimize=True)
    logger.info(f"[BANNER] Saved to {out_path}")
    return out_path
