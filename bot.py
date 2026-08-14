import os
import threading
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# 1. Танзими Flask барои Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# 2. Функсияи старт
def start(update, context):
    update.message.reply_text("Салом! ссилкаи лозимаатонро равон кунед!")

def main():
    # Токени боти шумо
    updater = Updater("8795068941:AAEvJ8xzh9oUOTZuala-jRVhEiaBThkSA8A", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    
    # Ботро дар фоне сар медиҳем
    updater.start_polling()

if __name__ == '__main__':
    # Бот ва серверро якҷоя медузавем
    threading.Thread(target=main).start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)