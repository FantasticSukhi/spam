import logging
import time
import threading
import random
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import psutil
import os
from config import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename=LOG_FILE
)
logger = logging.getLogger(__name__)

# Global variables
active_spams = {}
bot_start_time = datetime.now()

def load_raid_messages():
    with open('raid_messages.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

RAID_MESSAGES = load_raid_messages()

def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in SUDO_USERS

def get_uptime() -> str:
    uptime = datetime.now() - bot_start_time
    days, remainder = divmod(int(uptime.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def raid(update: Update, context: CallbackContext) -> None:
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("🚫 Admin only command!")
        return

    try:
        count = int(context.args[0])
        target = context.args[1]
        
        if count < 1 or count > RAID_LIMIT:
            update.message.reply_text(f"❌ Count must be 1-{RAID_LIMIT}!")
            return
        
        if threading.active_count() > MAX_THREADS:
            update.message.reply_text("⚠️ Too many active raids! Try again later.")
            return

        threading.Thread(
            target=execute_raid,
            args=(context.bot, update.message.chat_id, target, count)
        ).start()
        update.message.reply_text(f"⚔️ Raid started against {target}!")

    except (IndexError, ValueError):
        update.message.reply_text("❌ Usage: /raid <count> @username")

def execute_raid(bot, chat_id, target, count):
    try:
        for _ in range(count):
            message = random.choice(RAID_MESSAGES).format(target=target)
            bot.send_message(chat_id=chat_id, text=message)
            time.sleep(RAID_COOLDOWN)
    except Exception as e:
        logger.error(f"Raid error: {e}")

# [Rest of your existing commands...]

def main():
    for token in BOT_TOKENS:
        try:
            updater = Updater(token)
            dp = updater.dispatcher

            # Add handlers
            dp.add_handler(CommandHandler("start", start))
            dp.add_handler(CommandHandler("help", help_command))
            dp.add_handler(CommandHandler("ping", ping))
            dp.add_handler(CommandHandler("alive", alive))
            dp.add_handler(CommandHandler("spam", lambda u, c: spam_handler(u, c, "spam")))
            dp.add_handler(CommandHandler("bspam", lambda u, c: spam_handler(u, c, "bspam")))
            dp.add_handler(CommandHandler("uspam", lambda u, c: spam_handler(u, c, "uspam")))
            dp.add_handler(CommandHandler("raid", raid))
            dp.add_handler(CommandHandler("stop", stop_spam))
            dp.add_handler(CallbackQueryHandler(button_handler))

            updater.start_polling()
            logger.info(f"Bot started with token {token[:5]}...")
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")

    threading.Event().wait()

if __name__ == '__main__':
    if not os.path.exists("assets"):
        os.makedirs("assets")
    main()
