import os
import asyncio

# Функсия барои хондани корбарон аз файл
def load_users():
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            return set(line.strip() for line in f if line.strip().isdigit())
    return set()

users_set = load_users()
last_urls = {}

from aiohttp import web
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

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
    user_id = str(update.effective_user.id)
    if user_id not in users_set:
        users_set.add(user_id)
        # ID-ро дар файл сабт мекунем, то тоза нашавад
        with open("users.txt", "a") as f:
            f.write(user_id + "\n")
            
    print(f"Корбар бо ID-и {user_id} фармони /start-ро пахш кард!")
    await update.message.reply_text("Салом! Ссылкаи видеоро партоед:")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Лутфан ссылкаи дуруст партоед.")
        return

    user_id = update.effective_user.id
    last_urls[user_id] = url

    msg = await update.message.reply_text("Видео скачать шуда истодааст лутфан мунтазир шавед...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        keyboard = [[InlineKeyboardButton("📄 Получить текст поста", callback_data="get_text")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_video(
            video=open('video.mp4', 'rb'),
            reply_markup=reply_markup
        )
        await msg.delete()
        os.remove('video.mp4')
    except Exception as e:
        await msg.edit_text(f"Хатогӣ рух дод: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_text":
        user_id = query.from_user.id
        url = last_urls.get(user_id)

        if not url:
            await query.message.reply_text("Маълумоти видео ёфт нашуд. Бори дигар ссылкаро партоед.")
            return

        await query.message.reply_text("Лутфан мунтазир шавед, матни пост ва хештегҳо гирифта истодаанд...")

        ydl_opts = {'extract_flat': True, 'skip_download': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Сарлавҳа нест')
                description = info.get('description', 'Описания ёфт нашуд.')

            text_result = f"📌 **Сарлавҳа:**\n{title}\n\n📝 **Описания ва хештегҳо:**\n{description}"
            
            if len(text_result) > 4096:
                text_result = text_result[:4093] + "..."

            await query.message.reply_text(text_result, parse_mode="Markdown")
        except Exception as e:
            await query.message.reply_text(f"Хатогӣ ҳангоми гирифтани текст: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(users_set)
    print(f"Касе оморро хост. Шумораи корбарон: {total_users}")
    if total_users == 0:
        await update.message.reply_text("То ҳол ягон корбар фармони /start-ро пахш накардааст.")
    else:
        await update.message.reply_text(f"Шумораи корбарони боти шумо: {total_users} нафар")

async def main():
    asyncio.create_task(web_server())

    TOKEN = "8795068941:AAHOByRd5heZm7jyNQekDRBpUjfAM-6_Wqk"
    app = Application.builder().token(TOKEN).read_timeout(120).write_timeout(120).connect_timeout(120).pool_timeout(120).build()
        
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("Bot started...")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
