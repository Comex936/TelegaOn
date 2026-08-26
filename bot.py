import os
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не найден в Variables!"
    )


# =========================================================
# ЛОГИ
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================================================
# BOT
# =========================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def main_menu():

    kb = InlineKeyboardBuilder()

    kb.button(
        text="📋 Как получить File ID",
        callback_data="help"
    )

    kb.adjust(1)

    return kb.as_markup()


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "🛠 <b>NFT File ID Helper</b>\n\n"
        "Привет! Я помогу тебе получать "
        "<b>File ID</b> для NFT.\n\n"
        "📌 Просто отправь мне Telegram-стикер.\n\n"
        "Я сразу покажу:\n"
        "🆔 File ID\n"
        "🔐 File Unique ID\n"
        "💻 Готовую строку для <code>nfts.py</code>\n\n"
        "Можешь отправлять стикеры один за другим.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================================================
# HELP
# =========================================================

@dp.message(Command("help"))
async def help_command(message: Message):

    await message.answer(
        "📋 <b>Как пользоваться</b>\n\n"
        "1️⃣ Найди нужный NFT-стикер.\n"
        "2️⃣ Отправь его мне.\n"
        "3️⃣ Я покажу его File ID.\n"
        "4️⃣ Скопируй File ID в <code>nfts.py</code>.\n\n"
        "💡 Можно отправлять сколько угодно "
        "стикеров подряд.",
        parse_mode="HTML"
    )


# =========================================================
# КНОПКА HELP
# =========================================================

@dp.callback_query(F.data == "help")
async def help_button(callback):

    await callback.message.edit_text(
        "📋 <b>Как получить File ID</b>\n\n"
        "Просто отправь мне нужный "
        "<b>Telegram-стикер</b>.\n\n"
        "Я автоматически получу его "
        "File ID и покажу тебе готовую "
        "строку для <code>nfts.py</code>.\n\n"
        "Например:\n\n"
        "<code>"
        '"file_id": "CAACAgIAAxkBAAIB..."'
        "</code>",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ПОЛУЧЕНИЕ FILE ID СТИКЕРА
# =========================================================

@dp.message(F.sticker)
async def sticker_handler(message: Message):

    sticker = message.sticker

    file_id = sticker.file_id
    unique_id = sticker.file_unique_id

    # -----------------------------------------------------
    # Готовая строка для nfts.py
    # -----------------------------------------------------

    python_line = (
        f'"file_id": "{file_id}"'
    )

    # -----------------------------------------------------
    # Информация о стикере
    # -----------------------------------------------------

    if sticker.emoji:

        emoji_text = sticker.emoji

    else:

        emoji_text = "Не указан"

    if sticker.set_name:

        set_text = sticker.set_name

    else:

        set_text = "Неизвестный набор"

    await message.answer(
        "✅ <b>Стикер найден!</b>\n\n"
        f"😀 Emoji: <b>{emoji_text}</b>\n"
        f"📦 Набор: <b>{set_text}</b>\n\n"
        "🆔 <b>File ID:</b>\n"
        f"<code>{file_id}</code>\n\n"
        "🔐 <b>File Unique ID:</b>\n"
        f"<code>{unique_id}</code>\n\n"
        "💻 <b>Для nfts.py:</b>\n"
        f"<code>{python_line}</code>",
        parse_mode="HTML"
    )


# =========================================================
# ОБЫЧНЫЙ ТЕКСТ
# =========================================================

@dp.message()
async def unknown_message(message: Message):

    await message.answer(
        "🤔 Я не нашёл здесь стикер.\n\n"
        "Просто отправь мне <b>Telegram-стикер</b>, "
        "и я покажу его File ID.",
        parse_mode="HTML"
    )


# =========================================================
# ЗАПУСК
# =========================================================

async def main():

    logging.info(
        "🛠 NFT File ID Helper запущен!"
    )

    await dp.start_polling(
        bot
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    import asyncio

    asyncio.run(
        main()
    )
