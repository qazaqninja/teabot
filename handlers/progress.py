from datetime import date
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import database as db

# Conversation states
QURAN, SALAWAT, TAHAJJUD, BOOK, FASTING = range(5)


async def start_logging(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the progress logging conversation."""
    user = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Алдымен /start басыңыз.")
        return ConversationHandler.END

    context.user_data["db_user_id"] = db_user.id
    context.user_data["progress"] = {}

    await update.message.reply_text(
        "Ассаламу алейкум! Күнделікті прогресс уақыты.\n\n"
        "1️⃣ Бүгін Құран неше бет оқыдыңыз?\n"
        "(Сан жазыңыз, немесе 0)"
    )
    return QURAN


async def receive_quran(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive Quran pages count."""
    try:
        pages = int(update.message.text.strip())
        if pages < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Дұрыс сан жазыңыз (0 немесе одан көп).")
        return QURAN

    context.user_data["progress"]["quran_pages"] = pages

    await update.message.reply_text(
        "2️⃣ Неше салауат айттыңыз?\n"
        "(Сан жазыңыз, немесе 0)"
    )
    return SALAWAT


async def receive_salawat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive salawat count."""
    try:
        count = int(update.message.text.strip())
        if count < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Дұрыс сан жазыңыз (0 немесе одан көп).")
        return SALAWAT

    context.user_data["progress"]["salawat_count"] = count

    await update.message.reply_text(
        "3️⃣ Тахажжуд намазын оқыдыңыз ба?\n"
        "(иә/жоқ)"
    )
    return TAHAJJUD


async def receive_tahajjud(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive tahajjud answer."""
    text = update.message.text.strip().lower()

    if text in ("yes", "y", "да", "1", "ha", "иә", "ия", "әрине"):
        context.user_data["progress"]["tahajjud"] = True
    elif text in ("no", "n", "нет", "0", "yoq", "жоқ", "жок"):
        context.user_data["progress"]["tahajjud"] = False
    else:
        await update.message.reply_text("Иә немесе жоқ деп жауап беріңіз.")
        return TAHAJJUD

    book_name = db.get_setting("current_book") or "таңдалған кітап"

    await update.message.reply_text(
        f"4️⃣ \"{book_name}\" кітабынан неше бет оқыдыңыз?\n"
        "(Сан жазыңыз, немесе 0)"
    )
    return BOOK


async def receive_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive book pages count."""
    try:
        pages = int(update.message.text.strip())
        if pages < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Дұрыс сан жазыңыз (0 немесе одан көп).")
        return BOOK

    context.user_data["progress"]["book_pages"] = pages

    await update.message.reply_text(
        "5️⃣ Бүгін ораза тұттыңыз ба?\n"
        "(иә/жоқ)"
    )
    return FASTING


async def receive_fasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive fasting answer and save progress."""
    text = update.message.text.strip().lower()

    if text in ("yes", "y", "да", "1", "ha", "иә", "ия", "әрине"):
        fasted = True
    elif text in ("no", "n", "нет", "0", "yoq", "жоқ", "жок"):
        fasted = False
    else:
        await update.message.reply_text("Иә немесе жоқ деп жауап беріңіз.")
        return FASTING

    progress = context.user_data["progress"]
    user_id = context.user_data["db_user_id"]

    # Save to database
    db.save_progress(
        user_id=user_id,
        progress_date=date.today(),
        quran_pages=progress["quran_pages"],
        salawat_count=progress["salawat_count"],
        tahajjud=progress["tahajjud"],
        book_pages=progress["book_pages"],
        fasted=fasted
    )

    # Build summary
    tahajjud_symbol = "✓" if progress["tahajjud"] else "✗"
    fasted_symbol = "✓" if fasted else "✗"
    book_name = db.get_setting("current_book") or "Кітап"

    await update.message.reply_text(
        "✅ Жазылды! Жазақаллаһу хайыр.\n\n"
        f"Бүгінгі қорытынды:\n"
        f"Құран: {progress['quran_pages']}б | "
        f"Салауат: {progress['salawat_count']} | "
        f"Тахажжуд: {tahajjud_symbol} | "
        f"{book_name}: {progress['book_pages']}б | "
        f"Ораза: {fasted_symbol}"
    )

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Прогресс жазу тоқтатылды. Қайта бастау үшін /log басыңыз."
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_progress_handler() -> ConversationHandler:
    """Return the conversation handler for progress logging."""
    return ConversationHandler(
        entry_points=[CommandHandler("log", start_logging)],
        states={
            QURAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quran)],
            SALAWAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_salawat)],
            TAHAJJUD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tahajjud)],
            BOOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_book)],
            FASTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_fasting)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
