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
            [KeyboardButton(text="❌ Доработать задачу")],
            [KeyboardButton(text="📋 Вернуться к списку выполненных задач")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_update_task_action_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Изменить задачу")],
            [KeyboardButton(text="❌ Удалить задачу")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )