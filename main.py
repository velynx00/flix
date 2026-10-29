import os
import threading
import logging

from flask import Flask
from telegram.ext import Application
from telegram.request import HTTPXRequest

import config
import database.db as db
from handlers import start, admin, scraper, states, help

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)

# ── Flask health check ────────────────────────────────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def health_check():
    return "Nox Syndicate Bot — Online ✅", 200

def run_flask() -> None:
    port = int(os.environ.get("PORT", config.FLASK_PORT))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


# ── Global error handler ──────────────────────────────────────
async def error_handler(update: object, context) -> None:
    logging.warning(f"Update caused error: {context.error}")


# ── Entry point ───────────────────────────────────────────────
def main() -> None:
    # Start Flask in daemon thread so Render keeps the dyno alive
    threading.Thread(target=run_flask, daemon=True).start()
    logging.info("Flask health check thread started.")

    db.init_db()
    logging.info("Database initialised.")

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .request(request)
        .build()
    )

    # Register handlers — ORDER MATTERS:
    # scraper, admin, help, start first; states LAST (catches all text)
    scraper.register(application)
    admin.register(application)
    help.register(application)
    start.register(application)
    states.register(application)     # ← MUST be last

    application.add_error_handler(error_handler)

    logging.info("Nox Syndicate Bot is live!")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
