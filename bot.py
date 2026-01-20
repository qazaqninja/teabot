import logging
from telegram.ext import Application, CommandHandler

import database as db
from config import BOT_TOKEN
from handlers.commands import start, today, stats, settime
from handlers.progress import get_progress_handler
from handlers.admin import setbook, broadcast, makeadmin, results, weekly
from scheduler import ReminderScheduler

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    # Initialize database
    db.init_db()
    logger.info("Database initialized")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("settime", settime))
    application.add_handler(CommandHandler("setbook", setbook))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("makeadmin", makeadmin))
    application.add_handler(CommandHandler("results", results))
    application.add_handler(CommandHandler("weekly", weekly))

    # Add conversation handler for progress logging
    application.add_handler(get_progress_handler())

    # Set up scheduler
    scheduler = ReminderScheduler(application.bot)

    # Start scheduler when bot starts
    async def post_init(app):
        scheduler.start()
        logger.info("Scheduler started")

    # Stop scheduler when bot stops
    async def post_shutdown(app):
        scheduler.stop()
        logger.info("Scheduler stopped")

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    # Run the bot
    logger.info("Starting bot...")
    application.run_polling()


if __name__ == "__main__":
    main()
