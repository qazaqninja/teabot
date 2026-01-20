from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

import database as db
from config import TIMEZONE


class ReminderScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=ZoneInfo(TIMEZONE))
        self._scheduled_users: set[str] = set()

    def start(self):
        """Start the scheduler and schedule initial jobs."""
        # Run check every minute to handle user-specific times
        self.scheduler.add_job(
            self._check_and_send_reminders,
            CronTrigger(minute="*"),
            id="reminder_check",
            replace_existing=True
        )
        self.scheduler.start()

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()

    async def _check_and_send_reminders(self):
        """Check if any users should receive reminders at current time."""
        now = datetime.now(ZoneInfo(TIMEZONE))
        current_time = now.strftime("%H:%M")
        today_str = now.date().isoformat()

        # Clean old entries at the start of each check
        self._scheduled_users = {
            k for k in self._scheduled_users
            if today_str in k
        }

        # Only get users who can receive DMs
        users = db.get_users_for_reminders()

        for user in users:
            if user.reminder_time == current_time:
                # Check if already reminded today
                today_key = f"{user.telegram_id}_{today_str}"
                if today_key in self._scheduled_users:
                    continue

                self._scheduled_users.add(today_key)
                await self._send_reminder(user.telegram_id)

    async def _send_reminder(self, telegram_id: int):
        """Send a reminder to a specific user."""
        book_name = db.get_setting("current_book") or "таңдалған кітап"

        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=(
                    "Ассаламу алейкум! Күнделікті прогресс уақыты келді.\n\n"
                    "Прогресті жазу үшін /log басыңыз:\n"
                    "- Құран беттері\n"
                    "- Салауат саны\n"
                    "- Тахажжуд намазы\n"
                    f"- \"{book_name}\" беттері\n"
                    "- Ораза"
                )
            )
        except Exception as e:
            print(f"Failed to send reminder to {telegram_id}: {e}")
            # Mark user as unable to receive DMs
            db.set_can_dm(telegram_id, False)

    async def send_reminder_to_user(self, telegram_id: int):
        """Manually trigger a reminder for testing."""
        await self._send_reminder(telegram_id)
