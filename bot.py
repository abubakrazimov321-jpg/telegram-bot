import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

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

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

def main():
    TOKEN = "8795068941:AAFtEH5Uo2uCigSMA5gV0cZO5t4o0snJ5c"
    app = Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
