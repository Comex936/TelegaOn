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

ADMIN_ID = int(
    os.getenv("ADMIN_ID", "0")
)

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://comex936.github.io/Mini-App/"
)


if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не настроен в Railway Variables"
    )


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# =========================
# BOT
# =========================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================
# USER MENU
# =========================

def main_menu():

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


# =========================
# ADMIN MENU
# =========================

def admin_menu():

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
async def start_handler(
    message: Message
):

    user = message.from_user

    if user is None:
        return


    text = (
        f"👋 Привет, {user.first_name}!\n\n"

        "🎮 Добро пожаловать "
        "в игровой маркетплейс!\n\n"

        "Здесь можно будет покупать:\n"

        "🎮 Игровые аккаунты\n"
        "💰 Игровую валюту\n"
        "🔑 Ключи\n"
        "🎁 Предметы\n"
        "➕ И многое другое.\n\n"

        "Нажми кнопку ниже, "
        "чтобы открыть магазин."
    )


    # =========================
    # ADMIN
    # =========================

    if user.id == ADMIN_ID:

        text += (
            "\n\n"
            "👑 Вы вошли как администратор."
        )

        await message.answer(
            text,
            reply_markup=admin_menu(),
        )

        return


    # =========================
    # USER
    # =========================

    await message.answer(
        text,
        reply_markup=main_menu(),
    )


# =========================
# /ADMIN
# =========================

@dp.message(Command("admin"))
async def admin_handler(
    message: Message
):

    user = message.from_user

    if user is None:
        return


    if user.id != ADMIN_ID:

        await message.answer(
            "⛔ Доступ запрещён."
        )

        return


    await message.answer(
        "👑 Админ-панель\n\n"
        "Здесь вы можете "
        "управлять магазином.",
        reply_markup=admin_menu(),
    )


# =========================
# PROFILE
# =========================

@dp.callback_query(
    F.data == "profile"
)
async def profile_handler(
    callback: CallbackQuery
):

    user = callback.from_user


    await callback.message.answer(

        "👤 Профиль\n\n"

        f"🆔 Telegram ID: {user.id}\n"

        f"👤 Имя: "
        f"{user.first_name}\n"

        f"📛 Username: "
        f"@{user.username}"
        if user.username
        else
        "📛 Username: не указан\n"

        "\n📦 Покупок: 0"

    )


    await callback.answer()


# =========================
# ORDERS
# =========================

@dp.callback_query(
    F.data == "orders"
)
async def orders_handler(
    callback: CallbackQuery
):

    await callback.message.answer(

        "📦 Мои покупки\n\n"

        "У вас пока нет покупок."

    )

    await callback.answer()


# =========================
# SUPPORT
# =========================

@dp.callback_query(
    F.data == "support"
)
async def support_handler(
    callback: CallbackQuery
):

    await callback.message.answer(

        "🎫 Поддержка\n\n"

        "Опишите вашу проблему "
        "следующим сообщением."

    )

    await callback.answer()


# =========================
# START BOT
# =========================

async def main():

    logging.info(
        "Запуск бота..."
    )


    await bot.delete_webhook(
        drop_pending_updates=True
    )


    me = await bot.get_me()


    logging.info(
        "Бот запущен: @%s",
        me.username
    )


    await dp.start_polling(
        bot
    )


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
