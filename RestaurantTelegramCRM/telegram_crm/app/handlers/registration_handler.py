from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.user_service import UserService
from core.models.base_model import UserRole, SectorStatus

register_router = Router()


class Registration(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_role = State()
    waiting_for_position = State()
    waiting_for_sector = State()


@register_router.message(CommandStart())
async def start_registration(message: Message, state: FSMContext):
    existing_user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if existing_user:
        await message.answer(f"С возвращением, {existing_user.full_name}!")
        return

    await state.update_data(telegram_id=message.from_user.id)
    await message.answer(
        "Привет! Добро пожаловать в систему управления рестораном.\n"
        "Для начала, пожалуйста, введите ваше полное имя (имя и фамилия):"
    )
    await state.set_state(Registration.waiting_for_full_name)


@register_router.message(Registration.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    await state.update_data(full_name=full_name)

    # Создаем инлайн клавиатуру для выбора роли
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Менеджер", callback_data="role:manager")],
        [InlineKeyboardButton(text="Работник", callback_data="role:staff")]
    ])

    await message.answer("Отлично! Кем вы являетесь в нашем ресторане?", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_role)


@register_router.callback_query(lambda c: c.data and c.data.startswith('role:'))
async def process_role(callback_query: CallbackQuery, state: FSMContext):
    role_str = callback_query.data.split(':')[1]

    role_mapping = {
        "manager": UserRole.MANAGER,
        "staff": UserRole.STAFF
    }

    if role_str not in role_mapping:
        await callback_query.answer("Ошибка при выборе роли.", show_alert=True)
        return

    await state.update_data(role=role_mapping[role_str])
    await callback_query.answer()

    # Создаем инлайн клавиатуру для выбора сектора
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бар", callback_data="sector:bar")],
        [InlineKeyboardButton(text="Зал", callback_data="sector:hall")],
        [InlineKeyboardButton(text="Кухня", callback_data="sector:kitchen")],
        [InlineKeyboardButton(text="Нет рабочей зоны", callback_data="sector:none")]
    ])

    await callback_query.message.edit_text("Укажите рабочую зону:", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_sector)


# Удаляем старый хендлер, так как теперь используем callback
# @register_router.message(Registration.waiting_for_role)
# async def process_role(message: Message, state: FSMContext):
#     # ... старый код ...


@register_router.callback_query(lambda c: c.data and c.data.startswith('sector:'))
async def process_sector(callback_query: CallbackQuery, state: FSMContext):
    sector_str = callback_query.data.split(':')[1]

    sector_mapping = {
        "bar": SectorStatus.BAR,
        "hall": SectorStatus.HALL,
        "kitchen": SectorStatus.KITCHEN,
        "none": None,
    }

    if sector_str not in sector_mapping:
        await callback_query.answer("Ошибка при выборе сектора.", show_alert=True)
        return

    await state.update_data(sector=sector_mapping[sector_str])
    await callback_query.answer()
    await callback_query.message.edit_text("Отлично! Теперь укажите вашу должность:")
    await state.set_state(Registration.waiting_for_position)


# Удаляем старый хендлер, так как теперь используем callback
# @register_router.message(Registration.waiting_for_sector)
# async def process_se(message: Message, state: FSMContext):
#     # ... старый код ...


@register_router.message(Registration.waiting_for_position)
async def process_position(message: Message, state: FSMContext):
    position = message.text.strip()
    if not position:
        await message.answer("Пожалуйста, укажите вашу должность:")
        return

    data = await state.get_data()
    result = await UserService.create_new_user(
        telegram_id=data['telegram_id'],
        full_name=data['full_name'],
        role=data['role'],
        position=position,
        sector=data['sector']
    )
    await state.clear()

    if result['success']:
        await message.answer(f"Регистрация завершена! Добро пожаловать, {data['full_name']}!")
    else:
        await message.answer(f"Ошибка: {result['message']}")