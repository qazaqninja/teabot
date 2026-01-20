import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional
from contextlib import contextmanager

from config import DATABASE_PATH, DEFAULT_REMINDER_TIME
from models import User, DailyProgress


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                reminder_time TEXT DEFAULT '20:00',
                is_admin INTEGER DEFAULT 0,
                can_dm INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS daily_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                quran_pages INTEGER DEFAULT 0,
                salawat_count INTEGER DEFAULT 0,
                tahajjud INTEGER DEFAULT 0,
                book_pages INTEGER DEFAULT 0,
                fasted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        # Migration: add can_dm column if not exists
        try:
            conn.execute("ALTER TABLE users ADD COLUMN can_dm INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.commit()


def create_user(telegram_id: int, username: Optional[str] = None, is_admin: bool = False, can_dm: bool = False) -> User:
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO users (telegram_id, username, reminder_time, is_admin, can_dm)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET
                   username = excluded.username,
                   can_dm = CASE WHEN excluded.can_dm = 1 THEN 1 ELSE users.can_dm END
               RETURNING *""",
            (telegram_id, username, DEFAULT_REMINDER_TIME, int(is_admin), int(can_dm))
        )
        row = cursor.fetchone()
        conn.commit()
        return _row_to_user(row)


def set_can_dm(telegram_id: int, can_dm: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET can_dm = ? WHERE telegram_id = ?",
            (int(can_dm), telegram_id)
        )
        conn.commit()


def get_users_for_reminders() -> list[User]:
    """Get users who can receive DM reminders."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM users WHERE can_dm = 1")
        return [_row_to_user(row) for row in cursor.fetchall()]


def get_user(telegram_id: int) -> Optional[User]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = cursor.fetchone()
        return _row_to_user(row) if row else None


def get_all_users() -> list[User]:
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM users")
        return [_row_to_user(row) for row in cursor.fetchall()]


def update_reminder_time(telegram_id: int, time: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET reminder_time = ? WHERE telegram_id = ?",
            (time, telegram_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def save_progress(
    user_id: int,
    progress_date: date,
    quran_pages: int,
    salawat_count: int,
    tahajjud: bool,
    book_pages: int,
    fasted: bool
) -> DailyProgress:
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO daily_progress
               (user_id, date, quran_pages, salawat_count, tahajjud, book_pages, fasted)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, date) DO UPDATE SET
                   quran_pages = excluded.quran_pages,
                   salawat_count = excluded.salawat_count,
                   tahajjud = excluded.tahajjud,
                   book_pages = excluded.book_pages,
                   fasted = excluded.fasted
               RETURNING *""",
            (user_id, progress_date.isoformat(), quran_pages, salawat_count, int(tahajjud), book_pages, int(fasted))
        )
        row = cursor.fetchone()
        conn.commit()
        return _row_to_progress(row)


def get_today_progress(user_id: int) -> Optional[DailyProgress]:
    today = date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM daily_progress WHERE user_id = ? AND date = ?",
            (user_id, today)
        )
        row = cursor.fetchone()
        return _row_to_progress(row) if row else None


def get_weekly_stats(user_id: int) -> dict:
    today = date.today()
    week_ago = today - timedelta(days=7)

    with get_connection() as conn:
        cursor = conn.execute(
            """SELECT
                SUM(quran_pages) as total_quran,
                SUM(salawat_count) as total_salawat,
                SUM(tahajjud) as total_tahajjud,
                SUM(book_pages) as total_book,
                SUM(fasted) as total_fasted,
                COUNT(*) as days_logged
               FROM daily_progress
               WHERE user_id = ? AND date >= ?""",
            (user_id, week_ago.isoformat())
        )
        row = cursor.fetchone()
        return {
            "quran_pages": row["total_quran"] or 0,
            "salawat_count": row["total_salawat"] or 0,
            "tahajjud_days": row["total_tahajjud"] or 0,
            "book_pages": row["total_book"] or 0,
            "fasting_days": row["total_fasted"] or 0,
            "days_logged": row["days_logged"] or 0
        }


def get_monthly_stats(user_id: int) -> dict:
    today = date.today()
    month_ago = today - timedelta(days=30)

    with get_connection() as conn:
        cursor = conn.execute(
            """SELECT
                SUM(quran_pages) as total_quran,
                SUM(salawat_count) as total_salawat,
                SUM(tahajjud) as total_tahajjud,
                SUM(book_pages) as total_book,
                SUM(fasted) as total_fasted,
                COUNT(*) as days_logged
               FROM daily_progress
               WHERE user_id = ? AND date >= ?""",
            (user_id, month_ago.isoformat())
        )
        row = cursor.fetchone()
        return {
            "quran_pages": row["total_quran"] or 0,
            "salawat_count": row["total_salawat"] or 0,
            "tahajjud_days": row["total_tahajjud"] or 0,
            "book_pages": row["total_book"] or 0,
            "fasting_days": row["total_fasted"] or 0,
            "days_logged": row["days_logged"] or 0
        }


def get_all_users_weekly_stats() -> list[dict]:
    """Get weekly stats for all users (for admin view)."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    with get_connection() as conn:
        cursor = conn.execute(
            """SELECT
                u.id,
                u.username,
                u.telegram_id,
                COALESCE(SUM(p.quran_pages), 0) as total_quran,
                COALESCE(SUM(p.salawat_count), 0) as total_salawat,
                COALESCE(SUM(p.tahajjud), 0) as total_tahajjud,
                COALESCE(SUM(p.book_pages), 0) as total_book,
                COALESCE(SUM(p.fasted), 0) as total_fasted,
                COUNT(p.id) as days_logged
               FROM users u
               LEFT JOIN daily_progress p ON u.id = p.user_id AND p.date >= ?
               GROUP BY u.id
               ORDER BY total_quran DESC""",
            (week_ago.isoformat(),)
        )
        return [
            {
                "user_id": row["id"],
                "username": row["username"] or f"User_{row['telegram_id']}",
                "quran_pages": row["total_quran"],
                "salawat_count": row["total_salawat"],
                "tahajjud_days": row["total_tahajjud"],
                "book_pages": row["total_book"],
                "fasting_days": row["total_fasted"],
                "days_logged": row["days_logged"]
            }
            for row in cursor.fetchall()
        ]


def get_today_all_progress() -> list[dict]:
    """Get today's progress for all users (for admin view)."""
    today = date.today().isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """SELECT
                u.username,
                u.telegram_id,
                p.quran_pages,
                p.salawat_count,
                p.tahajjud,
                p.book_pages,
                p.fasted
               FROM users u
               LEFT JOIN daily_progress p ON u.id = p.user_id AND p.date = ?
               ORDER BY u.username""",
            (today,)
        )
        return [
            {
                "username": row["username"] or f"User_{row['telegram_id']}",
                "quran_pages": row["quran_pages"],
                "salawat_count": row["salawat_count"],
                "tahajjud": bool(row["tahajjud"]) if row["tahajjud"] is not None else None,
                "book_pages": row["book_pages"],
                "fasted": bool(row["fasted"]) if row["fasted"] is not None else None,
                "logged": row["quran_pages"] is not None
            }
            for row in cursor.fetchall()
        ]


def get_setting(key: str) -> Optional[str]:
    with get_connection() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value)
        )
        conn.commit()


def _row_to_user(row) -> User:
    return User(
        id=row["id"],
        telegram_id=row["telegram_id"],
        username=row["username"],
        reminder_time=row["reminder_time"],
        is_admin=bool(row["is_admin"]),
        can_dm=bool(row["can_dm"]) if "can_dm" in row.keys() else False,
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
    )


def _row_to_progress(row) -> DailyProgress:
    return DailyProgress(
        id=row["id"],
        user_id=row["user_id"],
        date=date.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"],
        quran_pages=row["quran_pages"],
        salawat_count=row["salawat_count"],
        tahajjud=bool(row["tahajjud"]),
        book_pages=row["book_pages"],
        fasted=bool(row["fasted"]),
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
    )
