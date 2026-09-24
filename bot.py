import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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

async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Оғоз кардани кор бо бот"),
        BotCommand("help", "Что умеет этот бот?")
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users_set:
        users_set.add(user_id)
        with open("users.txt", "a") as f:
            f.write(user_id + "\n")
            
    is_subscribed = await check_subscription(update.effective_user.id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("Обуна шудан ба канал", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Санҷиши обуна", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🚀 Барои истифодаи бот, лутфан аввал ба канали мо обуна шавед: https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
            reply_markup=reply_markup
        )
        return

    # Паёми хушомадгӯӣ пас аз пахш кардани старт
    welcome_text = (
        "<b>Добро пожаловать!</b>\n\n"
        "Вы можете скинуть мне ссылку на пост в <b>Instagram, TikTok, YouTube или Pinterest</b>, откуда нужно выгрузить <b>фото, видео, карусели, сторис, текст</b> и скачать <b>музыку</b> — через пару секунд всё будет у вас! 🚀\n\n"
        "На данный момент я поддерживаю загрузку контента из этих платформ без лишних лимитов и рекламы. Всё быстро, просто и удобно!"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Что умеет этот бот?", callback_data="about_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>✨ Что умеет этот бот?</b>\n\n"
        "Вы можете отправить боту ссылку на публикацию, а в ответ мгновенно получить <b>фото, видео, карусель (слайдшоу), сторис, текст</b> и возможность <b>скачать музыку</b> — всё это готово для сохранения и дальнейшего использования! 🚀\n\n"
        "🚫 <b>Никаких лишних лимитов и рекламы!</b> Всё быстро, просто и удобно."
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global url_counter
    user_id = update.effective_user.id

    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("Обуна шудан ба канал", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Санҷиши обуна", callback_data="check_sub")]
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
        'format': 'best',
        'outtmpl': 'downloaded_media-%(id)s.%(ext)s',
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
            description = info.get('description', '') or info.get('title', '')
            title = info.get('title', 'Мусиқӣ')
        
        url_counter += 1
        url_id = str(url_counter)
        url_storage[url_id] = {
            'url': url,
            'title': title,
            'caption': description
        }

        keyboard = [
            [InlineKeyboardButton("🎵 Скачать мусиқи", callback_data=f"a_{url_id}")]
        ]
        if description:
            keyboard.append([InlineKeyboardButton("📄 Получить текст", callback_data=f"t_{url_id}")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_any = False
        for f in os.listdir('.'):
            if f.startswith('downloaded_media-'):
                file_path = f
                ext = file_path.split('.')[-1].lower()
                sent_any = True
                
                with open(file_path, 'rb') as media_file:
                    if ext in ['jpg', 'jpeg', 'png', 'webp']:
                        await update.message.reply_photo(photo=media_file, reply_markup=reply_markup)
                    else:
                        await update.message.reply_video(video=media_file, reply_markup=reply_markup)
                os.remove(file_path)

        if not sent_any:
            await update.message.reply_text("лутфан ссилкаи дуруст партоед медиафайли ин ссилка ефт нашуд.")
            
    except Exception as e:
        await update.message.reply_text(f"Хатогӣ ҳангоми зеркашӣ: {e}")
        for f in os.listdir('.'):
            if f.startswith('downloaded_media-'):
                os.remove(f)

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

    if data == "about_bot":
        text = (
            "<b>✨ Что умеет этот бот?</b>\n\n"
            "Вы можете отправить боту ссылку на публикацию, а в ответ мгновенно получить <b>фото, видео, карусель (слайдшоу), сторис, текст</b> и возможность <b>скачать музыку</b> — всё это готово для сохранения и дальнейшего использования! 🚀\n\n"
            "🚫 <b>Никаких лишних лимитов и рекламы!</b> Всё быстро, просто и удобно."
        )
        await query.message.reply_text(text, parse_mode="HTML")
        return

    if "_" not in data:
        return

    action, url_id = data.split("_", 1)
    stored_data = url_storage.get(url_id)

    if not stored_data:
        await query.message.reply_text("Маълумоти ин ссылка кӯҳна шудааст, лутфан ссылкаро аз нав партоед.")
        return

    url = stored_data['url']
    video_title = stored_data['title']
    caption_text = stored_data['caption']
    message = query.message

    if action == "t":
        if caption_text:
            await message.reply_text(f"📄 **Матни пост:**\n\n{caption_text}", parse_mode="Markdown")
        else:
            await query.answer("Матн ё описание мавҷуд нест.", show_alert=True)
        return

    if action == "a":
        await context.bot.send_chat_action(chat_id=message.chat_id, action="upload_audio")
        
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'audio.m4a',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
            'extractor_args': {'instagram': {'api_hostname': 'i.instagram.com'}},
            'usenetrc': False,
            'quiet': True
        }

        try:
            success = False
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if 'entries' in info:
                        info = info['entries'][0]
                    duration = info.get('duration', 0)
                    title = info.get('title', video_title)
                    if duration and duration > 5:
                        success = True
            except Exception:
                success = False

            if not success and video_title:
                search_query = f"ytsearch1:{video_title}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search_query, download=True)
                    if 'entries' in info:
                        info = info['entries'][0]
                    duration = info.get('duration', None)
                    title = info.get('title', video_title)

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

        except Exception as e:
            await message.reply_text(f"Хатогӣ ҳангоми зеркашии мусиқи: {e}")
            if os.path.exists('audio.m4a'):
                os.remove('audio.m4a')

def main():
    TOKEN = "8795068941:AAEZ1u_n1luTl3H4mligLSqz5QYRRC_ZcB4"
    app = Application.builder().token(TOKEN).read_timeout(120).write_timeout(120).connect_timeout(120).pool_timeout(120).build()
        
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    app.job_queue.run_once(lambda context: set_bot_commands(app), 1)

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
