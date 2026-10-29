import os, threading, logging
from flask import Flask
from telegram.ext import Application
from telegram.request import HTTPXRequest
from telegram import Update
from telegram.ext import ContextTypes
import config
from database.db import db
from handlers import start, admin, scraper, states, help, router

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = Flask(__name__)
@app.route('/')
def health_check(): return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger = logging.getLogger(__name__)
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(f"❌ Internal Error: {context.error}")
        except: pass

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    request = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)
    application = Application.builder().token(config.BOT_TOKEN).request(request).build()

    scraper.register(application)
    start.register(application)
    admin.register(application)
    help.register(application)
    router.register(application)
    states.register(application)

    application.add_error_handler(error_handler)
    logging.info("Enterprise Bot is Live!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)

if __name__ == "__main__":
    main()
