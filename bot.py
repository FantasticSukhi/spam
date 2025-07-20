import asyncio
import random
import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import psutil
from config import (
    BOT_TOKENS, OWNER_ID, SUDO_USERS,
    CHANNEL_LINK, GROUP_LINK, SUPPORT_CHAT,
    MIN_SPAM, MAX_SPAM, MIN_BSPAM, MAX_BSPAM,
    SPAM_DELAY, BSPAM_DELAY, USPAM_DELAY, RAID_DELAY,
    RAID_FILE, SHAYARI_FILE, MAX_THREADS
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables
active_spams = {}
active_uspams = {}
raid_messages = []
shayari_messages = []
bots = []
current_bot_index = 0
applications = []

def is_sudo(user_id: int) -> bool:
    """Check if user is sudo or owner"""
    return user_id == OWNER_ID or user_id in SUDO_USERS

async def check_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is authorized"""
    user_id = update.effective_user.id
    if not is_sudo(user_id):
        await update.message.reply_text("🚫 You are not authorized to use this command!")
        return False
    return True

async def initialize_bots():
    """Initialize all bot instances"""
    global bots
    bots = []
    for token in BOT_TOKENS:
        try:
            bot = Bot(token)
            me = await bot.get_me()
            bot_info = {
                'instance': bot,
                'username': me.username,
                'available': True,
                'token': token
            }
            bots.append(bot_info)
            logger.info(f"Bot @{me.username} initialized successfully!")
        except Exception as e:
            logger.error(f"Failed to initialize bot with token {token[:10]}...: {e}")
    
    if not bots:
        logger.error("No bots initialized successfully!")
        return False
    return True

def get_available_bot():
    """Get an available bot instance with round-robin"""
    global current_bot_index
    
    if not bots:
        return None
    
    # Try to find an available bot
    for _ in range(len(bots)):
        current_bot_index = (current_bot_index + 1) % len(bots)
        if bots[current_bot_index]['available']:
            return bots[current_bot_index]['instance']
    
    return None

async def create_applications():
    """Create applications for all bots"""
    global applications
    applications = []
    for token in BOT_TOKENS:
        try:
            application = Application.builder().token(token).build()
            applications.append(application)
            logger.info(f"Created application for token {token[:10]}...")
        except Exception as e:
            logger.error(f"Failed to create application for token {token[:10]}...: {e}")
    return applications

def load_messages():
    """Load raid and shayari messages from files"""
    global raid_messages, shayari_messages
    try:
        with open(RAID_FILE, 'r', encoding='utf-8') as f:
            raid_messages = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(raid_messages)} raid messages")
    except FileNotFoundError:
        raid_messages = ["Default raid message 1", "Default raid message 2"]
        logger.warning("raid.txt not found, using default messages")
    
    try:
        with open(SHAYARI_FILE, 'r', encoding='utf-8') as f:
            shayari_messages = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(shayari_messages)} shayari messages")
    except FileNotFoundError:
        shayari_messages = ["Default shayari 1", "Default shayari 2"]
        logger.warning("shayari.txt not found, using default messages")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    start_message = f"""
    🚀 *Welcome to Multi-Token Spam Bot* 🚀
    
    *Owner:* [Click Here](tg://user?id={OWNER_ID})
    *Channel:* [Join Here]({CHANNEL_LINK})
    *Group:* [Join Here]({GROUP_LINK})
    *Support:* [Get Help]({SUPPORT_CHAT})
    
    Use /help to see all available commands.
    """
    await update.message.reply_text(
        text=start_message,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /spam command"""
    if not await check_sudo(update, context):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /spam <count (1-999)> <message>")
        return
    
    try:
        count = int(context.args[0])
        if count < MIN_SPAM or count > MAX_SPAM:
            await update.message.reply_text(f"Count must be between {MIN_SPAM} and {MAX_SPAM}")
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
            await asyncio.sleep(SPAM_DELAY)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            continue
    
    active_spams.pop(chat_id, None)

async def bspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bspam command"""
    if not await check_sudo(update, context):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(f"Usage: /bspam <count ({MIN_BSPAM}-{MAX_BSPAM})> <message>")
        return
    
    try:
        count = int(context.args[0])
        if count < MIN_BSPAM or count > MAX_BSPAM:
            await update.message.reply_text(f"Count must be between {MIN_BSPAM} and {MAX_BSPAM}")
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
            await asyncio.sleep(BSPAM_DELAY)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            continue
    
    active_spams.pop(chat_id, None)

async def uspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /uspam command"""
    if not await check_sudo(update, context):
        return
    
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
            await asyncio.sleep(USPAM_DELAY)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            continue

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    chat_id = update.message.chat_id
    if chat_id in active_spams:
        active_spams.pop(chat_id)
    if chat_id in active_uspams:
        active_uspams.pop(chat_id)
    await update.message.reply_text("All spam activities stopped!")

async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /raid command"""
    if not await check_sudo(update, context):
        return
    
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
            await asyncio.sleep(RAID_DELAY)
        except Exception as e:
            logger.error(f"Error sending raid message: {e}")
            continue
    
    active_spams.pop(chat_id, None)

async def sraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sraid command"""
    if not await check_sudo(update, context):
        return
    
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
            await asyncio.sleep(RAID_DELAY)
        except Exception as e:
            logger.error(f"Error sending shayari raid message: {e}")
            continue
    
    active_spams.pop(chat_id, None)

async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a sudo user (Owner only)"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the owner can add sudo users!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /addsudo <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in SUDO_USERS:
            await update.message.reply_text("⚠️ This user is already a sudo user!")
            return
            
        SUDO_USERS.append(user_id)
        await update.message.reply_text(f"✅ User {user_id} added to sudo users!")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def removesudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a sudo user (Owner only)"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the owner can remove sudo users!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /removesudo <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id not in SUDO_USERS:
            await update.message.reply_text("⚠️ This user is not a sudo user!")
            return
            
        SUDO_USERS.remove(user_id)
        await update.message.reply_text(f"✅ User {user_id} removed from sudo users!")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all sudo users"""
    if not await check_sudo(update, context):
        return
    
    sudo_list = "\n".join([f"• {user_id}" for user_id in SUDO_USERS])
    message = f"""
    👑 *Sudo Users List* 👑
    
    *Owner ID:* {OWNER_ID}
    
    *Sudo Users:*
    {sudo_list}
    
    Total: {len(SUDO_USERS)} sudo users
    """
    await update.message.reply_text(
        text=message,
        parse_mode="Markdown"
    )

async def alive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alive command"""
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    bot_count = len(bots)
    active_bots = sum(1 for bot in bots if bot['available'])
    
    alive_message = f"""
    🚀 *Bot is alive and kicking!* 🚀
    
    📊 *System Stats:*
    • CPU Usage: {cpu_usage}%
    • RAM Usage: {ram_usage}%
    
    🤖 *Bot Status:*
    • Total Bots: {bot_count}
    • Active Bots: {active_bots}
    
    👤 *Owner:* [Click Here](tg://user?id={OWNER_ID})
    📢 *Channel:* [Join Here]({CHANNEL_LINK})
    👥 *Group:* [Join Here]({GROUP_LINK})
    """
    await update.message.reply_text(
        text=alive_message,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = f"""
    📜 *Available Commands* 📜
    
    */start* - Start the bot
    */spam* <count> <msg> - Send limited spam (1-999)
    */bspam* <count> <msg> - Send big spam (999-999999)
    */uspam* <msg> - Unlimited spam (/stop to stop)
    */raid* <count> @user - Raid a user
    */sraid* <count> @user - Shayari raid
    
    👑 *Admin Commands:*
    */addsudo* <user_id> - Add sudo user (Owner)
    */removesudo* <user_id> - Remove sudo user (Owner)
    */sudolist* - List sudo users
    
    *Support Links:*
    👤 [Owner](tg://user?id={OWNER_ID})
    📢 [Channel]({CHANNEL_LINK})
    👥 [Group]({GROUP_LINK})
    💬 [Support]({SUPPORT_CHAT})
    """
    await update.message.reply_text(
        text=help_text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def register_handlers(application):
    """Register command handlers for an application"""
    commands = [
        ("start", start),
        ("spam", spam),
        ("bspam", bspam),
        ("uspam", uspam),
        ("stop", stop),
        ("raid", raid),
        ("sraid", sraid),
        ("alive", alive),
        ("help", help_cmd),
        ("addsudo", addsudo),
        ("removesudo", removesudo),
        ("sudolist", sudolist)
    ]
    
    for cmd, handler in commands:
        application.add_handler(CommandHandler(cmd, handler))

async def main():
    """Main function to start the bot"""
    # Load messages first
    load_messages()
    
    # Initialize all bots
    if not await initialize_bots():
        logger.error("Failed to initialize any bots. Exiting.")
        return
    
    # Create applications for all bots
    apps = await create_applications()
    if not apps:
        logger.error("Failed to create any applications. Exiting.")
        return
    
    # Register handlers for each application
    for app in apps:
        await register_handlers(app)
    
    # Start all applications
    for app in apps:
        await app.initialize()
        await app.start()
        if hasattr(app, 'updater'):
            await app.updater.start_polling()
    
    logger.info(f"All {len(apps)} bots are running...")
    
    # Keep the applications running
    while True:
        await asyncio.sleep(3600)  # Sleep for 1 hour

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("\nBots stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        loop.close()
