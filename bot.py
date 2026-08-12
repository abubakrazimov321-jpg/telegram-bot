import os
from httpcore import __name
import yt_dlp
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8795068941:AAFtEHI5Uo2uCig5MA5gV0cZOSt4o0snJ5c"

CHANNEL_USERNAME = "@trenddmarket_tj"
CHANNEL_URL = "https://t.me/trenddmarket_tj"

video_captions = {}

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Обуна шудан ба канал", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ Санҷидани обуна", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ Барои истифодаи бот, лутфан аввал ба канали мо обуна шавед!",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text(
        "✅ Обунаи шумо тасдиқ шуд!\n\n"
        "Лутфан линки даркории худро аз Instagram, YouTube ё TikTok фиристед."
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check_sub":
        if await check_subscription(user_id, context):
            await query.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Обунаи шумо тасдиқ шуд!\n\n"
                     "Лутфан линки даркории худро аз Instagram, YouTube ё TikTok фиристед."
            )
        else:
            await query.answer("❌ Шумо ҳанӯз ба канал обуна нашудаед!", show_alert=True)
            
    elif query.data == "get_caption":
        caption = video_captions.get(user_id, "Описания ёфт нашуд ё холӣ аст.")
        await query.message.reply_text(f"📝 **Тексти пост / Описания:**\n\n{caption}")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Обуна шудан ба канал", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ Санҷидани обуна", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            " Барои зеркашии видео, аввал бояд ба канали мо обуна шавед!",
            reply_markup=reply_markup
        )
        return

    url = update.message.text.strip()
    status_msg = await update.message.reply_text("⏳ Видео скачат шуда истодааст интизор шавед...")

    filename = None
    try:
        ydl_opts = {
            "outtmpl": "downloaded_video.%(ext)s",
            "format": "best[filesize<50M]/b",  # Файлҳои сабук ва зуд зеркашишавандаро меинтихоб кунад
            "quiet": True,
            "no_warnings": True,
            "skip_download": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            description = info.get("description", "")

        if not os.path.exists(filename):
            for file in os.listdir("."):
                if file.startswith("downloaded_video."):
                    filename = file
                    break

        video_captions[user_id] = description if description else "Описания мавҷуд нест."

        with open(filename, "rb") as video:
            await update.message.reply_video(video=video, read_timeout=300, write_timeout=300)

        keyboard = [
            [InlineKeyboardButton("Получить текст поста", callback_data="get_caption")]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Нажмите, чтобы получить текст поста 👇🏻",
            reply_markup=reply_markup
        )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text("❌ Хато шуд: Видео скачат нашуд.")

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

app = Application.builder().read_timeout(60).write_timeout(60).token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

print("Bot started...")
if __name__ == "__main__":
    print("Bot started...")
    app.run_polling() 