# ============================================================
# main.py — Velyn Nox Premium Bot Entry Point
#
# Responsibilities:
#   1. Initialise logging
#   2. Initialise the SQLite database (schema creation)
#   3. Spin up the Flask health-check server in a daemon thread
#      (keeps Render's free dyno alive via UptimeRobot pings)
#   4. Build the PTB Application
#   5. Register all handlers (start, admin, scraper, router)
#   6. Run the bot with run_polling()
# ============================================================

from __future__ import annotations

import logging
import threading
import os  # <-- FIX 1: Render port ke liye import kiya
from typing import Final

from flask import Flask
from telegram.ext import Application
from telegram.request import HTTPXRequest  # <-- FIX 2: Network timeout ke liye import

import config
import database.db as db
from handlers import start, admin, scraper, router

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    format  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    level   = logging.INFO,
)
# Suppress overly verbose library loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ── Flask health-check app ────────────────────────────────────

flask_app: Final[Flask] = Flask(__name__)


@flask_app.route("/")
def health_check():
    """
    Simple HTTP endpoint so UptimeRobot / Render can verify the
    dyno is alive.

    Returns
    -------
    tuple[str, int]
        A 200 OK response with a plain-text body.
    """
    return f"{config.BOT_NAME} — Online", 200


@flask_app.route("/ping")
def ping():
    """Secondary ping endpoint."""
    return "pong", 200


def _run_flask() -> None:
    """
    Start Flask in blocking mode.
    Intended to be run inside a daemon thread so it does not
    prevent the main asyncio loop from exiting.
    """
    # FIX 1: Render dynamic port deta hai, isliye os.environ use kiya
    port = int(os.environ.get("PORT", config.FLASK_PORT))
    
    flask_app.run(
        host   = "0.0.0.0",
        port   = port,
        debug  = False,
        use_reloader = False,
    )


def start_flask_thread() -> None:
    """
    Launch the Flask server in a background daemon thread.
    The thread is set as a daemon so Python will not wait for
    it when the main program exits.
    """
    thread = threading.Thread(target=_run_flask, daemon=True, name="flask-health")
    thread.start()
    logger.info(f"[MAIN] Flask health server started")


# ── PTB Application builder ───────────────────────────────────

def build_application() -> Application:
    """
    Construct and configure the python-telegram-bot Application.

    Steps:
        1. Use ApplicationBuilder with the bot token.
        2. Register handlers from each module in priority order:
               scraper (group 1-4) → start → admin (group 5)
               → router (groups 8-10) → error handler

    Returns
    -------
    Application
    """
    # FIX 2: Termux/Render network drop se bachne ke liye Timeout badhaya
    req = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)

    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .request(req)  # <-- FIX 2: Request inject kiya
        .build()
    )

    # ── Register handlers in dependency order ─────────────────
    # scraper registers groups 1-4 (document, session text, scrape text, add text)
    scraper.register(app)

    # start registers commands + menu callbacks
    start.register(app)

    # admin registers /admin command + admin callbacks + group-5 text handler
    admin.register(app)

    # router registers fallback handlers at groups 8-10 + error handler
    router.register(app)

    logger.info("[MAIN] All handlers registered.")
    return app


# ── Entry point ───────────────────────────────────────────────

def main() -> None:
    """
    Full startup sequence:
        1. Init DB
        2. Start Flask thread
        3. Build PTB app
        4. Run polling loop (blocks until Ctrl-C or SIGTERM)
    """
    logger.info(
        f"[MAIN] Starting {config.BOT_NAME} v{config.VERSION} "
        f"— owner={config.OWNER_ID}"
    )

    # ── 1. Database ───────────────────────────────────────────
    db.init_db()

    # ── 2. Flask thread ───────────────────────────────────────
    start_flask_thread()

    # ── 3 + 4. PTB app ───────────────────────────────────────
    application = build_application()

    logger.info("[MAIN] Bot polling started. Press Ctrl-C to stop.")
    application.run_polling(
        allowed_updates = [
            "message",
            "callback_query",
            "inline_query",
        ],
        drop_pending_updates = True,   # ignore backlog on restart
    )


if __name__ == "__main__":
    main()
