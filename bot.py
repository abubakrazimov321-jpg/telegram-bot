import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import threading

# Flask сервер барои он ки Render розӣ шавад
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# Функцияҳои боти Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Салом! Ссылкаи видеоро партоед:")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Лутфан ссылкаи дуруст партовед.")
        return

    msg = await update.message.reply_text("Видео боргирӣ шуда истодааст...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await update.message.reply_video(video=open('video.mp4', 'rb'))
        await msg.delete()
        os.remove('video.mp4')
    except Exception as e:
        await msg.edit_text(f"Хатогӣ рух дод: {e}")

def main():
    # Сервери веб дар потоки алоҳида (background thread)
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    # Идоракунии боти Telegram
    TOKEN = os.environ.get("TOKEN")
    application = Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()
