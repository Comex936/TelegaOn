import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


BOT_TOKEN = os.getenv("BOT_TOKEN")

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

    kb.button(
        text="🗑️ Удалённые сообщения",
        callback_data="deleted"
    )

    kb.button(
        text="✏️ Изменённые сообщения",
        callback_data="edited"
    )

    kb.button(
        text="🎤 Аудиосообщения",
        callback_data="audio"
    )

    kb.button(
        text="🎥 Видеосообщения",
        callback_data="video"
    )

    kb.button(
        text="📷 Фотографии",
        callback_data="photos"
    )

    kb.button(
        text="📎 Файлы",
        callback_data="files"
    )

    kb.button(
        text="🎭 Стикеры",
        callback_data="stickers"
    )

    kb.button(
        text="🔔 Уведомления",
        callback_data="notifications"
    )

    kb.button(
        text="💬 Формат сообщений",
        callback_data="format"
    )

    kb.button(
        text="📴 Оффлайн-ответ",
        callback_data="offline"
    )

    kb.button(
        text="🚫 Бан-слова",
        callback_data="banwords"
    )

    kb.button(
        text="◀️ Назад",
        callback_data="main"
    )

    kb.adjust(1)

    return kb.as_markup()


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


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    text = (
        "Привет, дорогой пользователь! 💎\n\n"
        "Добро пожаловать в TelegaOn!\n\n"
        "Здесь я буду присылать удалённые "
        "сообщения, аудиосообщения, "
        "видеосообщения и так далее.\n\n"
        "Для начала подключите TelegaOn."
    )

    await message.answer(
        text,
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

    text = (
        "⚡ Подключение TelegaOn\n\n"
        
        "Чтобы подключить TelegaOn, "
        "откройте настройки Telegram.\n\n"

        "1️⃣ Откройте Настройки.\n"
        "2️⃣ Перейдите в раздел автоматизаций "
        "чатов.\n"
        "3️⃣ Добавьте туда бота TelegaOn.\n"
        "4️⃣ Выдайте необходимые разрешения.\n\n"

        "После этого TelegaOn сможет работать "
        "с разрешёнными функциями."
    )

    await callback.message.edit_text(
        text,
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
        "Выберите функцию, которую хотите "
        "настроить:",
        reply_markup=settings_menu()
    )

    await callback.answer()


# =========================
# УДАЛЁННЫЕ СООБЩЕНИЯ
# =========================

@dp.callback_query(F.data == "deleted")
async def deleted(callback: CallbackQuery):

    text = (
        "🗑️ Удалённые сообщения\n\n"
        "TelegaOn будет сохранять и присылать "
        "сообщения, которые были удалены "
        "в подключённых чатах.\n\n"
        "Статус: 🟢 Включено"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# ИЗМЕНЁННЫЕ СООБЩЕНИЯ
# =========================

@dp.callback_query(F.data == "edited")
async def edited(callback: CallbackQuery):

    text = (
        "✏️ Изменённые сообщения\n\n"

        "TelegaOn будет показывать "
        "предыдущую версию сообщения.\n\n"

        "Пример:\n\n"

        "✏️ Сообщение было редактировано!\n"
        "Пользователь: 💬 @юзер\n\n"

        "До:\n"
        "Как дела! Я в шоке!\n\n"

        "После:\n"
        "Я в школе! Как дела?"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# АУДИО
# =========================

@dp.callback_query(F.data == "audio")
async def audio(callback: CallbackQuery):

    text = (
        "🎤 Аудиосообщения\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые аудиосообщения.\n\n"
        "Статус: 🟢 Включено"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# ВИДЕО
# =========================

@dp.callback_query(F.data == "video")
async def video(callback: CallbackQuery):

    text = (
        "🎥 Видеосообщения\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые видеосообщения.\n\n"
        "Статус: 🟢 Включено"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# ФОТО
# =========================

@dp.callback_query(F.data == "photos")
async def photos(callback: CallbackQuery):

    text = (
        "📷 Фотографии\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые фотографии.\n\n"
        "Статус: 🟢 Включено"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# ФАЙЛЫ
# =========================

@dp.callback_query(F.data == "files")
async def files(callback: CallbackQuery):

    text = (
        "📎 Файлы\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые файлы.\n\n"
        "Статус: 🟢 Включено"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# СТИКЕРЫ
# =========================

@dp.callback_query(F.data == "stickers")
async def stickers(callback: CallbackQuery):

    text = (
        "🎭 Стикеры\n\n"
        "TelegaOn будет сохранять и присылать "
        "удалённые стикеры.\n\n"
        "Статус: 🟢 Включено"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# УВЕДОМЛЕНИЯ
# =========================

@dp.callback_query(F.data == "notifications")
async def notifications(callback: CallbackQuery):

    text = (
        "🔔 Уведомления\n\n"

        "Выберите, какие события должны\n"
        "приходить вам от TelegaOn.\n\n"

        "🗑️ Удалённые сообщения — 🟢\n"
        "✏️ Изменённые сообщения — 🟢\n"
        "🎤 Аудиосообщения — 🟢\n"
        "🎥 Видеосообщения — 🟢\n"
        "📷 Фотографии — 🟢\n"
        "📎 Файлы — 🟢\n"
        "🎭 Стикеры — 🟢"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# ФОРМАТ — БЕТА
# =========================

@dp.callback_query(F.data == "format")
async def format_messages(callback: CallbackQuery):

    text = (
        "💬 Формат сообщений\n\n"

        "Сейчас эта функция недоступна "
        "или находится в бета-тесте.\n\n"

        "Информация будет позже."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# ОФФЛАЙН-ОТВЕТ
# =========================

@dp.callback_query(F.data == "offline")
async def offline(callback: CallbackQuery):

    text = (
        "📴 Оффлайн-ответ\n\n"

        "TelegaOn автоматически отправит "
        "ваш ответ, когда вы будете не в сети.\n\n"

        "Статус: 🔴 Выключено"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# БАН-СЛОВА — БЕТА
# =========================

@dp.callback_query(F.data == "banwords")
async def banwords(callback: CallbackQuery):

    text = (
        "🚫 Бан-слова\n\n"

        "Сейчас эта функция недоступна "
        "или находится в бета-тесте.\n\n"

        "Информация будет позже."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================
# ПОМОЩЬ СОТРУДНИКОВ — БЕТА
# =========================

@dp.callback_query(F.data == "staff_help")
async def staff_help(callback: CallbackQuery):

    text = (
        "🧑‍💻 Помощь сотрудников\n\n"

        "Функция находится в бета-тесте.\n\n"

        "Сейчас возможность связаться "
        "с сотрудником TelegaOn недоступна.\n\n"

        "Информация будет позже."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_main()
    )

    await callback.answer()


# =========================
# ЗАПУСК
# =========================

async def main():

    print("TelegaOn запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
