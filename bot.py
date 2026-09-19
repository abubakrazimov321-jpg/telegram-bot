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
        with open("users.txt", "a") as f:
            f.write(user_id + "\n")
            
    print(f"Корбар бо ID-и {user_id} фармони /start-ро пахш кард!")
    await update.message.reply_text("Салом! Ссылкаи видеои лозимаро видеоро партоед:")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Лутфан ссылкаи дуруст партоед.")
        return

    user_id = update.effective_user.id
    last_urls[user_id] = url

    # Тугмаҳо барои интихоб
    keyboard = [
        [InlineKeyboardButton("📥 Скачать видео", callback_data="dl_video")],
        [InlineKeyboardButton("🎵 Скачать музыку", callback_data="dl_audio")],
        [InlineKeyboardButton("📄 Получить текст", callback_data="get_text")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Ссылка қабул шуд! Чӣ кор кардан лозим аст? Тугмаи лозимиро пахш кунед:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = last_urls.get(user_id)

    if not url:
        await query.message.reply_text("Маълумоти ссылка ёфт нашуд. Бори дигар ссылкаро партоед.")
        return

    # 1. Зеркашии видео
    if query.data == "dl_video":
        # Нишон додани статуси "отправляет видео" дар болои чат
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_video")
        
        ydl_opts = {
            'format': 'mp4[height<=720]/best[height<=720]/best',
            'outtmpl': 'video.mp4',
            'extractor_args': {'instagram': {'api_hostname': 'i.instagram.com'}},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', None)
                width = info.get('width', None)
                height = info.get('height', None)
            
            with open('video.mp4', 'rb') as video_file:
                await query.message.reply_video(
                    video=video_file,
                    duration=duration,
                    width=width,
                    height=height
                )
            os.remove('video.mp4')
        except Exception as e:
            await query.message.reply_text(f"Хатогӣ ҳангоми зеркашии видео: {e}")
            if os.path.exists('video.mp4'):
                os.remove('video.mp4')

    # 2. Зеркашии мусиқа (аудиои пурра)
    elif query.data == "dl_audio":
        # Нишон додани статуси "отправляет аудио" дар болои чат
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_audio")
        
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'audio.m4a',
            'extractor_args': {'instagram': {'api_hostname': 'i.instagram.com'}},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', None)
                title = info.get('title', 'Мусиқии релс')

            with open('audio.m4a', 'rb') as audio_file:
                await query.message.reply_audio(
                    audio=audio_file,
                    title=title,
                    duration=duration
                )
            os.remove('audio.m4a')
        except Exception as e:
            await query.message.reply_text(f"Хатогӣ ҳангоми зеркашии мусиқи: {e}")
            if os.path.exists('audio.m4a'):
                os.remove('audio.m4a')

    # 3. Гирифтани текст ва описания
    elif query.data == "get_text":
        # Нишон додани статуси "печатает" дар болои чат
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="typing")

        ydl_opts = {'extract_flat': True, 'skip_download': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Сарлавҳа нест')
                description = info.get('description', 'Описания ёфт нашуд.')

            text_result = f"📌 Сарлавҳа:\n{title}\n\n📝 Описания ва хештегҳо:\n{description}"
            
            if len(text_result) > 4096:
                text_result = text_result[:4093] + "..."

            await query.message.reply_text(text_result, parse_mode="Markdown")
        except Exception as e:
            await query.message.reply_text(f"Хатогӣ ҳангоми гирифтани текст: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(users_set)
    if total_users == 0:
        await update.message.reply_text("То ҳол ягон корбар фармони /start-ро пахш накардааст.")
    else:
        await update.message.reply_text(f"Шумораи корбарони боти шумо: {total_users} нафар")

async def main():
    asyncio.create_task(web_server())

    TOKEN = "8795068941:AAEBH5QJAs_lcrbKOqbqm5MNUr6f9CKV5vk"
    app = Application.builder().token(TOKEN).read_timeout(120).write_timeout(120).connect_timeout(120).pool_timeout(120).build()
        
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("Bot started...")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
