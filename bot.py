import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

def load_users():
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            return set(line.strip() for line in f if line.strip().isdigit())
    return set()

users_set = load_users()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users_set:
        users_set.add(user_id)
        with open("users.txt", "a") as f:
            f.write(user_id + "\n")
            
    await update.message.reply_text("Салом! Ссылкаро аз чойи лозима партоед:")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Лутфан ссылкаи дуруст партоед.")
        return

    await update.message.reply_text("⏳ Зеркашӣ истодааст...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_video")
    
    # Танзимоти васеъшуда барои дастгирии Reels, Stories ва Highlights (Актуальное)
    ydl_opts = {
        'format': 'mp4[height<=720]/best[height<=720]/best',
        'outtmpl': 'video.mp4',
        'extractor_args': {
            'instagram': {
                'api_hostname': 'i.instagram.com',
            }
        },
        # Агар шумо cookie дошта бошед, метавонед дар папкаи бот файли cookies.txt монда ин сатрро фаъол кунед:
        # 'cookiefile': 'cookies.txt',
        'usenetrc': False,
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            duration = info.get('duration', None)
            width = info.get('width', None)
            height = info.get('height', None)
        
        keyboard = [
            [InlineKeyboardButton("🎵 Скачать мусиқи", callback_data=f"a_{url}")],
            [InlineKeyboardButton("📄 Получить текст", callback_data=f"t_{url}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Санҷиш барои он ки оё файл зеркашӣ шуд ё не
        if os.path.exists('video.mp4'):
            with open('video.mp4', 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    duration=duration,
                    width=width,
                    height=height,
                    caption="Видео, сторис ё актуальное бомуваффақият зеркашӣ шуд 👇",
                    reply_markup=reply_markup
                )
            os.remove('video.mp4')
        else:
            await update.message.reply_text("Медиафайл ёфт нашуд ё ссылка хато аст.")
            
    except Exception as e:
        await update.message.reply_text(f"Хатогӣ ҳангоми зеркашӣ (барои сторис шояд ворид шудан лозим шавад): {e}")
        if os.path.exists('video.mp4'):
            os.remove('video.mp4')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if "_" not in data:
        await query.message.reply_text("Хатогӣ рух дод.")
        return

    action, url = data.split("_", 1)
    message = query.message
    markup = message.reply_markup
    inline_keyboard = markup.inline_keyboard if markup else []

    if action == "a":
        await context.bot.send_chat_action(chat_id=message.chat_id, action="upload_audio")
        
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'audio.m4a',
            'extractor_args': {'instagram': {'api_hostname': 'i.instagram.com'}},
            'usenetrc': False,
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', None)
                title = info.get('title', 'Мусиқии медиа')

            if os.path.exists('audio.m4a'):
                with open('audio.m4a', 'rb') as audio_file:
                    await message.reply_audio(
                        audio=audio_file,
                        title=title,
                        duration=duration
                    )
                os.remove('audio.m4a')
            else:
                await message.reply_text("Мусиқии ин медиа ёфт нашуд.")

            # Тоза кардани тугмаи мусиқӣ
            new_keyboard = []
            for row in inline_keyboard:
                new_row = [btn for btn in row if not btn.callback_data.startswith("a_")]
                if new_row:
                    new_keyboard.append(new_row)

            new_markup = InlineKeyboardMarkup(new_keyboard) if new_keyboard else None
            await message.edit_reply_markup(reply_markup=new_markup)

        except Exception as e:
            await message.reply_text(f"Хатогӣ ҳангоми зеркашии мусиқи: {e}")
            if os.path.exists('audio.m4a'):
                os.remove('audio.m4a')

    elif action == "t":
        await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")

        ydl_opts = {
            'extract_flat': True, 
            'skip_download': True,
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Сарлавҳа нест')
                description = info.get('description', 'Описания ёфт нашуд.')

            text_result = f"📌 Сарлавҳа:\n{title}\n\n📝 Описания ва хештегҳо:\n{description}"
            
            if len(text_result) > 4096:
                text_result = text_result[:4093] + "..."

            await message.reply_text(text_result, parse_mode="Markdown")

            # Тоза кардани тугмаи текст
            new_keyboard = []
            for row in inline_keyboard:
                new_row = [btn for btn in row if not btn.callback_data.startswith("t_")]
                if new_row:
                    new_keyboard.append(new_row)

            new_markup = InlineKeyboardMarkup(new_keyboard) if new_keyboard else None
            await message.edit_reply_markup(reply_markup=new_markup)

        except Exception as e:
            await message.reply_text(f"Хатогӣ ҳангоми гирифтани текст: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(users_set)
    if total_users == 0:
        await update.message.reply_text("То ҳол ягон корбар фармони /start-ро пахш накардааст.")
    else:
        await update.message.reply_text(f"Шумораи корбарони боти шумо: {total_users} нафар")

def main():
    TOKEN = "8795068941:AAEBH5QJAs_lcrbKOqbqm5MNUr6f9CKV5vk"
    app = Application.builder().token(TOKEN).read_timeout(120).write_timeout(120).connect_timeout(120).pool_timeout(120).build()
        
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    PORT = int(os.environ.get("PORT", 10000))
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=webhook_url
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
