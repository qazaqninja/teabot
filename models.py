from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    reminder_time: str
    is_admin: bool
    can_dm: bool
    created_at: datetime


@dataclass
class DailyProgress:
    id: int
    user_id: int
    date: date
    quran_pages: int
    salawat_count: int
    tahajjud: bool
    book_pages: int
    fasted: bool
    created_at: datetime
