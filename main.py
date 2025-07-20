import asyncio
import os
import random
import sys
import time
from threading import Thread
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import psutil

# Global variables
active_spams = {}
active_uspams = {}
raid_messages = []
shayari_messages = []
bots = {}

# Load configuration
def load_config():
    # Put your bot tokens here
    bot_tokens = [
        "YOUR_BOT_TOKEN_1",
        "YOUR_BOT_TOKEN_2",
        # Add more tokens as needed
    ]
    
    # Load raid messages (one per line)
    global raid_messages
    try:
        with open('raid.txt', 'r', encoding='utf-8') as f:
            raid_messages = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raid_messages = ["RAID MESSAGE DEFAULT 1", "RAID MESSAGE DEFAULT 2"]
    
    # Load shayari messages (one per line)
    global shayari_messages
    try:
        with open('shayari.txt', 'r', encoding='utf-8') as f:
            shayari_messages = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        shayari_messages = ["SHAYARI MESSAGE DEFAULT 1", "SHAYARI MESSAGE DEFAULT 2"]
    
    return bot_tokens

# Initialize bots
async def initialize_bots(bot_tokens):
    for token in bot_tokens:
        try:
            bot = Bot(token)
            me = await bot.get_me()
            bots[token] = {
                'instance': bot,
                'username': me.username,
                'available': True
            }
            print(f"Bot @{me.username} initialized successfully!")
        except Exception as e:
            print(f"Failed to initialize bot with token {token[:10]}...: {e}")

# Get an available bot
def get_available_bot():
    for token, bot_data in bots.items():
        if bot_data['available']:
            return bot_data['instance']
    return None

# Spam command handler
async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /spam <count (1-999)> <message>")
        return
    
    try:
        count = int(context.args[0])
        if count < 1 or count > 999:
            await update.message.reply_text("Count must be between 1 and 999")
            return
    except ValueError:
        await update.message.reply_text("Count must be a number")
        return
    
    message = ' '.join(context.args[1:])
    chat_id = update.message.chat_id
    
    active_spams[chat_id] = True
    
    bot = get_available_bot()
    if not bot:
        await update.message.reply_text("No available bots at the moment")
        return
    
    for i in range(count):
        if not active_spams.get(chat_id, False):
            break
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            await asyncio.sleep(0.5)  # Small delay to avoid rate limits
        except Exception as e:
            print(f"Error sending message: {e}")
            break
    
    active_spams.pop(chat_id, None)

# Big spam command handler
async def bspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /bspam <count (999-999999)> <message>")
        return
    
    try:
        count = int(context.args[0])
        if count < 999 or count > 999999:
            await update.message.reply_text("Count must be between 999 and 999999")
            return
    except ValueError:
        await update.message.reply_text("Count must be a number")
        return
    
    message = ' '.join(context.args[1:])
    chat_id = update.message.chat_id
    
    active_spams[chat_id] = True
    
    for i in range(count):
        if not active_spams.get(chat_id, False):
            break
        
        bot = get_available_bot()
        if not bot:
            await update.message.reply_text("No available bots at the moment")
            break
        
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            await asyncio.sleep(0.3)  # Smaller delay for bigger spam
        except Exception as e:
            print(f"Error sending message: {e}")
            continue
    
    active_spams.pop(chat_id, None)

# Unlimited spam command handler
async def uspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /uspam <message>")
        return
    
    message = ' '.join(context.args)
    chat_id = update.message.chat_id
    
    active_uspams[chat_id] = True
    
    await update.message.reply_text("Unlimited spam started! Use /stop to stop.")
    
    while active_uspams.get(chat_id, False):
        bot = get_available_bot()
        if not bot:
            await update.message.reply_text("No available bots at the moment")
            break
        
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            await asyncio.sleep(0.2)  # Very small delay for unlimited spam
        except Exception as e:
            print(f"Error sending message: {e}")
            continue

# Stop command handler
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in active_spams:
        active_spams.pop(chat_id)
    if chat_id in active_uspams:
        active_uspams.pop(chat_id)
    await update.message.reply_text("All spam activities stopped!")

# Raid command handler
async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /raid <count> <@username>")
        return
    
    try:
        count = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Count must be a number")
        return
    
    username = context.args[1]
    if not username.startswith('@'):
        await update.message.reply_text("Username must start with @")
        return
    
    chat_id = update.message.chat_id
    active_spams[chat_id] = True
    
    for i in range(count):
        if not active_spams.get(chat_id, False):
            break
        
        bot = get_available_bot()
        if not bot:
            await update.message.reply_text("No available bots at the moment")
            break
        
        message = random.choice(raid_messages)
        try:
            await bot.send_message(chat_id=chat_id, text=f"{username} {message}")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error sending raid message: {e}")
            continue
    
    active_spams.pop(chat_id, None)

# Shayari raid command handler
async def sraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /sraid <count> <@username>")
        return
    
    try:
        count = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Count must be a number")
        return
    
    username = context.args[1]
    if not username.startswith('@'):
        await update.message.reply_text("Username must start with @")
        return
    
    chat_id = update.message.chat_id
    active_spams[chat_id] = True
    
    for i in range(count):
        if not active_spams.get(chat_id, False):
            break
        
        bot = get_available_bot()
        if not bot:
            await update.message.reply_text("No available bots at the moment")
            break
        
        message = random.choice(shayari_messages)
        try:
            await bot.send_message(chat_id=chat_id, text=f"{username} {message}")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error sending shayari raid message: {e}")
            continue
    
    active_spams.pop(chat_id, None)

# Help command handler
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    Available Commands:
    
    /start - Start the bot
    /spam <count (1-999)> <message> - Send limited spam
    /bspam <count (999-999999)> <message> - Send big spam
    /uspam <message> - Unlimited spam (use /stop to stop)
    /raid <count> <@username> - Raid a user
    /sraid <count> <@username> - Shayari raid a user
    /stop - Stop all spam activities
    /alive - Check bot status
    /help - Show this help message
    """
    await update.message.reply_text(help_text)

# Alive command handler
async def alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    bot_count = len(bots)
    active_bots = sum(1 for bot in bots.values() if bot['available'])
    
    alive_message = f"""
    🚀 Bot is alive and kicking! 🚀
    
    📊 System Stats:
    CPU Usage: {cpu_usage}%
    RAM Usage: {ram_usage}%
    
    🤖 Bot Status:
    Total Bots: {bot_count}
    Active Bots: {active_bots}
    
    🌟 Powered by Multi-Token Spam Bot
    """
    await update.message.reply_text(alive_message)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
    Welcome to the Multi-Token Spam Bot!
    
    Use /help to see all available commands.
    
    Features:
    - Multiple bot token support
    - Various spam modes
    - Raid capabilities
    """)

def main():
    # Load configuration
    bot_tokens = load_config()
    
    if not bot_tokens:
        print("No bot tokens configured. Please add your bot tokens to the script.")
        sys.exit(1)
    
    # Initialize bots
    asyncio.run(initialize_bots(bot_tokens))
    
    # Create application for the first bot (others will be used as workers)
    application = Application.builder().token(bot_tokens[0]).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("spam", spam))
    application.add_handler(CommandHandler("bspam", bspam))
    application.add_handler(CommandHandler("uspam", uspam))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("raid", raid))
    application.add_handler(CommandHandler("sraid", sraid))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("alive", alive))
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
