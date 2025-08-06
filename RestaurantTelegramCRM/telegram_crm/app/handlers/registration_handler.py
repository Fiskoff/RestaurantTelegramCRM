from aiogram import Router
from aiogram.types import Message
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
    await message.answer(
        "Отлично! Кем вы являетесь в нашем ресторане?\n"
        "Пожалуйста, выберите роль из списка:\n"
        "- Менеджер\n"
        "- Работник"
    )
    await state.set_state(Registration.waiting_for_role)


@register_router.message(Registration.waiting_for_role)
async def process_role(message: Message, state: FSMContext):
    role_mapping = {
        "менеджер": UserRole.MANAGER,
        "работник": UserRole.STAFF
    }
    user_input = message.text.strip().lower()
    if user_input not in role_mapping:
        await message.answer(
            "Неизвестная роль. Пожалуйста, выберите из списка:\n"
            "- Менеджер\n"
            "- Работник"
        )
        return

    await state.update_data(role=role_mapping[user_input])
    await message.answer("Укажите рабочую зону\nОтправьте число:\n 1 - Бар\n 2 - Зал\n 3 - Кухня\n 4 - Нет рабочей зоны")
    await state.set_state(Registration.waiting_for_sector)


@register_router.message(Registration.waiting_for_sector)
async def process_se(message: Message, state: FSMContext):
    sector_mapping = {
        1: SectorStatus.BAR,
        2: SectorStatus.HALL,
        3: SectorStatus.KITCHEN,
        4: None,
    }
    user_input = int(message.text.strip())
    if user_input not in sector_mapping:
        await message.answer(
            "Неизвестный сектор. Пожалуйста, выберите из списка:\n"
            "1 - Бар\n2 - Зал\n3 - Кухня\n4 - Нет рабочей зоны"
        )
        return
    await state.update_data(sector=sector_mapping[user_input])
    await message.answer("Отлично! Теперь укажите вашу должность:")
    await state.set_state(Registration.waiting_for_position)


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