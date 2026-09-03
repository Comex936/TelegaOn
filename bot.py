```python
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from dotenv import load_dotenv


# =========================
# НАСТРОЙКИ
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")

ADMIN_ID = 8558737152

# Пока ставим временный URL.
# Позже сюда вставим HTTPS-ссылку нашего HTML Mini App.
WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://example.com"
)


# =========================
# ЛОГИ
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================
# BOT / DISPATCHER
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# КЛАВИАТУРЫ
# =========================

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Мои покупки",
                    callback_data="my_orders"
                ),
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎫 Поддержка",
                    callback_data="support"
                )
            ]
        ]
    )


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-панель",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ]
    )


# =========================
# /START
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user

    text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎮 Добро пожаловать в игровой маркетплейс.\n\n"
        "Здесь можно будет покупать:\n"
        "🎮 игровые аккаунты\n"
        "💰 игровую валюту\n"
        "🔑 ключи\n"
        "🎁 предметы и многое другое.\n\n"
        "Нажми кнопку ниже, чтобы открыть магазин."
    )

    if user.id == ADMIN_ID:
        text += "\n\n👑 Вы вошли как администратор."

        await message.answer(
            text,
            reply_markup=admin_menu()
        )
    else:
        await message.answer(
            text,
            reply_markup=main_menu()
        )


# =========================
# /ADMIN
# =========================

@dp.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "👑 Панель администратора\n\n"
        "Выберите нужный раздел:",
        reply_markup=admin_menu()
    )


# =========================
# CALLBACKS
# =========================

@dp.callback_query(F.data == "profile")
async def profile_handler(callback):
    user = callback.from_user

    await callback.message.answer(
        "👤 Ваш профиль\n\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Имя: {user.first_name}\n\n"
        "📦 Покупок: пока 0"
    )

    await callback.answer()


@dp.callback_query(F.data == "my_orders")
async def orders_handler(callback):
    await callback.message.answer(
        "📦 Мои покупки\n\n"
        "У вас пока нет покупок."
    )

    await callback.answer()


@dp.callback_query(F.data == "support")
async def support_handler(callback):
    await callback.message.answer(
        "🎫 Поддержка\n\n"
        "Если у вас возникла проблема с заказом, "
        "напишите администратору."
    )

    await callback.answer()


# =========================
# ЗАПУСК
# =========================

async def main():
    logging.info("Бот запускается...")

    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("Бот успешно запущен.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```
