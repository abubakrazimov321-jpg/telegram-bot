import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# Мини-сервер барои нигоҳ доштани активгии бот дар Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

CHANNEL_USERNAME = "@trenddmarket_tj"

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Обуна шудан ба канал", url=f"https://t.me/trenddmarket_tj")],
            [InlineKeyboardButton("✅ Санҷиши обуна", callback_data="check_sub")]
        ]
        await update.message.reply_text(f"Лутфан аввал ба канали мо {CHANNEL_USERNAME} обуна шавед!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text("Салом! сылкаи видеои лозимаро аз Instagram, Tiktok, YouTube партоед:")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_subscription(query.from_user.id, context):
        await query.message.edit_text("Ташаккур! Акнун ссылкаи видеоро партоед:")
    else:
        await query.message.reply_text("Шумо ҳанӯз обуна нашудаед!")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        await update.message.reply_text(f"Лутфан ба канал обуна шавед: {CHANNEL_USERNAME}")
        return

    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Лутфан ссылкаи дурустро партоед.")
        return

    msg = await update.message.reply_text("Видео скачать шуда истодааст лутфан мунтазир шавед...")
    try:
        ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await update.message.reply_video(video=open('video.mp4', 'rb'))
        await msg.delete()
        os.remove('video.mp4')
    except Exception as e:
        await msg.edit_text(f"Хатогӣ: {e}")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    TOKEN = os.environ.get("TOKEN")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot is running...")
    app.run_polling()