import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Канали худи шумо
CHANNEL_USERNAME = "@trenddmarket_tj"

def load_users():
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            return set(line.strip() for line in f if line.strip().isdigit())
    return set()

users_set = load_users()

url_storage = {}
url_counter = 0

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users_set:
        users_set.add(user_id)
        with open("users.txt", "a") as f:
            f.write(user_id + "\n")
            
    is_subscribed = await check_subscription(update.effective_user.id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("ПЕРЕЙТИ В КАНАЛ", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🚀 Барои истифодаи бот, лутфан аввал ба канали мо обуна шавед: https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text("Салом! Ссылкаи видео, релс ё сторисро партоед:")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global url_counter
    user_id = update.effective_user.id

    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("ПЕРЕЙТИ В КАНАЛ", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🚀 Барои истифодаи бот, лутфан аввал ба канали мо обуна шавед: https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
            reply_markup=reply_markup
        )
        return

    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Лутфан ссылкаи дуруст партоед.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_video")
    
    ydl_opts = {
        'format': 'mp4[height<=720]/best[height<=720]/best',
        'outtmpl': 'video.mp4',
        'extractor_args': {
            'instagram': {
                'api_hostname': 'i.instagram.com',
            }
        },
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
        
        url_counter += 1
        url_id = str(url_counter)
        url_storage[url_id] = url

        keyboard = [
            [InlineKeyboardButton("🎵 Скачать мусиқи", callback_data=f"a_{url_id}")],
            [InlineKeyboardButton("📄 Получить текст", callback_data=f"t_{url_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if os.path.exists('video.mp4'):
            with open('video.mp4', 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    duration=duration,
                    width=width,
                    height=height,
                    reply_markup=reply_markup
                )
            os.remove('video.mp4')
        else:
            await update.message.reply_text("Медиафайл ёфт нашуд ё ссылка хато аст.")
            
    except Exception as e:
        await update.message.reply_text(f"Хатогӣ ҳангоми зеркашӣ: {e}")
        if os.path.exists('video.mp4'):
            os.remove('video.mp4')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "check_sub":
        is_subscribed = await check_subscription(query.from_user.id, context)
        if is_subscribed:
            await query.message.edit_text("✅ Ташаккур барои обуна шудан! Акнун ссылкаи видеоро партоед:")
        else:
            await query.answer("❌ Шумо ҳанӯз ба канал обуна нашудаед!", show_alert=True)
        return

    if "_" not in data:
        await query.message.reply_text("Хатогӣ рух дод.")
        return

    action, url_id = data.split("_", 1)
    url = url_storage.get(url_id)

    if not url:
        await query.message.reply_text("Маълумоти ин ссылка кӯҳна шудааст, лутфан ссылкаро аз нав партоед.")
        return

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

            text_result = f"📌 Сарлавҳа:\n{title}\n\n📝 Описания:\n{description}"
            
            if len(text_result) > 4096:
                text_result = text_result[:4093] + "..."

            await message.reply_text(text_result, parse_mode="Markdown")

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
    TOKEN = "8795068941:AAG908tyqDVKGBC7bSY9GlR-_wqp7OYc_cc"
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
