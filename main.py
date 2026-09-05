import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://comex936.github.io/Mini-App/"
)


# =========================
# ПРОВЕРКА НАСТРОЕК
# =========================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не настроен в Railway Variables"
    )

if not ADMIN_ID:
    raise RuntimeError(
        "ADMIN_ID не настроен в Railway Variables"
    )


# =========================
# ЛОГИ
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# =========================
# BOT / DISPATCHER
# =========================

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()


# =========================
# КЛАВИАТУРА ПОЛЬЗОВАТЕЛЯ
# =========================

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Мои покупки",
                    callback_data="orders"
                ),
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="profile"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎫 Поддержка",
                    callback_data="support"
                )
            ],
        ]
    )


# =========================
# КЛАВИАТУРА АДМИНА
# =========================

def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-панель",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL + "#admin"
                    ),
                )
            ],
        ]
    )


# =========================
# /START
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user

    if user is None:
        return

    text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎮 Добро пожаловать в игровой маркетплейс!\n\n"
        "Здесь можно будет покупать:\n"
        "🎮 Игровые аккаунты\n"
        "💰 Игровую валюту\n"
        "🔑 Ключи\n"
        "🎁 Предметы\n"
        "➕ И многое другое.\n\n"
        "Нажми кнопку ниже, чтобы открыть магазин."
    )

    # Если пользователь администратор
    if user.id == ADMIN_ID:
        text += (
            "\n\n"
            "👑 Вы вошли как администратор."
        )

        await message.answer(
            text,
            reply_markup=admin_menu()
        )

        return

    # Обычный пользователь
    await message.answer(
        text,
        reply_markup=main_menu()
    )


# =========================
# /ADMIN
# =========================

@dp.message(Command("admin"))
async def admin_handler(message: Message):
    user = message.from_user

    if user is None:
        return

    # Проверяем Telegram ID
    if user.id != ADMIN_ID:
        await message.answer(
            "⛔ Доступ запрещён."
        )
        return

    await message.answer(
        "👑 Админ-панель\n\n"
        "Здесь вы можете управлять магазином.",
        reply_markup=admin_menu()
    )


# =========================
# ПРОФИЛЬ
# =========================

@dp.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user = callback.from_user

    if user.username:
        username_text = (
            f"📛 Username: @{user.username}"
        )
    else:
        username_text = (
            "📛 Username: не указан"
        )

    # Базовая информация
    text = (
        "👤 Профиль\n\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"👤 Имя: {user.first_name}\n"
        f"{username_text}\n\n"
        "📦 Покупок: 0"
    )

    # Кнопки профиля
    buttons = [
        [
            InlineKeyboardButton(
                text="📦 Мои покупки",
                callback_data="orders"
            )
        ]
    ]

    # Кнопка администратора
    # появляется ТОЛЬКО у владельца
    if user.id == ADMIN_ID:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="👑 Панель товаров",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL + "#admin"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🎫 Поддержка",
                callback_data="support"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.answer(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# МОИ ПОКУПКИ
# =========================

@dp.callback_query(F.data == "orders")
async def orders_handler(callback: CallbackQuery):
    await callback.message.answer(
        "📦 Мои покупки\n\n"
        "У вас пока нет покупок."
    )

    await callback.answer()


# =========================
# ПОДДЕРЖКА
# =========================

@dp.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    await callback.message.answer(
        "🎫 Поддержка\n\n"
        "Опишите вашу проблему "
        "следующим сообщением."
    )

    await callback.answer()


# =========================
# ЗАПУСК
# =========================

async def main():
    logging.info(
        "Запуск бота..."
    )

    # Удаляем старый webhook,
    # чтобы polling работал корректно
    await bot.delete_webhook(
        drop_pending_updates=True
    )

    # Проверяем подключение к Telegram
    me = await bot.get_me()

    logging.info(
        "Бот запущен: @%s",
        me.username
    )

    logging.info(
        "ADMIN_ID: %s",
        ADMIN_ID
    )

    logging.info(
        "WEBAPP_URL: %s",
        WEBAPP_URL
    )

    # Запускаем получение обновлений
    await dp.start_polling(bot)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    asyncio.run(main())
