# ============================================================
# config.py — Global Configuration for Velyn Nox Premium Bot
# All hardcoded credentials and constants live here.
# ============================================================

# ── Telegram Bot Credentials ──────────────────────────────────
BOT_TOKEN: str = "9036560812:AAHlvRIN3tCN8a2HTYpWD50YsbDBQ6mm_xQ"

# ── Owner / Admin ─────────────────────────────────────────────
OWNER_ID: int = 8576582616

# ── Update Channel ────────────────────────────────────────────
UPDATE_CHANNEL_URL: str = "https://t.me/xi5nxu"

# ── Default Telethon API Credentials ─────────────────────────
# Users who do NOT supply their own API ID/Hash will fall back to these.
DEFAULT_API_ID: int = 36949822
DEFAULT_API_HASH: str = "d1f2cf120b72f1d586e01bfba05d08d5"

# ── Database ──────────────────────────────────────────────────
DATABASE_PATH: str = "velyn_nox.db"

# ── Flask UptimeRobot Config ──────────────────────────────────
# Flask listens on this port so Render's health check keeps the dyno alive.
FLASK_PORT: int = 8080

# ── Scraper / Adder Engine Limits ─────────────────────────────
# How long (in seconds) to wait between each add attempt.
ADD_DELAY_SECONDS: int = 10

# Maximum members scraped per session (free tier cap).
FREE_SCRAPE_LIMIT: int = 50

# Maximum members that can be added per session (free tier cap).
FREE_ADD_LIMIT: int = 20

# ── Premium Plan Durations (in days) ─────────────────────────
PLAN_DURATIONS: dict = {
    "trial":   1,
    "weekly":  7,
    "monthly": 30,
    "yearly":  365,
}

# ── Pillow Banner Settings ────────────────────────────────────
BANNER_WIDTH:  int = 1024
BANNER_HEIGHT: int = 500
BANNER_BG_COLOR:   str = "#050000"   # near-black with a hint of red
BANNER_GRID_COLOR: str = "#8B0000"   # dark-red grid lines
BANNER_NEON_COLOR: str = "#FF0000"   # bright red neon ring
BANNER_TEXT_COLOR: str = "#FF0000"   # headline text
BANNER_SUB_COLOR:  str = "#CC0000"   # sub-headline text
BANNER_OUTPUT_PATH: str = "assets/banner.png"

# ── Version String ────────────────────────────────────────────
VERSION: str = "2.0.0"
BOT_NAME: str = "Velyn Nox Premium"
