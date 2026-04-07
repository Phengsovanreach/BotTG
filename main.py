import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp

# --- បង្កើត Web Server តូចមួយដើម្បីឱ្យ Render ស្គាល់ (សម្រាប់គម្រោង Free) ---
app_web = Flask('')
@app_web.route('/')
def home():
    return "Bot is running!"

def run_web():
    # Render នឹងផ្តល់ Port ឱ្យតាមរយៈ Environment Variable
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# ---------------- CONFIG ----------------
TOKEN = "8237446590:AAFUWWuMiPGmuAnK0n3oYxDzNlO08hqKPp0"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 សួស្តី Morgan! ផ្ញើ Link មកខ្ញុំដើម្បីទាញយកវីដេអូ។")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    status = await update.message.reply_text("⬇️ កំពុងទាញយក... សូមរង់ចាំ")
    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "cookiefile": "cookies.txt",  # កុំភ្លេចដាក់ File នេះក្នុង GitHub ផង
        "merge_output_format": "mp4"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
        
        with open(filename, "rb") as video:
            await update.message.reply_video(video=video, caption=f"✅ {info.get('title')}")
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    finally:
        await status.delete()

def main():
    # បើក Web Server នៅ Background ដើម្បីកុំឱ្យ Render បិទ Bot យើង
    Thread(target=run_web).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()