import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
import yt_dlp
import telegram

# ---------------------- RENDER KEEP-ALIVE ----------------------
# Render's free tier requires a web server to stay "awake"
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    # Render automatically provides a PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()

# ---------------------- CONFIG ----------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 500 * 1024 * 1024  # Render free has limited RAM (512MB)

async def safe_edit(message, text):
    try:
        await message.edit_text(text)
    except Exception:
        pass

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 I am running on Render! Send me a link.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    status_msg = await update.message.reply_text("⬇️ Downloading...")
    filename = None

    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "format": "best", # 'best' avoids heavy FFmpeg merging which crashes low-RAM servers
        "quiet": True,
        "restrictfilenames": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as video_file:
            await update.message.reply_video(video=video_file, caption="✅ Success!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found!")
    else:
        keep_alive()  # <--- This starts the web server for Render
        print("🤖 Bot is starting...")
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling()