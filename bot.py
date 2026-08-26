import asyncio
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не установлен")


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================
# КЛАВИАТУРЫ
# =========================

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
        kb.button(text=text, callback_data=callback_data)

    kb.button(
        text="◀️ Назад",
        callback_data="main"
    )

    kb.adjust(1)

    return kb.as_markup()


def back_to_main():
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад", callback_data="main")
    return kb.as_markup()


def back_to_settings():
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад", callback_data="settings")
    return kb.as_markup()


# =========================
# START
# =========================

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


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

@dp.callback_query(F.data == "main")
async def main_menu_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "💎 TelegaOn\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu()
    )

    await callback.answer()


# =========================
# ПОДКЛЮЧЕНИЕ
# =========================

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


# =========================
# НАСТРОЙКИ
# =========================

@dp.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):

    await callback.message.edit_text(
        "⚙️ Настройки TelegaOn\n\n"
        "Выберите функцию, которую хотите настроить:",
        reply_markup=settings_menu()
    )

    await callback.answer()


# =========================
# ФУНКЦИИ
# =========================

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


# =========================
# ПОМОЩЬ СОТРУДНИКОВ
# =========================

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


# =========================
# HTTP-СЕРВЕР ДЛЯ RENDER
# =========================

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

    print(f"HTTP server started on 0.0.0.0:{PORT}")


# =========================
# ЗАПУСК
# =========================

async def main():

    await start_web_server()

    print("TelegaOn запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
