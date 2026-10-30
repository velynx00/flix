import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
import config
from core.context_osint import ContextOSINT

osint = ContextOSINT()

async def cmd_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.OWNER_ID: return
    if not context.args:
        return await update.message.reply_text("Usage: <code>/scrape &lt;url&gt;</code>", parse_mode=ParseMode.HTML)
    
    url = context.args[0]
    msg = await update.message.reply_text(f"⏳ Scraping: <code>{url}</code>...", parse_mode=ParseMode.HTML)
    
    # Bot ko freeze hone se bachane ke liye thread me chalaya ja raha hai
    result = await asyncio.to_thread(osint.scrape_url, url)
    
    await msg.delete()
    if result.startswith("Error:"):
        return await update.message.reply_text(f"❌ {result}")
    
    # Telegram 4096 limit handle karo
    for i in range(0, len(result), 4000):
        chunk = result[i:i+4000]
        await update.message.reply_text(f"<pre>{chunk}</pre>", parse_mode=ParseMode.HTML)

async def cmd_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.OWNER_ID: return
    if not context.args:
        return await update.message.reply_text("Usage: <code>/map &lt;domain&gt;</code>", parse_mode=ParseMode.HTML)
    
    domain = context.args[0]
    msg = await update.message.reply_text(f"⏳ Mapping: <code>{domain}</code>...", parse_mode=ParseMode.HTML)
    
    result = await asyncio.to_thread(osint.map_urls, domain)
    
    if isinstance(result, str) and result.startswith("Error:"):
        return await msg.edit_text(f"❌ {result}")
    if not result:
        return await msg.edit_text("❌ No URLs found.")
    
    text = f"<b>🌐 URLs on {domain}:</b>\n\n"
    for u in result[:20]:
        text += f"• <code>{u}</code>\n"
    if len(result) > 20:
        text += f"\n<i>...and {len(result) - 20} more.</i>"
        
    await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

def register(app: Application) -> None:
    app.add_handler(CommandHandler("scrape", cmd_scrape))
    app.add_handler(CommandHandler("map", cmd_map))
