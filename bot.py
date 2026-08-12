import os
import asyncio
from aiohttp import web
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Сервери хурд барои он ки Render розӣ шавад ва хато накунад
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

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

async def main():
    # Веб-серверро ба кор медарорем, то Render хомӯш накунад
    asyncio.create_task(web_server())

    TOKEN = os.environ.get("TOKEN")
    app = Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot started...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
