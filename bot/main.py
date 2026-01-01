import os
import logging
import random
import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from bot.db import init_db, AsyncSessionLocal, User
from bot.texts import PHRASES
from sqlalchemy.future import select
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# UI texts for the interface (to avoid cluttering PHRASES)
UI_TEXTS = {
    "ru": {
        "welcome": "Добро пожаловать в Lifery! 👋\n\nПожалуйста, введите дату рождения в формате ДД.ММ.ГГГГ",
        "invalid_format": "⚠️ Неверный формат. Используйте ДД.ММ.ГГГГ",
        "saved": "✅ <b>Дата сохранена.</b> Следующее напоминание: Понедельник 12:00 UTC.",
        "week_msg": "⏳ Это <b>{weeks}</b> неделя из {total}.",
        "profile": (
            "👤 <b>Ваш профиль Lifery</b>\n\n"
            "📅 Дата рождения: {birth_date}\n"
            "🗓 Прожито недель: <b>{weeks_lived}</b>\n"
            "⏳ Осталось недель: <b>{weeks_left}</b> (из 4680)\n\n"
            "<code>{progress_bar}</code> <b>{percentage}%</b>\n\n"
            "<i>Время — твой самый ценный ресурс.</i>"
        ),
        "about": (
            "🏛 <b>О проекте Lifery</b>\n\n"
            "Твоя жизнь — это не бесконечный ресурс. "
            "В среднем нам отведено <b>4680 недель</b> (около 90 лет).\n\n"
            "Мы часто живём так, будто впереди вечность: откладываем мечты, терпим нелюбимую работу, "
            "тратим часы на суету. Но это число — конечно.\n\n"
            "Этот бот — твой компас. Раз в неделю он напоминает: время уходит. "
            "Это не повод для грусти. Это повод <b>проснуться</b>.\n\n"
            "<i>Живи сейчас. Memento Mori.</i>\n\n"
            "💡 Вдохновлено блогом WaitButWhy (Tim Urban) и философией стоиков."
        ),
        "reset": "🗑 <b>Данные удалены.</b>\nЕсли захочешь вернуться — просто отправь мне дату рождения снова.",
        "not_registered": "⚠️ Вы еще не указали дату рождения. Отправьте её в формате ДД.ММ.ГГГГ",
    },
    "en": {
        "welcome": "Welcome to Lifery! 👋\n\nPlease enter your birth date in format DD.MM.YYYY",
        "invalid_format": "⚠️ Invalid format. Please use DD.MM.YYYY",
        "saved": "✅ <b>Date saved.</b> Next reminder: Monday 12:00 UTC.",
        "week_msg": "⏳ This is week <b>{weeks}</b> of {total}.",
        "profile": (
            "👤 <b>Your Lifery Profile</b>\n\n"
            "📅 Birth Date: {birth_date}\n"
            "🗓 Weeks Lived: <b>{weeks_lived}</b>\n"
            "⏳ Weeks Left: <b>{weeks_left}</b> (of 4680)\n\n"
            "<code>{progress_bar}</code> <b>{percentage}%</b>\n\n"
            "<i>Time is your most valuable resource.</i>"
        ),
        "about": (
            "🏛 <b>About Lifery</b>\n\n"
            "Your life is not an infinite resource. "
            "On average, we are given <b>4680 weeks</b> (about 90 years).\n\n"
            "We often live as if we have eternity ahead: postponing dreams, enduring jobs we hate, "
            "wasting hours on trivia. But this number is finite.\n\n"
            "This bot is your compass. Once a week, it reminds you: time is ticking. "
            "It's not a reason to be sad. It's a reason to <b>wake up</b>.\n\n"
            "<i>Live now. Memento Mori.</i>\n\n"
            "💡 Inspired by WaitButWhy (Tim Urban) and Stoic philosophy."
        ),
        "reset": "🗑 <b>Data deleted.</b>\nIf you want to come back, just send me your birth date again.",
        "not_registered": "⚠️ You haven't set your birth date yet. Send it in DD.MM.YYYY format.",
    },
}


def get_language(user_lang: str) -> str:
    if not user_lang:
        return "en"
    return "ru" if user_lang.lower().startswith("ru") else "en"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Determine user language (ru or en)
    lang = get_language(update.effective_user.language_code)

    # Send welcome message
    await update.message.reply_text(UI_TEXTS[lang]["welcome"])


async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Determine language again for error/success handling
    lang = get_language(update.effective_user.language_code)

    try:
        birth_date = datetime.datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text(UI_TEXTS[lang]["invalid_format"])
        return

    chat_id = update.effective_chat.id

    # Save to Database using ORM
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        user = result.scalar_one_or_none()

        if user:
            user.birth_date = birth_date
            user.language_code = lang
        else:
            user = User(chat_id=chat_id, birth_date=birth_date, language_code=lang)
            session.add(user)

        await session.commit()

    # --- INSTANT FEEDBACK LOGIC ---
    today = datetime.date.today()
    weeks_passed = (today - birth_date).days // 7
    total_weeks = 4680

    # Pick a random quote
    quote = random.choice(PHRASES.get(lang, PHRASES["en"]))

    # Format message
    intro = UI_TEXTS[lang]["week_msg"].format(weeks=weeks_passed, total=total_weeks)
    footer = UI_TEXTS[lang]["saved"]

    full_message = f"{intro}\n\n<i>{quote}</i>\n\n{footer}"

    await update.message.reply_text(full_message, parse_mode="HTML")


async def send_weekly_motivation(context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        today = datetime.date.today()

        for user in users:
            weeks_passed = (today - user.birth_date).days // 7
            total_weeks = 4680
            # User proper language check for saved users
            lang = (
                "ru"
                if user.language_code and user.language_code.lower().startswith("ru")
                else "en"
            )
            phrase = random.choice(PHRASES.get(lang, PHRASES["en"]))

            if lang == "ru":
                message = f"⏳ Неделя <b>{weeks_passed}</b> из {total_weeks}.\n\n<i>{phrase}</i>"
            else:
                message = f"⏳ Week <b>{weeks_passed}</b> of {total_weeks}.\n\n<i>{phrase}</i>"

            try:
                await context.bot.send_message(
                    chat_id=user.chat_id, text=message, parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Failed to send message to {user.chat_id}: {e}")


def generate_progress_bar(percent: int, length: int = 15) -> str:
    filled_length = int(length * percent // 100)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"[{bar}]"


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(update.effective_user.language_code)
    chat_id = update.effective_chat.id

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        user = result.scalar_one_or_none()

    if not user:
        await update.message.reply_text(UI_TEXTS[lang]["not_registered"])
        return

    today = datetime.date.today()
    weeks_lived = (today - user.birth_date).days // 7
    total_weeks = 4680
    weeks_left = total_weeks - weeks_lived
    percentage = int((weeks_lived / total_weeks) * 100)
    percentage = min(100, max(0, percentage))  # clamp 0-100

    msg = UI_TEXTS[lang]["profile"].format(
        birth_date=user.birth_date.strftime("%d.%m.%Y"),
        weeks_lived=weeks_lived,
        weeks_left=weeks_left,
        progress_bar=generate_progress_bar(percentage),
        percentage=percentage,
    )

    await update.message.reply_text(msg, parse_mode="HTML")


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(update.effective_user.language_code)
    await update.message.reply_text(UI_TEXTS[lang]["about"], parse_mode="HTML")


async def reset_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(update.effective_user.language_code)
    chat_id = update.effective_chat.id

    from bot.db import (
        delete_user,
    )  # Local import to avoid circular dependency issues if any

    deleted = await delete_user(chat_id)
    if deleted:
        await update.message.reply_text(UI_TEXTS[lang]["reset"], parse_mode="HTML")
    else:
        await update.message.reply_text(UI_TEXTS[lang]["not_registered"])


async def post_init(application):
    await init_db()
    # Set commands for suggestion menu
    await application.bot.set_my_commands(
        [
            ("start", "Start / Начать"),
            ("profile", "My Life / Моя жизнь"),
            ("about", "About / О проекте"),
            ("reset", "Delete Data / Удалить данные"),
        ]
    )


def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN is not set!")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("reset", reset_data))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_date)
    )

    job_queue = application.job_queue
    # Run every Monday at 12:00 UTC.
    job_queue.run_daily(
        send_weekly_motivation,
        time=datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc),
        days=(0,),
    )

    application.run_polling()


if __name__ == "__main__":
    main()
