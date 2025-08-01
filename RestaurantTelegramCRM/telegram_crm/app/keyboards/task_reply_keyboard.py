from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_task_action_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Задача выполнена")],
            [KeyboardButton(text="📋 Вернуться к списку задач")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_report_action_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📤 Отправить отчёт")],
            [KeyboardButton(text="❌ Отменить отправку отчёта")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_remove_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_chek_task_action_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Задача закрыта")],
            [KeyboardButton(text="❌ Доработать")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
