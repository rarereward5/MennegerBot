import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

BOT_TOKEN = "8053502095:AAHTbgRZUda6OF9bN6L8klnL7EBgpjNkpE0" 
ADMIN_ID = 8299768278 

SERVICES = {
    "search_utils": "Пак поисковых утилит",
    "reporters": "Пак телеграм репортеров сносера",
    "databases": "Приватные базы данных",
    "smtp": "СМТП почты эмаилы",
    "signs": "Свободные сигны для редактирования",
    "write_script": "Подготовить скрипт",
    "private": "Приватка",
    "anon": "Скрыть от Шерлока анонимитизация",
    "mysql": "Курс по MySQL",
    "programming": "Курс по программированию"
}

class UserForm(StatesGroup):
    waiting_for_problem = State()
    waiting_for_question = State()
    choosing_service = State()

def get_start_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1) Проблема", callback_data="problem")],
        [InlineKeyboardButton(text="2) Нужна услуга", callback_data="service")],
        [InlineKeyboardButton(text="3) Вопрос", callback_data="question")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_service_keyboard():
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=f"select_service_{k}")]
        for k, v in SERVICES.items()
    ])
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="start_menu"))
    return builder

def get_confirm_keyboard(service_key):
    buttons = [
        [InlineKeyboardButton(text="Да ✅", callback_data=f"confirm_{service_key}")],
        [InlineKeyboardButton(text="Нет ❌", callback_data="cancel_service")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💻 Привет чем могу помочь ? Данный бот используется в цели менеджера ⚡",
        reply_markup=get_start_keyboard(),
    )

@dp.callback_query(F.data == "cancel_service")
@dp.callback_query(F.data == "start_menu")
async def cb_back_to_start(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text(
        "💻 Привет чем могу помочь ? Данный бот используется в цели менеджера ⚡",
        reply_markup=get_start_keyboard(),
    )
    await query.answer()

@dp.callback_query(F.data == "problem")
async def cb_problem(query: CallbackQuery, state: FSMContext):
    await state.set_state(UserForm.waiting_for_problem)
    await query.message.edit_text(
        "Опишите вашу проблему чем я могу вам помочь

"
        "После вашего сообщения мы отправим его @owersz чтобы позже он вам ответил, прошу не спамить ему в лс"
    )
    await query.answer()

@dp.message(UserForm.waiting_for_problem)
async def process_problem_text(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user = message.from_user
    username = f"@{user.username}" if user.username else "N/A"
    admin_text = (
        f"Получена заявка на тип: (проблема)
"
        f"Отправлена от: (ID: {user.id}), (Username: {username})
"
        f"Текст сообщения: {message.text}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        await message.answer("✅ Ваше сообщение о проблеме успешно отправлено @owersz.")
    except Exception as e:
        logging.error(f"Failed to send message to admin {ADMIN_ID}: {e}")
        await message.answer("⚠️ Произошла ошибка при отправке. Попробуйте позже.")
    await cmd_start(message, state)

@dp.callback_query(F.data == "service")
async def cb_service(query: CallbackQuery, state: FSMContext):
    await state.set_state(UserForm.choosing_service)
    await query.message.edit_text("Выберите услугу", reply_markup=get_service_keyboard())
    await query.answer()

@dp.callback_query(UserForm.choosing_service, F.data.startswith("select_service_"))
async def cb_select_service(query: CallbackQuery, state: FSMContext):
    service_key = query.data.split("select_service_")[1]
    if service_key in SERVICES:
        await state.update_data(selected_service_key=service_key)
        await query.message.edit_text(
            "✅ Услуга выбрана вы хотите подтвердить что вам нужна именно эта ? ⚡",
            reply_markup=get_confirm_keyboard(service_key),
        )
    else:
        await query.answer("Ошибка: услуга не найдена", show_alert=True)
    await query.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def cb_confirm_service(query: CallbackQuery, state: FSMContext, bot: Bot):
    service_key = query.data.split("confirm_")[1]
    service_name = SERVICES.get(service_key, "Неизвестная услуга")
    await state.clear()
    user = query.from_user
    username = f"@{user.username}" if user.username else "N/A"
    admin_text = (
        f"Данный покупатель: (Username: {username}, ID: {user.id}) "
        f"хочет купить вашу услугу: ({service_name})"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        await query.message.edit_text(
            "❄️ Выбор услуги от вас отправлен пользователю @owersz 🪪
"
            "🌐 Ожидайте ответа он вам ответит либо с бота либо со своего аккаунта ⌛"
        )
    except Exception as e:
        logging.error(f"Failed to send message to admin {ADMIN_ID}: {e}")
        await query.message.edit_text("⚠️ Произошла ошибка при отправке. Попробуйте позже.")
    await query.answer()

@dp.callback_query(F.data == "question")
async def cb_question(query: CallbackQuery, state: FSMContext):
    await state.set_state(UserForm.waiting_for_question)
    await query.message.edit_text("⚡ Введите ваш вопрос ⚡")
    await query.answer()

@dp.message(UserForm.waiting_for_question)
async def process_question_text(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user = message.from_user
    username = f"@{user.username}" if user.username else "N/A"
    admin_text = (
        f"Получена заявка на тип: (вопрос)
"
        f"Отправлена от: (ID: {user.id}), (Username: {username})
"
        f"Текст сообщения: {message.text}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        await message.answer("🌐 Ждите ответа от @owersz в течении суток ⌛")
    except Exception as e:
        logging.error(f"Failed to send message to admin {ADMIN_ID}: {e}")
        await message.answer("⚠️ Произошла ошибка при отправке. Попробуйте позже.")
    await cmd_start(message, state)

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
