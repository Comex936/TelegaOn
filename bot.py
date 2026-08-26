import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, BusinessConnection
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не установлен")


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("TelegaOn")


# =========================================================
# BOT
# =========================================================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# Здесь пока храним подключения в памяти.
# Позже перенесём это в базу данных.
business_connections = {}


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    kb = InlineKeyboardBuilder()

    kb.button(
        text="⚡ Подключить TelegaOn",
        callback_data="connect"
    )

    kb.button(
        text="⚙️ Настройки",
        callback_data="settings"
    )

    kb.button(
        text="🧑‍💻 Помощь сотрудников",
        callback_data="staff_help"
    )

    kb.adjust(1)

    return kb.as_markup()


# =========================================================
# SETTINGS MENU
# =========================================================

def settings_menu():

    kb = InlineKeyboardBuilder()

    buttons = [
        ("🗑️ Удалённые сообщения", "deleted"),
        ("✏️ Изменённые сообщения", "edited"),
        ("🎤 Аудиосообщения", "audio"),
        ("🎥 Видеосообщения", "video"),
        ("📷 Фотографии", "photos"),
        ("📎 Файлы", "files"),
        ("🎭 Стикеры", "stickers"),
        ("🔔 Уведомления", "notifications"),
        ("💬 Формат сообщений", "format"),
        ("📴 Оффлайн-ответ", "offline"),
        ("🚫 Бан-слова", "banwords"),
    ]

    for text, callback_data in buttons:
        kb.button(
            text=text,
            callback_data=callback_data
        )

    kb.button(
        text="◀️ Назад",
        callback_data="main"
    )

    kb.adjust(1)

    return kb.as_markup()


# =========================================================
# BACK BUTTONS
# =========================================================

def back_to_main():

    kb = InlineKeyboardBuilder()

    kb.button(
        text="◀️ Назад",
        callback_data="main"
    )

    return kb.as_markup()


def back_to_settings():

    kb = InlineKeyboardBuilder()

    kb.button(
        text="◀️ Назад",
        callback_data="settings"
    )

    return kb.as_markup()


# =========================================================
# /START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "Привет, дорогой пользователь! 💎\n\n"
        "Добро пожаловать в TelegaOn!\n\n"
        "Здесь я буду присылать удалённые "
        "сообщения, аудиосообщения, "
        "видеосообщения и так далее.\n\n"
        "Для начала подключите TelegaOn.",
        reply_markup=main_menu()
    )


# =========================================================
# BUSINESS CONNECTION
# =========================================================

@dp.business_connection()
async def business_connection_handler(
    connection: BusinessConnection
):

    connection_id = connection.id
    user_id = connection.user.id

    business_connections[connection_id] = connection

    logger.info("========================================")
    logger.info("📡 BUSINESS CONNECTION UPDATE")
    logger.info("Connection ID: %s", connection_id)
    logger.info("Business user ID: %s", user_id)
    logger.info("User name: %s", connection.user.full_name)
    logger.info("Username: @%s", connection.user.username)
    logger.info("Enabled: %s", connection.is_enabled)

    # В новых версиях Bot API права находятся
    # в connection.rights.
    if connection.rights:
        logger.info("Business rights: %s", connection.rights)

    logger.info("========================================")

    if connection.is_enabled:

        logger.info(
            "✅ TelegaOn успешно подключён "
            "к Business-аккаунту пользователя %s",
            user_id
        )

    else:

        logger.info(
            "🔴 TelegaOn отключён "
            "от Business-аккаунта пользователя %s",
            user_id
        )


# =========================================================
# BUSINESS MESSAGE TEST
# =========================================================

@dp.business_message()
async def business_message_handler(message: Message):

    logger.info("========================================")
    logger.info("📨 NEW BUSINESS MESSAGE")
    logger.info("Message ID: %s", message.message_id)
    logger.info("Chat ID: %s", message.chat.id)
    logger.info(
        "Business Connection ID: %s",
        message.business_connection_id
    )

    if message.from_user:
        logger.info(
            "From: %s (@%s)",
            message.from_user.full_name,
            message.from_user.username
        )

    if message.text:
        logger.info("Text: %s", message.text)

    logger.info("========================================")


# =========================================================
# EDITED BUSINESS MESSAGE TEST
# =========================================================

@dp.edited_business_message()
async def edited_business_message_handler(
    message: Message
):

    logger.info("========================================")
    logger.info("✏️ EDITED BUSINESS MESSAGE")
    logger.info("Message ID: %s", message.message_id)
    logger.info("Chat ID: %s", message.chat.id)
    logger.info(
        "Business Connection ID: %s",
        message.business_connection_id
    )

    if message.text:
        logger.info("New text: %s", message.text)

    logger.info("========================================")


# =========================================================
# DELETED BUSINESS MESSAGES TEST
# =========================================================

@dp.deleted_business_messages()
async def deleted_business_messages_handler(event):

    logger.info("========================================")
    logger.info("🗑️ BUSINESS MESSAGES DELETED")

    logger.info(
        "Business Connection ID: %s",
        event.business_connection_id
    )

    logger.info(
        "Chat ID: %s",
        event.chat.id
    )

    logger.info(
        "Deleted message IDs: %s",
        event.message_ids
    )

    logger.info("========================================")


# =========================================================
# MAIN MENU
# =========================================================

@dp.callback_query(F.data == "main")
async def main_menu_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "💎 TelegaOn\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu()
    )

    await callback.answer()


# =========================================================
# CONNECT
# =========================================================

@dp.callback_query(F.data == "connect")
async def connect(callback: CallbackQuery):

    await callback.message.edit_text(
        "⚡ Подключение TelegaOn\n\n"
        "Чтобы подключить TelegaOn:\n\n"
        "1️⃣ Откройте настройки Telegram.\n\n"
        "2️⃣ Перейдите в раздел автоматизаций "
        "чатов.\n\n"
        "3️⃣ Добавьте туда бота TelegaOn.\n\n"
        "4️⃣ Выдайте необходимые разрешения.\n\n"
        "После этого вернитесь сюда.",
        reply_markup=back_to_main()
    )

    await callback.answer()


# =========================================================
# SETTINGS
# =========================================================

@dp.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):

    await callback.message.edit_text(
        "⚙️ Настройки TelegaOn\n\n"
        "Выберите функцию, которую хотите настроить:",
        reply_markup=settings_menu()
    )

    await callback.answer()


# =========================================================
# SETTINGS ITEMS
# =========================================================

@dp.callback_query(F.data == "deleted")
async def deleted(callback: CallbackQuery):

    await callback.message.edit_text(
        "🗑️ Удалённые сообщения\n\n"
        "TelegaOn будет сохранять и присылать "
        "сообщения, которые были удалены "
        "в подключённых чатах.\n\n"
        "Статус: 🟢 Включено",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "edited")
async def edited(callback: CallbackQuery):

    await callback.message.edit_text(
        "✏️ Изменённые сообщения\n\n"
        "TelegaOn будет показывать предыдущую "
        "версию сообщения.\n\n"
        "Пример:\n\n"
        "✏️ Сообщение было редактировано!\n"
        "Пользователь: 💬 @юзер\n\n"
        "До:\n"
        "Как дела! Я в шоке!\n\n"
        "После:\n"
        "Я в школе! Как дела?",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "audio")
async def audio(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎤 Аудиосообщения\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые аудиосообщения.\n\n"
        "Статус: 🟢 Включено",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "video")
async def video(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎥 Видеосообщения\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые видеосообщения.\n\n"
        "Статус: 🟢 Включено",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "photos")
async def photos(callback: CallbackQuery):

    await callback.message.edit_text(
        "📷 Фотографии\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые фотографии.\n\n"
        "Статус: 🟢 Включено",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "files")
async def files(callback: CallbackQuery):

    await callback.message.edit_text(
        "📎 Файлы\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые файлы.\n\n"
        "Статус: 🟢 Включено",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "stickers")
async def stickers(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎭 Стикеры\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые стикеры.\n\n"
        "Статус: 🟢 Включено",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "notifications")
async def notifications(callback: CallbackQuery):

    await callback.message.edit_text(
        "🔔 Уведомления\n\n"
        "Выберите, какие события должны\n"
        "приходить вам от TelegaOn.\n\n"
        "🗑️ Удалённые сообщения — 🟢\n"
        "✏️ Изменённые сообщения — 🟢\n"
        "🎤 Аудиосообщения — 🟢\n"
        "🎥 Видеосообщения — 🟢\n"
        "📷 Фотографии — 🟢\n"
        "📎 Файлы — 🟢\n"
        "🎭 Стикеры — 🟢",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "format")
async def format_messages(callback: CallbackQuery):

    await callback.message.edit_text(
        "💬 Формат сообщений\n\n"
        "Сейчас эта функция недоступна "
        "или находится в бета-тесте.\n\n"
        "Информация будет позже.",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "offline")
async def offline(callback: CallbackQuery):

    await callback.message.edit_text(
        "📴 Оффлайн-ответ\n\n"
        "TelegaOn автоматически отправит "
        "ваш ответ, когда вы будете не в сети.\n\n"
        "Статус: 🔴 Выключено",
        reply_markup=back_to_settings()
    )

    await callback.answer()


@dp.callback_query(F.data == "banwords")
async def banwords(callback: CallbackQuery):

    await callback.message.edit_text(
        "🚫 Бан-слова\n\n"
        "Сейчас эта функция недоступна "
        "или находится в бета-тесте.\n\n"
        "Информация будет позже.",
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================================================
# STAFF HELP
# =========================================================

@dp.callback_query(F.data == "staff_help")
async def staff_help(callback: CallbackQuery):

    await callback.message.edit_text(
        "🧑‍💻 Помощь сотрудников\n\n"
        "Функция находится в бета-тесте.\n\n"
        "Сейчас возможность связаться "
        "с сотрудником TelegaOn недоступна.\n\n"
        "Информация будет позже.",
        reply_markup=back_to_main()
    )

    await callback.answer()


# =========================================================
# RENDER HTTP SERVER
# =========================================================

async def health(request):

    return web.Response(
        text="TelegaOn is running!"
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT
    )

    await site.start()

    logger.info(
        "🌐 HTTP server started on 0.0.0.0:%s",
        PORT
    )


# =========================================================
# START
# =========================================================

async def main():

    await start_web_server()

    logger.info("🤖 TelegaOn started!")

    await dp.start_polling(
        bot,
        allowed_updates=[
            "message",
            "callback_query",
            "business_connection",
            "business_message",
            "edited_business_message",
            "deleted_business_messages",
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
