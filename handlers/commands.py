from telegram import Update
from telegram.ext import ContextTypes

import database as db


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat

    # Check if this is a private chat (DM)
    is_private = chat.type == "private"

    db_user = db.create_user(
        telegram_id=user.id,
        username=user.username,
        can_dm=is_private
    )

    if is_private:
        await update.message.reply_text(
            f"Ассаламу алейкум, {user.first_name}!\n\n"
            "Прогресс трекер ботына қош келдіңіз.\n\n"
            "Мен сізге күнделікті еске салу жіберемін:\n"
            "- Құран оқылған беттер\n"
            "- Салауат саны\n"
            "- Тахажжуд намазы\n"
            "- Кітап оқылған беттер\n"
            "- Ораза\n\n"
            f"Еске салу уақыты: {db_user.reminder_time}\n"
            "Өзгерту үшін: /settime HH:MM\n\n"
            "Командалар:\n"
            "/today - Бүгінгі прогресс\n"
            "/stats - Апталық/айлық есеп\n"
            "/log - Прогресті жазу"
        )
    else:
        # In group chat - remind to start private chat
        await update.message.reply_text(
            f"Ассаламу алейкум, {user.first_name}!\n\n"
            "Күнделікті еске салу алу үшін маған жеке хат жазыңыз.\n"
            "Жеке чатта /start басыңыз."
        )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Алдымен /start басыңыз.")
        return

    progress = db.get_today_progress(db_user.id)
    book_name = db.get_setting("current_book") or "Кітап таңдалмаған"

    if not progress:
        await update.message.reply_text(
            "Бүгін әлі прогресс жазылмаған.\n"
            "Жазу үшін /log басыңыз."
        )
        return

    tahajjud_symbol = "✓" if progress.tahajjud else "✗"
    fasted_symbol = "✓" if progress.fasted else "✗"

    await update.message.reply_text(
        f"📊 Бүгінгі прогресс:\n\n"
        f"Құран: {progress.quran_pages} бет\n"
        f"Салауат: {progress.salawat_count}\n"
        f"Тахажжуд: {tahajjud_symbol}\n"
        f"Кітап ({book_name}): {progress.book_pages} бет\n"
        f"Ораза: {fasted_symbol}"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Алдымен /start басыңыз.")
        return

    weekly = db.get_weekly_stats(db_user.id)
    monthly = db.get_monthly_stats(db_user.id)

    await update.message.reply_text(
        f"📊 Сіздің статистика\n\n"
        f"═══ Соңғы 7 күн ═══\n"
        f"Құран: {weekly['quran_pages']} бет\n"
        f"Салауат: {weekly['salawat_count']}\n"
        f"Тахажжуд: {weekly['tahajjud_days']} күн\n"
        f"Кітап: {weekly['book_pages']} бет\n"
        f"Ораза: {weekly['fasting_days']} күн\n"
        f"Жазылған күндер: {weekly['days_logged']}/7\n\n"
        f"═══ Соңғы 30 күн ═══\n"
        f"Құран: {monthly['quran_pages']} бет\n"
        f"Салауат: {monthly['salawat_count']}\n"
        f"Тахажжуд: {monthly['tahajjud_days']} күн\n"
        f"Кітап: {monthly['book_pages']} бет\n"
        f"Ораза: {monthly['fasting_days']} күн\n"
        f"Жазылған күндер: {monthly['days_logged']}/30"
    )


async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Алдымен /start басыңыз.")
        return

    if not context.args:
        await update.message.reply_text(
            f"Қазіргі еске салу уақыты: {db_user.reminder_time}\n\n"
            "Қолдану: /settime HH:MM\n"
            "Мысалы: /settime 21:00"
        )
        return

    time_str = context.args[0]

    # Validate time format
    try:
        hours, minutes = time_str.split(":")
        hours = int(hours)
        minutes = int(minutes)
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError()
        time_str = f"{hours:02d}:{minutes:02d}"
    except (ValueError, AttributeError):
        await update.message.reply_text(
            "Қате формат. HH:MM форматын қолданыңыз.\n"
            "Мысалы: /settime 21:00"
        )
        return

    db.update_reminder_time(user.id, time_str)
    await update.message.reply_text(f"Еске салу уақыты өзгертілді: {time_str}")
