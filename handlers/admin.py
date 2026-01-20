from telegram import Update
from telegram.ext import ContextTypes

import database as db


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View today's progress for all users."""
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Алдымен /start басыңыз.")
        return

    all_progress = db.get_today_all_progress()

    if not all_progress:
        await update.message.reply_text("Әлі ешкім тіркелмеген.")
        return

    lines = ["📊 Бүгінгі прогресс (барлық қатысушылар)\n"]

    for p in all_progress:
        if p["logged"]:
            tahajjud = "✓" if p["tahajjud"] else "✗"
            fasted = "✓" if p["fasted"] else "✗"
            lines.append(
                f"@{p['username']}:\n"
                f"  Құран: {p['quran_pages']}б | Салауат: {p['salawat_count']}\n"
                f"  Тахажжуд: {tahajjud} | Кітап: {p['book_pages']}б | Ораза: {fasted}"
            )
        else:
            lines.append(f"@{p['username']}: ⏳ Әлі жазылмаған")

    await update.message.reply_text("\n".join(lines))


async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View weekly stats for all users."""
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Алдымен /start басыңыз.")
        return

    all_stats = db.get_all_users_weekly_stats()

    if not all_stats:
        await update.message.reply_text("Әлі ешкім тіркелмеген.")
        return

    lines = ["📊 Апталық есеп (соңғы 7 күн)\n"]

    for s in all_stats:
        lines.append(
            f"@{s['username']} ({s['days_logged']}/7 күн):\n"
            f"  Құран: {s['quran_pages']}б | Салауат: {s['salawat_count']}\n"
            f"  Тахажжуд: {s['tahajjud_days']}к | Кітап: {s['book_pages']}б | Ораза: {s['fasting_days']}к"
        )

    await update.message.reply_text("\n".join(lines))


async def setbook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the current book for all users (admin only)."""
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user or not db_user.is_admin:
        await update.message.reply_text("Бұл команда тек админдерге қолжетімді.")
        return

    if not context.args:
        current_book = db.get_setting("current_book")
        if current_book:
            await update.message.reply_text(
                f"Қазіргі кітап: {current_book}\n\n"
                "Қолдану: /setbook Кітап атауы"
            )
        else:
            await update.message.reply_text(
                "Кітап әлі таңдалмаған.\n\n"
                "Қолдану: /setbook Кітап атауы"
            )
        return

    book_name = " ".join(context.args)
    db.set_setting("current_book", book_name)

    await update.message.reply_text(f"Кітап орнатылды: {book_name}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to all users (admin only)."""
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user or not db_user.is_admin:
        await update.message.reply_text("Бұл команда тек админдерге қолжетімді.")
        return

    if not context.args:
        await update.message.reply_text("Қолдану: /broadcast Хабарлама мәтіні")
        return

    message = " ".join(context.args)
    users = db.get_all_users()

    sent_count = 0
    failed_count = 0

    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u.telegram_id,
                text=f"📢 Хабарлама:\n\n{message}"
            )
            sent_count += 1
        except Exception:
            failed_count += 1

    await update.message.reply_text(
        f"Хабарлама жіберілді.\n"
        f"Жеткізілді: {sent_count}\n"
        f"Қате: {failed_count}"
    )


async def makeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Make a user an admin (must reply to their message or use their ID)."""
    user = update.effective_user
    db_user = db.get_user(user.id)

    # First user becomes admin automatically
    users = db.get_all_users()
    if len(users) == 1 and users[0].telegram_id == user.id:
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE users SET is_admin = 1 WHERE telegram_id = ?",
                (user.id,)
            )
            conn.commit()
        await update.message.reply_text("Сіз енді админсіз (бірінші қатысушы құқығы).")
        return

    if not db_user or not db_user.is_admin:
        await update.message.reply_text("Бұл команда тек админдерге қолжетімді.")
        return

    # Check if replying to a message
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
    elif context.args:
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Дұрыс қатысушы ID жазыңыз.")
            return
    else:
        await update.message.reply_text(
            "Қолдану: Қатысушы хабарына жауап ретінде /makeadmin\n"
            "Немесе: /makeadmin USER_ID"
        )
        return

    target_db_user = db.get_user(target_id)
    if not target_db_user:
        await update.message.reply_text("Қатысушы табылмады. Алдымен ол /start басуы керек.")
        return

    with db.get_connection() as conn:
        conn.execute(
            "UPDATE users SET is_admin = 1 WHERE telegram_id = ?",
            (target_id,)
        )
        conn.commit()

    await update.message.reply_text(f"Қатысушы {target_id} енді админ.")
