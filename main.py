import os
import asyncio
import threading
import logging
from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
import config
from handlers import start, admin, scraper, states
from database import db

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ── FLASK FOR RENDER ──
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Alive!"

def run_flask():
    # Render assigns a random PORT env variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ── ERROR HANDLER ──
async def error_handler(update, context):
    logging.warning(f"Update caused error: {context.error}")

# ── MAIN BOT LOGIC ──
def main():
    # Start Flask in a background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Init Database
    db.init_db()

    # Higher timeouts for Termux/Render network drops
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    application = Application.builder().token(config.BOT_TOKEN).request(request).build()

    # Commands
    application.add_handler(CommandHandler("start", start.start_cmd))
    application.add_handler(CommandHandler("myplan", start.myplan_cmd))
    application.add_handler(CommandHandler("admin", admin.admin_cmd))
    
    # Callbacks (Buttons)
    application.add_handler(CallbackQueryHandler(admin.admin_callbacks, pattern="^admin:"))
    application.add_handler(CallbackQueryHandler(scraper.scraper_callbacks, pattern="^menu:(scrape|add)$"))
    application.add_handler(CallbackQueryHandler(start.main_router))
    
    # State Machine Handlers (Text inputs)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, states.handle_states))

    # Error Handler
    application.add_error_handler(error_handler)

    logging.info("Enterprise Bot is Live!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
