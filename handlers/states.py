import logging
import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
)
from telethon import TelegramClient
from telethon.sessions import StringSession

import database.db as db
from core.engine import do_scrape
from utils.text import sc

logger = logging.getLogger(__name__)


async def handle_states(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waiting_for = context.user_data.get("waiting_for")
    if not waiting_for:
        return

    text = update.message.text.strip()

    # ── API SETUP FLOW ──────────────────────────────────────────

    if waiting_for == "api_id":
        if not text.isdigit():
            await update.message.reply_html(f"❌ <b>API ID must be a number.</b> Try again:")
            return
        context.user_data["api_id"]      = text
        context.user_data["waiting_for"] = "api_hash"
        await update.message.reply_html(
            f"✅ <b>API ID saved.</b>\n\n"
            f"<b>{sc('step 2/4: enter api hash')}:</b>"
        )

    elif waiting_for == "api_hash":
        context.user_data["api_hash"]    = text
        context.user_data["waiting_for"] = "api_phone"
        await update.message.reply_html(
            f"✅ <b>API Hash saved.</b>\n\n"
            f"<b>{sc('step 3/4: enter phone number')} (+91...):</b>"
        )

    elif waiting_for == "api_phone":
        api_id   = int(context.user_data["api_id"])
        api_hash = context.user_data["api_hash"]
        phone    = text

        client = TelegramClient(StringSession(), api_id, api_hash)
        try:
            await client.connect()
            await client.send_code_request(phone)
            context.user_data["client"]      = client
            context.user_data["phone"]       = phone
            context.user_data["waiting_for"] = "api_otp"
            await update.message.reply_html(
                f"📲 <b>OTP sent to {phone}.</b>\n\n"
                f"<b>{sc('step 4/4: enter the otp code')}:</b>\n"
                f"<i>Spaces are ignored automatically.</i>"
            )
        except Exception as e:
            context.user_data["waiting_for"] = None
            try:
                await client.disconnect()
            except Exception:
                pass
            await update.message.reply_html(f"❌ <b>Error:</b> <code>{e}</code>")

    elif waiting_for == "api_otp":
        client = context.user_data.get("client")
        if not client:
            context.user_data["waiting_for"] = None
            await update.message.reply_html("❌ Session expired. Use /start and try again.")
            return
        otp = text.replace(" ", "")
        try:
            await client.sign_in(context.user_data["phone"], otp)
            session_str = client.session.save()
            db.add_api(
                context.user_data["api_id"],
                context.user_data["api_hash"],
                context.user_data["phone"],
                session_str,
            )
            context.user_data["waiting_for"] = None
            await update.message.reply_html("✅ <b>Session added successfully!</b>")
            await client.disconnect()
        except Exception as e:
            if "SessionPasswordNeeded" in str(type(e).__name__):
                context.user_data["waiting_for"] = "api_2fa"
                await update.message.reply_html(
                    "🔐 <b>2FA is enabled on this account.</b>\n\n"
                    "<b>Enter your 2FA password:</b>"
                )
            else:
                context.user_data["waiting_for"] = None
                try:
                    await client.disconnect()
                except Exception:
                    pass
                await update.message.reply_html(f"❌ <b>OTP Error:</b> <code>{e}</code>")

    elif waiting_for == "api_2fa":
        client = context.user_data.get("client")
        if not client:
            context.user_data["waiting_for"] = None
            await update.message.reply_html("❌ Session expired. Use /start and try again.")
            return
        try:
            await client.sign_in(password=text)
            session_str = client.session.save()
            db.add_api(
                context.user_data["api_id"],
                context.user_data["api_hash"],
                context.user_data["phone"],
                session_str,
            )
            context.user_data["waiting_for"] = None
            await update.message.reply_html("✅ <b>Session added (2FA)!</b>")
            await client.disconnect()
        except Exception as e:
            context.user_data["waiting_for"] = None
            try:
                await client.disconnect()
            except Exception:
                pass
            await update.message.reply_html(f"❌ <b>2FA Error:</b> <code>{e}</code>")

    # ── SCRAPE / ADD FLOW ───────────────────────────────────────

    elif waiting_for == "target":
        context.user_data["target"]      = text
        context.user_data["waiting_for"] = "limit"
        await update.message.reply_html(
            f"<b>{sc('enter limit')} (1–50):</b>\n"
            f"<i>Free tier max is 50 members.</i>"
        )

    elif waiting_for == "limit":
        try:
            limit = int(text)
        except ValueError:
            await update.message.reply_html(f"❌ <b>Enter a valid number (1–50).</b>")
            return
        limit = max(1, min(limit, 50))
        context.user_data["limit"] = limit

        if context.user_data.get("action") == "add":
            context.user_data["waiting_for"] = "dest"
            await update.message.reply_html(
                f"<b>{sc('send the destination group link')}:</b>\n"
                f"<i>Bot must be admin in this group.</i>"
            )
        else:
            # Scrape only — kick off immediately
            context.user_data["waiting_for"] = None
            apis = db.get_apis()
            if not apis:
                await update.message.reply_html(
                    "❌ <b>No API session configured.</b>\n"
                    "Ask the owner to add one via /admin."
                )
                return
            await update.message.reply_html(
                f"⏳ <b>{sc('scraping started')}...</b>\n"
                f"Target: <code>{context.user_data['target']}</code>\n"
                f"Limit: <code>{limit}</code>"
            )
            asyncio.create_task(
                do_scrape(
                    context.bot,
                    update.message.chat_id,
                    apis[0],
                    context.user_data["target"],
                    limit,
                )
            )

    elif waiting_for == "dest":
        dest = text
        context.user_data["waiting_for"] = None
        apis = db.get_apis()
        if not apis:
            await update.message.reply_html(
                "❌ <b>No API session configured.</b>\n"
                "Ask the owner to add one via /admin."
            )
            return
        await update.message.reply_html(
            f"⏳ <b>{sc('adding started')}...</b>\n"
            f"Source: <code>{context.user_data['target']}</code>\n"
            f"Dest:   <code>{dest}</code>\n"
            f"Limit:  <code>{context.user_data['limit']}</code>\n\n"
            f"<i>10 second delay between each add to avoid ban.</i>"
        )
        asyncio.create_task(
            do_scrape(
                context.bot,
                update.message.chat_id,
                apis[0],
                context.user_data["target"],
                context.user_data["limit"],
                dest,
            )
        )


def register(app: Application) -> None:
    # MUST be registered LAST so it doesn't eat other text handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_states))
