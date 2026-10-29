import os, threading, logging
from flask import Flask
from telegram.ext import Application
from telegram.request import HTTPXRequest
import config
import database.db as db
from handlers import start, admin, scraper, states, router, help

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = Flask(__name__)
@app.route('/')
def health_check(): return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

async def error_handler(update, context):
    logging.warning(f"Update caused error: {context.error}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    db.init_db()

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    application = Application.builder().token(config.BOT_TOKEN).request(request).build()

    scraper.register(application)
    start.register(application)
    admin.register(application)
    help.register(application)
    router.register(application)
    states.register(application)

    application.add_error_handler(error_handler)
    logging.info("Enterprise Bot is Live!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
