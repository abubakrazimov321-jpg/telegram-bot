import os
from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp
import threading

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

CHANNEL_USERNAME = "@trenddmarket_tj"

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except Exception as e:
        print(f"Xatosi sravneniya: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Обуна шудан ба канал", url=f"https://t.me/trenddmarket_tj")],
            [InlineKeyboardButton("✅ Санҷиши обуна", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Лутфан аввал ба канали мо {CHANNEL_USERNAME} обуна шавед, то аз бот истифода баред!",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text("Салом! Ссылкаи видеои лозимаро аз Instagram, Tiktok, YouTube партоед:")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_subscribed = await check_subscription(user_id, context)
    
    if is_subscribed:
        await query.message.edit_text("Ташаккур! Акнун ссылкаи лозимаро партоед:")
    else:
        await query.message.reply_text("Шумо ҳанӯз ба канал обуна нашудаед. Лутфан аввал обуна шавед ва тугмаи санҷиши обунаро пахш кунед!")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Обуна шудан ба канал", url=f"https://t.me/trenddmarket_tj")],
            [InlineKeyboardButton("✅ Санҷиши обуна", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Барои истифодаи бот лутфан аввал ба канали мо {CHANNEL_USERNAME} обуна шавед!",
            reply_markup=reply_markup
        )
        return

    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Лутфан ссылкаи дуруст партооед.")
        return

    msg = await update.message.reply_text("Видео скачать шуда истодааст лутфан мунтазир шавед...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
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
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    TOKEN = os.environ.get("TOKEN")
    application = Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot started...")
    application.run_polling()
    if __name__ == "__main__":
        main()
