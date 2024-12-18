import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
)
from parsers.parser_robota import RobotaContent, PeriodType
from config import TG_BOT_TOKEN
import re

user_data = {}
user_state = {}
cached_results = {}
current_page = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reset_user_data(user_id)

    keyboard = [[KeyboardButton("Position"), KeyboardButton("City")],
                [KeyboardButton("Period"), KeyboardButton("Next")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state.pop(user_id, None)
    user_data.pop(user_id, None)
    cached_results.pop(user_id, None)
    current_page.pop(user_id, None)
    await update.message.reply_text("Ваш сеанс завершен. Нажмите /start для нового сеанса.")


def reset_user_data(user_id):
    user_data[user_id] = {'position': None, 'city': None, 'period': None, 'salary_range': None}
    user_state[user_id] = None
    cached_results[user_id] = []
    current_page[user_id] = 0


async def position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = 'awaiting_position'
    await update.message.reply_text("Введите название позиции или должности:")


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = 'awaiting_city'
    await update.message.reply_text("Введите город или страну:")


async def period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[InlineKeyboardButton(p.name, callback_data=p.value)] for p in PeriodType]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Выберите период:", reply_markup=reply_markup)


async def save_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id]['period'] = query.data
    await query.edit_message_text(f"Период выбран: {query.data}")
    await show_menu(update)


async def save_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]['position'] = update.message.text
    user_state[user_id] = None
    await update.message.reply_text(f"Позиция сохранена: {update.message.text}")
    await show_menu(update)


async def save_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]['city'] = update.message.text
    user_state[user_id] = None
    await update.message.reply_text(f"Город сохранен: {update.message.text}")
    await show_menu(update)


async def filter_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = 'awaiting_salary_range'
    await update.message.reply_text("Введите диапазон зарплат (например, 1000-3000):")


async def apply_salary_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    salary_range = update.message.text

    match = re.match(r'(\d+)-(\d+)', salary_range)
    if not match:
        await update.message.reply_text("❗ Неверный формат. Введите диапазон как 1000-3000.")
        return
    user_data[user_id]['salary_range'] = tuple(map(int, match.groups()))
    user_state[user_id] = None
    await update.message.reply_text("Фильтр по зарплате сохранен.")


async def next_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    params = user_data[user_id]
    position = params.get('position', '')
    city = params.get('city', 'ukraine')
    period = params.get('period', PeriodType.THREE_MONTHS.value)

    if not position:
        await update.message.reply_text(
            "Нужно указать позицию. Пожалуйста, выберите 'Position' и введите её.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Position"), KeyboardButton("City")],
                 [KeyboardButton("Period"), KeyboardButton("Next")]],
                resize_keyboard=True
            )
        )
        return

    await update.message.reply_text(f"🔎 Поиск начался с параметрами:\n"
                                    f"📄 Position: {position}\n📍 City: {city}\n🗓 Period: {period}")

    asyncio.create_task(start_background_search(user_id, position, city, period))

    keyboard = [[KeyboardButton("Filter Salary"), KeyboardButton("Show")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Поиск идет. Вы можете задать фильтр по зарплате или нажать 'Show' для показа результатов.",
        reply_markup=reply_markup)


async def start_background_search(user_id, position, city, period):
    try:
        content_robota = await asyncio.to_thread(RobotaContent(
            position=position,
            city=city,
            period=period
        ).get_info)

        if not content_robota:
            cached_results[user_id] = 'empty'
            print("Результаты отсутствуют.")
            return
        cached_results[user_id] = content_robota
    except Exception as e:
        cached_results[user_id] = []
        print(f"Ошибка поиска: {e}")



async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not cached_results.get(user_id):
        await update.message.reply_text(
            "Ожидайте завершения поиска...",
            reply_markup=ReplyKeyboardRemove()
        )

        while not cached_results.get(user_id):
            await asyncio.sleep(1)

    if isinstance(cached_results.get(user_id), str) and cached_results.get(user_id) == 'empty':
        reset_user_data(user_id)
        await update.message.reply_text(
            "По вашему запросу ничего не найдено. Попробуйте изменить параметры поиска.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Position"), KeyboardButton("City")],
                 [KeyboardButton("Period"), KeyboardButton("Next")]],
                resize_keyboard=True
            )
        )
        return

    await display_results(update, user_id)


async def display_results(update: Update, user_id):
    results = cached_results.get(user_id, [])

    if not results:
        await update.message.reply_text("Результаты отсутствуют или поиск еще не завершен.")
        return

    salary_range = user_data[user_id].get('salary_range')
    if salary_range:
        min_salary, max_salary = salary_range
        results = [r for r in results if
                   r.get('salary') and min_salary <= int(re.search(r'\d+', r['salary']).group()) <= max_salary]
    start_idx = current_page[user_id]
    end_idx = min(start_idx + 5, len(results))
    print(len(results))
    print(start_idx, end_idx)
    for candidate in results[start_idx:end_idx]:
        print(candidate)
        text = (f"🔗 [Ссылка]({candidate['link']})\n📄 {candidate['position']}\n👤 {candidate['name']}\n"
                f"📍 {candidate['location']}\n💰 {candidate.get('salary', 'Не указана')}\n"
                f"🔧 Опыт: {candidate.get('experience', 'Не указан')}")
        await update.message.reply_text(text, parse_mode='Markdown')
    current_page[user_id] = end_idx
    total_results = len(results)
    if current_page[user_id] < total_results:
        await update.message.reply_text(f"Показано {min(end_idx, total_results)} из {total_results}.",
                                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(f"More")]],
                                                                         resize_keyboard=True))
    else:
        await update.message.reply_text("Все записи показаны. Возвращаюсь в главное меню...")
        reset_user_data(user_id)
        await show_menu(update)


async def show_menu(update: Update):
    keyboard = [[KeyboardButton("Position"), KeyboardButton("City")],
                [KeyboardButton("Period"), KeyboardButton("Next")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.message.reply_text("Что дальше?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Что дальше?", reply_markup=reply_markup)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_state.get(user_id) == 'awaiting_position':
        await save_position(update, context)
    elif user_state.get(user_id) == 'awaiting_city':
        await save_city(update, context)
    elif user_state.get(user_id) == 'awaiting_salary_range':
        await apply_salary_filter(update, context)
    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки для навигации.")


def main():
    application = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Position$"), position))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^City$"), city))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Period$"), period))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Next$"), next_step))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Show$"), show_results))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^More$"), show_results))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Filter Salary$"), filter_salary))
    application.add_handler(CallbackQueryHandler(save_period))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()


if __name__ == "__main__":
    main()
