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

# Configure logging
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
            f"{{target}} Message file missing!",
            f"{{target}} Contact admin for help!"
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

def format_links():
    """Ensure all links are properly formatted"""
    owner_url = f"https://t.me/{OWNER_USERNAME.lstrip('@')}"
    group_url = GROUP_LINK if GROUP_LINK.startswith('http') else f"https://t.me/{GROUP_LINK.lstrip('@')}"
    channel_url = CHANNEL_LINK if CHANNEL_LINK.startswith('http') else f"https://t.me/{CHANNEL_LINK.lstrip('@')}"
    return owner_url, group_url, channel_url

def start(update: Update, context: CallbackContext) -> None:
    """Send interactive welcome message with perfect links"""
    user = update.effective_user
    owner_url, group_url, channel_url = format_links()
    
    keyboard = [
        [InlineKeyboardButton("📚 Commands Help", callback_data="help")],
        [InlineKeyboardButton("👥 Support Group", url=group_url)],
        [InlineKeyboardButton("📢 Updates Channel", url=channel_url)],
        [InlineKeyboardButton("👑 Contact Owner", url=owner_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
✨ <b>Welcome {user.mention_html()}!</b> ✨

I'm an <b>Advanced Spam Bot</b> with powerful features:

• <b>Multi-Token Support</b>
• <b>Smart Spam Controls</b>
• <b>Admin Protection</b>

<b>Quick Start:</b>
🔹 /spam - Small scale spamming
🔹 /sraid - Romantic shayari raid
🔹 /help - All commands

<b>Important Links:</b>
├ <a href="{group_url}">Support Group</a>
├ <a href="{channel_url}">Updates Channel</a>
└ <a href="{owner_url}">Contact Owner</a>
    """
    
    try:
        update.message.reply_photo(
            photo=open("assets/welcome.jpg", "rb") if os.path.exists("assets/welcome.jpg") else None,
            caption=welcome_text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Start error: {e}")
        update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

def help_command(update: Update, context: CallbackContext) -> None:
    """Show help with perfect links"""
    owner_url, group_url, channel_url = format_links()
    
    help_text = f"""
📚 <b>Command List</b> 📚

🛡 <b>Admin Commands:</b>
├ /spam <count> <text> - Small spam (1-{SMALL_SPAM_LIMIT})
├ /bspam <count> <text> - Big spam (1-{BIG_SPAM_LIMIT})
├ /uspam <text> - Unlimited spam
├ /raid <count> @user - Normal raid
└ /sraid <count> @user - Shayari raid

📊 <b>Info Commands:</b>
├ /start - Bot introduction
├ /ping - Check latency
└ /alive - System status

🔗 <b>Links:</b>
├ <a href="{group_url}">Support Group</a>
├ <a href="{channel_url}">Updates Channel</a>
└ <a href="{owner_url}">Contact Owner</a>
    """
    
    update.message.reply_text(
        help_text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

def ping(update: Update, context: CallbackContext) -> None:
    """Check bot latency"""
    start = time.time()
    message = update.message.reply_text("🏓 Pinging...")
    end = time.time()
    ping_ms = round((end - start) * 1000, 2)
    message.edit_text(f"🏓 Pong! {ping_ms}ms\n⏳ Uptime: {get_uptime()}")

def alive(update: Update, context: CallbackContext) -> None:
    """Show system status"""
    owner_url, group_url, channel_url = format_links()
    
    system_info = f"""
<b>System Status:</b>
🖥 CPU: {psutil.cpu_percent()}%
🎮 RAM: {psutil.virtual_memory().percent}%
💾 Disk: {psutil.disk_usage('/').percent}%

<b>Bot Info:</b>
⏳ Uptime: {get_uptime()}
👤 Owner: <a href="{owner_url}">{OWNER_USERNAME}</a>
    """
    
    try:
        update.message.reply_photo(
            photo=open("assets/alive.jpg", "rb") if os.path.exists("assets/alive.jpg") else None,
            caption=system_info,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Alive error: {e}")
        update.message.reply_text(
            system_info,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

def raid(update: Update, context: CallbackContext) -> None:
    """Normal raid command"""
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("🚫 Admin only!")
        return

    try:
        count = int(context.args[0])
        target = context.args[1]
        
        if count < 1 or count > RAID_LIMIT:
            update.message.reply_text(f"❌ Limit: 1-{RAID_LIMIT}!")
            return
        
        if threading.active_count() > MAX_THREADS:
            update.message.reply_text("⚠️ Server busy!")
            return

        threading.Thread(
            target=execute_raid,
            args=(context.bot, update.message.chat_id, target, count)
        ).start()
        update.message.reply_text(f"⚔️ Raid started for {target}!")

    except (IndexError, ValueError):
        update.message.reply_text("❌ Use: /raid <count> @user")

def sraid(update: Update, context: CallbackContext) -> None:
    """Shayari raid command"""
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("🚫 Admin only!")
        return

    try:
        count = int(context.args[0])
        target = context.args[1]
        
        if count < 1 or count > SRAID_LIMIT:
            update.message.reply_text(f"❌ Limit: 1-{SRAID_LIMIT}!")
            return
        
        if threading.active_count() > MAX_THREADS:
            update.message.reply_text("⚠️ Server busy!")
            return

        threading.Thread(
            target=execute_sraid,
            args=(context.bot, update.message.chat_id, target, count)
        ).start()
        update.message.reply_text(f"💘 Shayari for {target}!")

    except (IndexError, ValueError):
        update.message.reply_text("❌ Use: /sraid <count> @user")

def execute_raid(bot, chat_id, target, count):
    """Execute normal raid"""
    try:
        for _ in range(count):
            message = random.choice(RAID_MESSAGES).format(target=target)
            bot.send_message(chat_id=chat_id, text=message)
            time.sleep(RAID_COOLDOWN)
    except Exception as e:
        logger.error(f"Raid error: {e}")

def execute_sraid(bot, chat_id, target, count):
    """Execute shayari raid"""
    try:
        for _ in range(count):
            message = random.choice(SRAID_MESSAGES).format(target=target)
            bot.send_message(chat_id=chat_id, text=message)
            time.sleep(SRAID_COOLDOWN)
    except Exception as e:
        logger.error(f"Shayari error: {e}")

def spam_handler(update: Update, context: CallbackContext, spam_type: str) -> None:
    """Handle spam commands"""
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("🚫 Admin only!")
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
                update.message.reply_text("⚠️ Already spamming!")
                return
            
            active_spams[chat_id] = True
            threading.Thread(
                target=infinite_spam,
                args=(context.bot, chat_id, message)
            ).start()
            update.message.reply_text("♾️ Unlimited spam started!")
        else:
            count = int(context.args[0])
            limit = SMALL_SPAM_LIMIT if spam_type == "spam" else BIG_SPAM_LIMIT
            
            if count < 1 or count > limit:
                update.message.reply_text(f"❌ Limit: 1-{limit}!")
                return
            
            message = ' '.join(context.args[1:])
            for _ in range(count):
                context.bot.send_message(chat_id=chat_id, text=message)
                time.sleep(SPAM_COOLDOWN)
                
    except Exception as e:
        logger.error(f"Spam error: {e}")
        update.message.reply_text("❌ Error processing request!")

def infinite_spam(bot, chat_id, message):
    """Handle unlimited spam"""
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
        update.message.reply_text("🛑 Stopped spam!")
    else:
        update.message.reply_text("ℹ️ No active spam")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle inline buttons"""
    query = update.callback_query
    if query.data == "help":
        help_command(update, context)
    query.answer()

def setup_bot(token):
    """Initialize and run bot with auto-restart"""
    while True:
        try:
            updater = Updater(token)
            dp = updater.dispatcher

            # Register handlers
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
            updater.idle()
            
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            logger.info("Restarting in 10 seconds...")
            time.sleep(10)

def main():
    """Main execution with thread management"""
    # Create directories
    if not os.path.exists("assets"):
        os.makedirs("assets")

    # Start bots
    threads = []
    for token in BOT_TOKENS:
        t = threading.Thread(target=setup_bot, args=(token,))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(1)  # Stagger startup

    # Keep main thread alive
    while True:
        time.sleep(3600)

if __name__ == '__main__':
    main()
