# Bot Configuration
BOT_TOKENS = [
    "7747234167:AAGsuZlyXZwIarywwFyKcHPFVEYfBY7xcpk",
    "8161769845:AAF2QYkJFcKTreGJF7keex64uVdapVU5muc"
]

# Admin Configuration
OWNER_ID = 7448520005  # Your Telegram ID
SUDO_USERS = [7448520005]  # Additional admin IDs

# Spam limits
MIN_SPAM = 1
MAX_SPAM = 999
MIN_BSPAM = 999
MAX_BSPAM = 999999

# Delay settings (in seconds)
SPAM_DELAY = 0.5
BSPAM_DELAY = 0.3
USPAM_DELAY = 0.2
RAID_DELAY = 0.5

# File paths
RAID_FILE = "raid.txt"
SHAYARI_FILE = "shayari.txt"

# Or if you want logs in your project directory:
LOG_FILE = "logs/spambot.log"  # Relative path (create logs directory first)

MAX_THREADS = 50  # Maximum concurrent threads
