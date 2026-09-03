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

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured in Railway Variables")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Мои покупки",
                    callback_data="orders",
                ),
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="profile",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎫 Поддержка",
                    callback_data="support",
                )
            ],
        ]
    )


def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-панель",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ],
        ]
    )


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

    if user.id == ADMIN_ID:
        text += "\n\n👑 Вы вошли как администратор."
        await message.answer(text, reply_markup=admin_menu())
    else:
        await message.answer(text, reply_markup=main_menu())


@dp.message(Command("admin"))
async def admin_handler(message: Message):
    user = message.from_user

    if user is None or user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    await message.answer(
        "👑 Админ-панель\n\n"
        "Здесь будет управление магазином.",
        reply_markup=admin_menu(),
    )


@dp.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user = callback.from_user

    await callback.message.answer(
        "👤 Профиль\n\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"👤 Имя: {user.first_name}\n\n"
        "📦 Покупок: 0"
    )

    await callback.answer()


@dp.callback_query(F.data == "orders")
async def orders_handler(callback: CallbackQuery):
    await callback.message.answer(
        "📦 Мои покупки\n\n"
        "У вас пока нет покупок."
    )

    await callback.answer()


@dp.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    await callback.message.answer(
        "🎫 Поддержка\n\n"
        "Опишите вашу проблему следующим сообщением."
    )

    await callback.answer()


async def main():
    logging.info("Starting bot...")

    await bot.delete_webhook(drop_pending_updates=True)

    me = await bot.get_me()

    logging.info("Bot started: @%s", me.username)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
