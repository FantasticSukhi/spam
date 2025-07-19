#!/usr/bin/env python3
import logging
from logging.handlers import RotatingFileHandler
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

# ======================
# LOGGING CONFIGURATION
# ======================
def setup_logging():
    """Configure advanced logging system"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:  # Only create dir if path contains directories
        os.makedirs(log_dir, exist_ok=True)
    
    # Set up rotating logs
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter(log_format))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[handler, console_handler]
    )

setup_logging()
logger = logging.getLogger(__name__)

# ======================
# GLOBAL VARIABLES
# ======================
active_spams = {}
active_raids = {}
bot_start_time = datetime.now()
RAID_MESSAGES = []
SRAID_MESSAGES = []

# ======================
# UTILITY FUNCTIONS
# ======================
def load_messages():
    """Load all message files"""
    global RAID_MESSAGES, SRAID_MESSAGES
    try:
        with open('raid_messages.txt', 'r', encoding='utf-8') as f:
            RAID_MESSAGES = [line.strip() for line in f if line.strip()]
        with open('sraid_messages.txt', 'r', encoding='utf-8') as f:
            SRAID_MESSAGES = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(RAID_MESSAGES)} raid and {len(SRAID_MESSAGES)} shayari messages")
    except Exception as e:
        logger.error(f"Error loading messages: {str(e)}", exc_info=True)
        RAID_MESSAGES = ["{target} RAID DEFAULT MESSAGE"]
        SRAID_MESSAGES = ["{target} SHAYARI DEFAULT MESSAGE"]

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

# ======================
# COMMAND HANDLERS
# ======================
def start(update: Update, context: CallbackContext) -> None:
    """Handle /start command"""
    try:
        user = update.effective_user
        owner_url, group_url, channel_url = format_links()
        
        keyboard = [
            [InlineKeyboardButton("📚 Commands Help", callback_data="help")],
            [InlineKeyboardButton("👥 Support Group", url=group_url)],
            [InlineKeyboardButton("📢 Updates Channel", url=channel_url)],
            [InlineKeyboardButton("👑 Contact Owner", url=owner_url)]
        ]
        
        welcome_text = f"""
✨ <b>Welcome {user.mention_html()}!</b> ✨

<b>Bot Features:</b>
• Multi-Token Support
• Advanced Spam Controls
• Admin Protection

<b>Quick Start:</b>
🔹 /spam - Small scale spamming
🔹 /sraid - Romantic shayari raid
🔹 /help - All commands
        """
        
        update.message.reply_photo(
            photo=open("assets/welcome.jpg", "rb") if os.path.exists("assets/welcome.jpg") else None,
            caption=welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Sent welcome message to {user.id}")
    except Exception as e:
        logger.error(f"Start command error: {str(e)}", exc_info=True)
        update.message.reply_text("🚫 Error processing your request!")

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle /help command"""
    try:
        owner_url, group_url, channel_url = format_links()
        
        help_text = f"""
<b>🛠️ Bot Commands Help</b>

<b>⚔️ Spam Commands:</b>
├ /spam <code>&lt;count&gt; &lt;text&gt;</code> - Normal spam (1-{SMALL_SPAM_LIMIT})
├ /bspam <code>&lt;count&gt; &lt;text&gt;</code> - Big spam (1-{BIG_SPAM_LIMIT})
├ /uspam <code>&lt;text&gt;</code> - Unlimited spam (<code>/stop</code> to end)
├ /raid <code>&lt;count&gt; @username</code> - Normal raid
└ /sraid <code>&lt;count&gt; @username</code> - Shayari raid

<b>🔗 Important Links:</b>
├ <a href="{group_url}">Support Group</a>
├ <a href="{channel_url}">Updates Channel</a>
└ <a href="{owner_url}">Contact Owner</a>
        """
        
        update.message.reply_text(
            text=help_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Sent help to {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Help command error: {str(e)}", exc_info=True)
        update.message.reply_text("ℹ️ Basic commands: /spam, /raid, /help")

def ping(update: Update, context: CallbackContext) -> None:
    """Handle /ping command"""
    try:
        start_time = time.time()
        message = update.message.reply_text("🏓 Pinging...")
        end_time = time.time()
        ping_ms = round((end_time - start_time) * 1000, 2)
        message.edit_text(f"🏓 Pong! {ping_ms}ms\n⏳ Uptime: {get_uptime()}")
        logger.info(f"Ping response: {ping_ms}ms")
    except Exception as e:
        logger.error(f"Ping command error: {str(e)}", exc_info=True)
        update.message.reply_text("❌ Couldn't calculate ping")

def alive(update: Update, context: CallbackContext) -> None:
    """Handle /alive command"""
    try:
        owner_url, group_url, channel_url = format_links()
        system_info = f"""
<b>System Status:</b>
🖥 CPU: {psutil.cpu_percent()}%
🎮 RAM: {psutil.virtual_memory().percent}%
💾 Disk: {psutil.disk_usage('/').percent}%

<b>Bot Info:</b>
⏳ Uptime: {get_uptime()}
👤 Owner: <a href="{owner_url}">{OWNER_USERNAME}</a>
🔢 Threads: {threading.active_count()}/{MAX_THREADS}
        """
        
        update.message.reply_photo(
            photo=open("assets/alive.jpg", "rb") if os.path.exists("assets/alive.jpg") else None,
            caption=system_info,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Sent alive status to {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Alive command error: {str(e)}", exc_info=True)
        update.message.reply_text("❌ Couldn't generate status")

def raid(update: Update, context: CallbackContext) -> None:
    """Handle /raid command"""
    try:
        if not is_admin(update.message.from_user.id):
            update.message.reply_text("🚫 Admin only command!")
            return

        if not context.args or len(context.args) < 2:
            update.message.reply_text("❌ Usage: /raid <count> @username")
            return

        count = int(context.args[0])
        target = context.args[1]

        if count < 1 or count > RAID_LIMIT:
            update.message.reply_text(f"❌ Count must be between 1-{RAID_LIMIT}!")
            return

        active_threads = threading.active_count()
        if active_threads > MAX_THREADS:
            update.message.reply_text(f"⚠️ Server busy! (Threads: {active_threads}/{MAX_THREADS})")
            return

        if update.message.chat_id in active_raids:
            update.message.reply_text("⚠️ Another raid is already active in this chat!")
            return

        active_raids[update.message.chat_id] = True
        threading.Thread(
            target=execute_raid,
            args=(context.bot, update.message.chat_id, target, count),
            daemon=True
        ).start()
        
        update.message.reply_text(f"⚔️ Raid started against {target}!")
        logger.info(f"Raid started by {update.effective_user.id} on {target} for {count} messages")

    except ValueError:
        update.message.reply_text("❌ Invalid count! Usage: /raid <count> @username")
    except Exception as e:
        logger.error(f"Raid command error: {str(e)}", exc_info=True)
        update.message.reply_text("❌ Error starting raid!")

def execute_raid(bot, chat_id, target, count):
    """Execute raid messages"""
    try:
        for i in range(count):
            if not active_raids.get(chat_id, False):
                break
                
            try:
                message = random.choice(RAID_MESSAGES).format(target=target)
                bot.send_message(chat_id=chat_id, text=message)
                
                if (i+1) % 10 == 0:
                    logger.info(f"Sent {i+1}/{count} raid messages to {target}")
                
                time.sleep(RAID_COOLDOWN)
                
            except Exception as msg_error:
                logger.error(f"Error sending raid message {i+1}: {str(msg_error)}")
                time.sleep(2)
                
    except Exception as e:
        logger.error(f"Raid execution failed: {str(e)}", exc_info=True)
    finally:
        active_raids.pop(chat_id, None)
        logger.info(f"Raid completed on {target}")

def sraid(update: Update, context: CallbackContext) -> None:
    """Handle /sraid command"""
    try:
        if not is_admin(update.message.from_user.id):
            update.message.reply_text("🚫 Admin only command!")
            return

        if not context.args or len(context.args) < 2:
            update.message.reply_text("❌ Usage: /sraid <count> @username")
            return

        count = int(context.args[0])
        target = context.args[1]

        if count < 1 or count > SRAID_LIMIT:
            update.message.reply_text(f"❌ Count must be between 1-{SRAID_LIMIT}!")
            return

        active_threads = threading.active_count()
        if active_threads > MAX_THREADS:
            update.message.reply_text(f"⚠️ Server busy! (Threads: {active_threads}/{MAX_THREADS})")
            return

        if update.message.chat_id in active_raids:
            update.message.reply_text("⚠️ Another raid is already active in this chat!")
            return

        active_raids[update.message.chat_id] = True
        threading.Thread(
            target=execute_sraid,
            args=(context.bot, update.message.chat_id, target, count),
            daemon=True
        ).start()
        
        update.message.reply_text(f"💘 Shayari raid started for {target}!")
        logger.info(f"Shayari raid by {update.effective_user.id} on {target} for {count} messages")

    except ValueError:
        update.message.reply_text("❌ Invalid count! Usage: /sraid <count> @username")
    except Exception as e:
        logger.error(f"Shayari command error: {str(e)}", exc_info=True)
        update.message.reply_text("❌ Error starting shayari raid!")

def execute_sraid(bot, chat_id, target, count):
    """Execute shayari raid"""
    try:
        for i in range(count):
            if not active_raids.get(chat_id, False):
                break
                
            try:
                message = random.choice(SRAID_MESSAGES).format(target=target)
                bot.send_message(chat_id=chat_id, text=message)
                
                if (i+1) % 5 == 0:
                    logger.info(f"Sent {i+1}/{count} shayaris to {target}")
                
                time.sleep(SRAID_COOLDOWN)
                
            except Exception as msg_error:
                logger.error(f"Error sending shayari {i+1}: {str(msg_error)}")
                time.sleep(3)
                
    except Exception as e:
        logger.error(f"Shayari execution failed: {str(e)}", exc_info=True)
    finally:
        active_raids.pop(chat_id, None)
        logger.info(f"Shayari raid completed on {target}")

def stop_spam(update: Update, context: CallbackContext) -> None:
    """Handle /stop command"""
    try:
        chat_id = update.message.chat_id
        if chat_id in active_spams:
            del active_spams[chat_id]
            update.message.reply_text("🛑 Stopped unlimited spam!")
            logger.info(f"Stopped spam in chat {chat_id}")
        elif chat_id in active_raids:
            del active_raids[chat_id]
            update.message.reply_text("🛑 Stopped active raid!")
            logger.info(f"Stopped raid in chat {chat_id}")
        else:
            update.message.reply_text("ℹ️ No active spam or raid to stop")
    except Exception as e:
        logger.error(f"Stop command error: {str(e)}", exc_info=True)
        update.message.reply_text("❌ Error stopping activities")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle inline button callbacks"""
    query = update.callback_query
    try:
        if query.data == "help":
            help_command(update, context)
        query.answer()
        logger.info(f"Handled button press: {query.data}")
    except Exception as e:
        logger.error(f"Button handler error: {str(e)}", exc_info=True)

# ======================
# MAIN BOT SETUP
# ======================
def setup_bot(token):
    """Initialize and run a bot instance"""
    while True:
        try:
            logger.info(f"Starting bot with token {token[:5]}...")
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
            logger.info(f"Bot {token[:5]}... is now running")
            updater.idle()
            
        except Exception as e:
            logger.critical(f"Bot crashed: {str(e)}", exc_info=True)
            logger.info("Restarting bot in 10 seconds...")
            time.sleep(10)

def main():
    """Main entry point"""
    try:
        logger.info("===== Starting SpamBot System =====")
        logger.info(f"Owner ID: {OWNER_ID}")
        logger.info(f"Sudo Users: {SUDO_USERS}")
        logger.info(f"Using {len(BOT_TOKENS)} bot tokens")
        
        # Load message files
        load_messages()
        
        # Create assets directory if not exists
        if not os.path.exists("assets"):
            os.makedirs("assets")
        
        # Start all bots
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
            
    except Exception as e:
        logger.critical(f"Fatal error in main: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
