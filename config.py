import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/tea_bot.db")
DEFAULT_REMINDER_TIME = "20:00"
TIMEZONE = os.getenv("TIMEZONE", "Asia/Almaty")
