#!/usr/bin/env python3
import logging
import time
import threading
import random
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    Filters
)
import psutil
import os
from config import *

# Configure robust logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename=LOG_FILE,
    filemode='a'
)
logger = logging.getLogger(__name__)

# Global variables
active_spams = {}
bot_start_time = datetime.now()

def load_messages(filename):
    """Load messages from file with error handling"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return [
            f"{{target}} Message file missing! ({filename})",
            f"{{target}} Please contact admin! ({filename})"
        ]

# Load raid messages
RAID_MESSAGES = load_messages('raid_messages.txt')
SRAID_MESSAGES = load_messages('sraid_messages.txt')

def is_admin(user_id: int) -> bool:
    """Check if user is admin/owner/sudo"""
    return user_id == OWNER_ID or user_id in SUDO_USERS

def get_uptime() -> str:
    """Calculate bot uptime"""
    uptime = datetime.now() - bot_start_time
    days, remainder = divmod(int(uptime.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def start(update: Update, context: CallbackContext) -> None:
    """Send interactive welcome message"""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📚 Commands Help", callback_data="help")],
        [InlineKeyboardButton("👥 Support Group", url=GROUP_LINK)],
        [InlineKeyboardButton("📢 Updates Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME[1:]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
✨ **Welcome {user.mention_html()}!** ✨

I'm a **Powerful Spam Bot** created by {OWNER_USERNAME} with advanced features:

• Multi-Token Support
• Smart Spam Controls
• Admin Protection
• Ultra-Fast Performance

📌 **Quick Access:**
🔹 /spam - Small spam (1-{SMALL_SPAM_LIMIT} msgs)
🔹 /bspam - Heavy spam (1-{BIG_SPAM_LIMIT} msgs)
🔹 /uspam - Unlimited spam (/stop to end)
🔹 /raid - Normal raid
🔹 /sraid - Shayari raid

📊 **Bot Status:** /alive
⚡ **Performance Check:** /ping
🛠 **All Commands:** /help
    """
    
    try:
        update.message.reply_photo(
            photo=open("assets/welcome.jpg", "rb") if os.path.exists("assets/welcome.jpg") else None,
            caption=welcome_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

def help_command(update: Update, context: CallbackContext) -> None:
    """Show help message with all commands"""
    help_text = f"""
📚 **Command List** 📚

🛡 **Admin Commands:**
├ /spam <count> <text> - Small spam (1-{SMALL_SPAM_LIMIT})
├ /bspam <count> <text> - Big spam (1-{BIG_SPAM_LIMIT})
├ /uspam <text> - Unlimited spam (/stop to end)
├ /raid <count> @username - Normal raid
└ /sraid <count> @username - Shayari raid (1-{SRAID_LIMIT})

📊 **Info Commands:**
├ /start - Start the bot
├ /ping - Check response time
├ /alive - Show bot status
└ /help - This message

👥 **Support:**
• Group: {GROUP_LINK}
• Channel: {CHANNEL_LINK}
• Owner: {OWNER_USERNAME}
    """
    update.message.reply_text(help_text, parse_mode="Markdown")

def ping(update: Update, context: CallbackContext) -> None:
    """Check bot latency"""
    start = time.time()
    message = update.message.reply_text("🏓 Pinging...")
    end = time.time()
    ping_time = round((end - start) * 1000, 2)
    message.edit_text(f"🏓 Pong! {ping_time}ms\n⏳ Uptime: {get_uptime()}")

def alive(update: Update, context: CallbackContext) -> None:
    """Check bot status with system info"""
    system_info = f"""
🖥 CPU: {psutil.cpu_percent()}%
🎮 RAM: {psutil.virtual_memory().percent}%
💾 Disk: {psutil.disk_usage('/').percent}%
    """
    try:
        with open("assets/alive.jpg", "rb") as photo:
            update.message.reply_photo(
                photo=photo,
                caption=(
                    f"🤖 **Bot is Alive!** 🤖\n\n"
                    f"⏳ Uptime: {get_uptime()}\n"
                    f"👑 Owner: {OWNER_USERNAME}\n"
                    f"{system_info}\n"
                    f"📢 Updates: {CHANNEL_LINK}"
                ),
                parse_mode="Markdown"
            )
    except FileNotFoundError:
        update.message.reply_text(
            f"🤖 **Bot is Alive!** 🤖\n\n"
            f"⏳ Uptime: {get_uptime()}\n"
            f"👑 Owner: {OWNER_USERNAME}\n"
            f"{system_info}\n"
            f"📢 Updates: {CHANNEL_LINK}",
            parse_mode="Markdown"
        )

def raid(update: Update, context: CallbackContext) -> None:
    """Handle normal raid command"""
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
            update.message.reply_text("⚠️ Server busy! Try again later.")
            return

        threading.Thread(
            target=execute_raid,
            args=(context.bot, update.message.chat_id, target, count)
        ).start()
        update.message.reply_text(f"⚔️ Raid started against {target}!")

    except (IndexError, ValueError):
        update.message.reply_text("❌ Usage: /raid <count> @username")

def sraid(update: Update, context: CallbackContext) -> None:
    """Handle shayari raid command"""
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("🚫 Admin only command!")
        return

    try:
        count = int(context.args[0])
        target = context.args[1]
        
        if count < 1 or count > SRAID_LIMIT:
            update.message.reply_text(f"❌ Count must be 1-{SRAID_LIMIT}!")
            return
        
        if threading.active_count() > MAX_THREADS:
            update.message.reply_text("⚠️ Server busy! Try again later.")
            return

        threading.Thread(
            target=execute_sraid,
            args=(context.bot, update.message.chat_id, target, count)
        ).start()
        update.message.reply_text(f"💘 Shayari raid started for {target}!")

    except (IndexError, ValueError):
        update.message.reply_text("❌ Usage: /sraid <count> @username")

def execute_raid(bot, chat_id, target, count):
    """Execute normal raid messages"""
    try:
        for _ in range(count):
            message = random.choice(RAID_MESSAGES).format(target=target)
            bot.send_message(chat_id=chat_id, text=message)
            time.sleep(RAID_COOLDOWN)
    except Exception as e:
        logger.error(f"Raid error: {e}")

def execute_sraid(bot, chat_id, target, count):
    """Execute shayari raid messages"""
    try:
        for _ in range(count):
            message = random.choice(SRAID_MESSAGES).format(target=target)
            bot.send_message(chat_id=chat_id, text=message)
            time.sleep(SRAID_COOLDOWN)
    except Exception as e:
        logger.error(f"Shayari raid error: {e}")

def spam_handler(update: Update, context: CallbackContext, spam_type: str) -> None:
    """Handle all spam commands"""
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("🚫 Admin only command!")
        return

    if not context.args or (spam_type != "uspam" and len(context.args) < 2):
        usage = {
            "spam": f"/spam <1-{SMALL_SPAM_LIMIT}> <text>",
            "bspam": f"/bspam <1-{BIG_SPAM_LIMIT}> <text>",
            "uspam": "/uspam <text>"
        }
        update.message.reply_text(f"❌ Usage: {usage[spam_type]}")
        return

    try:
        chat_id = update.message.chat_id
        
        if spam_type == "uspam":
            message = ' '.join(context.args)
            if chat_id in active_spams:
                update.message.reply_text("⚠️ Already spamming! Use /stop first.")
                return
            
            active_spams[chat_id] = True
            threading.Thread(
                target=infinite_spam,
                args=(context.bot, chat_id, message)
            ).start()
            update.message.reply_text("♾️ Unlimited spam started! Use /stop to end.")
        else:
            count = int(context.args[0])
            limit = SMALL_SPAM_LIMIT if spam_type == "spam" else BIG_SPAM_LIMIT
            
            if count < 1 or count > limit:
                update.message.reply_text(f"❌ Count must be 1-{limit}!")
                return
            
            message = ' '.join(context.args[1:])
            for _ in range(count):
                context.bot.send_message(chat_id=chat_id, text=message)
                time.sleep(SPAM_COOLDOWN)
                
    except Exception as e:
        logger.error(f"Spam error: {e}")
        update.message.reply_text("❌ Error processing your request!")

def infinite_spam(bot, chat_id, message):
    """Handle unlimited spam in background"""
    while active_spams.get(chat_id, False):
        try:
            bot.send_message(chat_id=chat_id, text=message)
            time.sleep(0.5)
        except:
            break

def stop_spam(update: Update, context: CallbackContext) -> None:
    """Stop unlimited spam"""
    chat_id = update.message.chat_id
    if chat_id in active_spams:
        del active_spams[chat_id]
        update.message.reply_text("🛑 Stopped all spam in this chat!")
    else:
        update.message.reply_text("ℹ️ No active spam to stop.")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle inline button callbacks"""
    query = update.callback_query
    if query.data == "help":
        help_command(update, context)
    query.answer()

def setup_bot(token):
    """Initialize and run a single bot instance with auto-restart"""
    while True:
        try:
            updater = Updater(token)
            dp = updater.dispatcher

            # Add all handlers
            dp.add_handler(CommandHandler("start", start))
            dp.add_handler(CommandHandler("help", help_command))
            dp.add_handler(CommandHandler("ping", ping))
            dp.add_handler(CommandHandler("alive", alive))
            dp.add_handler(CommandHandler("spam", lambda u, c: spam_handler(u, c, "spam")))
            dp.add_handler(CommandHandler("bspam", lambda u, c: spam_handler(u, c, "bspam")))
            dp.add_handler(CommandHandler("uspam", lambda u, c: spam_handler(u, c, "uspam")))
            dp.add_handler(CommandHandler("raid", raid))
            dp.add_handler(CommandHandler("sraid", sraid))
            dp.add_handler(CommandHandler("stop", stop_spam))
            dp.add_handler(CallbackQueryHandler(button_handler))

            updater.start_polling()
            logger.info(f"Bot started with token {token[:5]}...")
            updater.idle()  # Block until stopped
            
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            logger.info("Restarting bot in 10 seconds...")
            time.sleep(10)

def main():
    """Main execution with thread management"""
    # Create necessary directories
    if not os.path.exists("assets"):
        os.makedirs("assets")

    # Start each bot in a separate thread
    threads = []
    for token in BOT_TOKENS:
        t = threading.Thread(target=setup_bot, args=(token,))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(1)  # Stagger startup

    # Keep main thread alive
    while True:
        time.sleep(3600)  # Check hourly

if __name__ == '__main__':
    main()
