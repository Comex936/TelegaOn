
import asyncio
import logging
import os
from typing import Optional

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    BusinessConnection,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from supabase import create_client, Client


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

OWNER_ID = int(os.getenv("OWNER_ID", "0"))


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не установлен")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL не установлен")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY не установлен")


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("TelegaOn")


# =========================================================
# BOT / DATABASE
# =========================================================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# =========================================================
# TEMPORARY USER SETTINGS
# =========================================================

user_settings = {}

waiting_for_offline_text = set()

user_menu_messages = {}


def get_settings(user_id: int):

    if user_id not in user_settings:

        user_settings[user_id] = {
            "deleted": True,
            "edited": True,
            "audio": True,
            "video": True,
            "photos": True,
            "files": True,
            "stickers": True,
            "offline": False,
            "offline_text": "Пока не установлен.",
        }

    return user_settings[user_id]


def status_text(enabled: bool) -> str:

    if enabled:
        return "🟢 Включено"

    return "🔴 Выключено"


# =========================================================
# DATABASE HELPERS
# =========================================================

def get_user(telegram_id: int):

    try:

        result = (
            supabase
            .table("users")
            .select("*")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception:
        logger.exception("Ошибка получения пользователя")

    return None


def save_user(
    telegram_id: int,
    username: Optional[str],
    full_name: str
):

    try:

        existing = get_user(telegram_id)

        if telegram_id == OWNER_ID:
            role = "owner"

        elif existing:
            role = existing.get("role", "user")

        else:
            role = "user"

        (
            supabase
            .table("users")
            .upsert(
                {
                    "telegram_id": telegram_id,
                    "username": username,
                    "full_name": full_name,
                    "role": role,
                },
                on_conflict="telegram_id"
            )
            .execute()
        )

    except Exception:
        logger.exception("Ошибка сохранения пользователя")


def get_role(telegram_id: int) -> str:

    if telegram_id == OWNER_ID:
        return "owner"

    user = get_user(telegram_id)

    if not user:
        return "user"

    return user.get("role", "user")


def is_owner(telegram_id: int) -> bool:
    return telegram_id == OWNER_ID


def is_admin(telegram_id: int) -> bool:
    return get_role(telegram_id) in (
        "owner",
        "admin"
    )


def is_tester(telegram_id: int) -> bool:
    return get_role(telegram_id) in (
        "owner",
        "admin",
        "tester"
    )


# =========================================================
# ADMIN / TESTER DATABASE
# =========================================================

def get_users_by_role(role: str):

    try:

        result = (
            supabase
            .table("users")
            .select("*")
            .eq("role", role)
            .execute()
        )

        return result.data or []

    except Exception:

        logger.exception(
            "Ошибка получения списка пользователей"
        )

        return []


def set_user_role(
    telegram_id: int,
    role: str,
    username: Optional[str] = None,
    full_name: Optional[str] = None
):

    try:

        data = {
            "telegram_id": telegram_id,
            "role": role,
        }

        if username is not None:
            data["username"] = username

        if full_name is not None:
            data["full_name"] = full_name

        (
            supabase
            .table("users")
            .upsert(
                data,
                on_conflict="telegram_id"
            )
            .execute()
        )

        return True

    except Exception:

        logger.exception(
            "Ошибка изменения роли"
        )

        return False


# =========================================================
# BUSINESS CONNECTION DATABASE
# =========================================================

def save_business_connection(
    connection: BusinessConnection
):

    try:

        rights = None

        if connection.rights:
            rights = connection.rights.model_dump()

        (
            supabase
            .table("business_connections")
            .upsert(
                {
                    "connection_id": connection.id,
                    "telegram_id": connection.user.id,
                    "is_enabled": connection.is_enabled,
                    "rights": rights,
                },
                on_conflict="connection_id"
            )
            .execute()
        )

        logger.info(
            "🗄️ Business Connection сохранён в Supabase"
        )

    except Exception:

        logger.exception(
            "Ошибка сохранения Business Connection"
        )


# =========================================================
# MESSAGE DATABASE
# =========================================================

def get_message_type(message: Message) -> str:

    if message.text:
        return "text"

    if message.photo:
        return "photo"

    if message.video:
        return "video"

    if message.video_note:
        return "video_note"

    if message.audio:
        return "audio"

    if message.voice:
        return "voice"

    if message.document:
        return "document"

    if message.sticker:
        return "sticker"

    if message.animation:
        return "animation"

    if message.contact:
        return "contact"

    if message.location:
        return "location"

    return "other"


def save_business_message(message: Message):

    try:

        sender_id = None
        sender_username = None

        if message.from_user:
            sender_id = message.from_user.id
            sender_username = message.from_user.username

        message_data = message.model_dump(
            exclude_none=True
        )

        (
            supabase
            .table("messages")
            .upsert(
                {
                    "business_connection_id":
                        message.business_connection_id,

                    "chat_id":
                        message.chat.id,

                    "message_id":
                        message.message_id,

                    "sender_id":
                        sender_id,

                    "sender_username":
                        sender_username,

                    "message_type":
                        get_message_type(message),

                    "text_content":
                        message.text,

                    "message_data":
                        message_data,
                },
                on_conflict=(
                    "business_connection_id,"
                    "chat_id,"
                    "message_id"
                )
            )
            .execute()
        )

        logger.info(
            "💾 Сообщение %s сохранено",
            message.message_id
        )

    except Exception:

        logger.exception(
            "Ошибка сохранения Business Message"
        )


# =========================================================
# MAIN MENU
# =========================================================

def main_menu(user_id: int):

    kb = InlineKeyboardBuilder()

    kb.button(
        text="⚡ Подключить TelegaOn",
        callback_data="connect"
    )

    kb.button(
        text="⚙️ Настройки",
        callback_data="settings"
    )

    if is_admin(user_id):

        kb.button(
            text="👥 Админы и тестеры",
            callback_data="staff"
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


def back_to_settings():

    kb = InlineKeyboardBuilder()

    kb.button(
        text="◀️ Назад",
        callback_data="settings"
    )

    return kb.as_markup()


def back_to_main(user_id: int):

    kb = InlineKeyboardBuilder()

    kb.button(
        text="◀️ Назад",
        callback_data="main"
    )

    return kb.as_markup()


# =========================================================
# FUNCTION CONTROLS
# =========================================================

def function_controls(
    function_name: str,
    enabled: bool,
    can_edit: bool = False
):

    kb = InlineKeyboardBuilder()

    if enabled:

        kb.button(
            text="🔴 Выключить",
            callback_data=f"disable:{function_name}"
        )

    else:

        kb.button(
            text="🟢 Включить",
            callback_data=f"enable:{function_name}"
        )

    if can_edit:

        kb.button(
            text="✏️ Изменить ответ",
            callback_data=f"edit:{function_name}"
        )

    kb.button(
        text="◀️ Назад",
        callback_data="settings"
    )

    kb.adjust(1)

    return kb.as_markup()


# =========================================================
# SETTINGS INFO
# =========================================================

SETTINGS_INFO = {

    "deleted": (
        "🗑️ Удалённые сообщения",
        "TelegaOn будет сохранять и присылать "
        "сообщения, которые были удалены "
        "в подключённых чатах."
    ),

    "edited": (
        "✏️ Изменённые сообщения",
        "TelegaOn будет показывать предыдущую "
        "версию сообщения.\n\n"
        "Пример:\n\n"
        "✏️ Сообщение было редактировано!\n"
        "Пользователь: 💬 @юзер\n\n"
        "До:\n"
        "Как дела! Я в шоке!\n\n"
        "После:\n"
        "Я в школе! Как дела?"
    ),

    "audio": (
        "🎤 Аудиосообщения",
        "Удалённые аудиосообщения будут "
        "сохраняться."
    ),

    "video": (
        "🎥 Видеосообщения",
        "Удалённые видеосообщения будут "
        "сохраняться."
    ),

    "photos": (
        "📷 Фотографии",
        "Удалённые фотографии будут "
        "сохраняться."
    ),

    "files": (
        "📎 Файлы",
        "Удалённые файлы будут "
        "сохраняться."
    ),

    "stickers": (
        "🎭 Стикеры",
        "Удалённые стикеры будут "
        "сохраняться."
    ),
}


async def show_function_page(
    callback: CallbackQuery,
    function_name: str
):

    settings = get_settings(
        callback.from_user.id
    )

    title, description = SETTINGS_INFO[
        function_name
    ]

    await callback.message.edit_text(
        f"{title}\n\n"
        f"{description}\n\n"
        f"Статус: "
        f"{status_text(settings[function_name])}",
        reply_markup=function_controls(
            function_name,
            settings[function_name]
        )
    )


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    if message.from_user:

        save_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name
        )

    user_id = message.from_user.id

    await message.answer(
        "Привет, дорогой пользователь! 💎\n\n"
        "Добро пожаловать в TelegaOn!\n\n"
        "Здесь я буду присылать удалённые "
        "сообщения, аудиосообщения, "
        "видеосообщения и так далее.\n\n"
        "Для начала подключите TelegaOn.",
        reply_markup=main_menu(user_id)
    )


# =========================================================
# RECEIVE NEW OFFLINE TEXT
# =========================================================

@dp.message(
    F.text,
    ~F.text.startswith("/")
)
async def receive_offline_text(
    message: Message
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    if user_id not in waiting_for_offline_text:
        return

    new_text = message.text.strip()

    if not new_text:
        return

    settings = get_settings(user_id)

    settings["offline_text"] = new_text

    waiting_for_offline_text.discard(
        user_id
    )

    menu_data = user_menu_messages.get(
        user_id
    )

    if menu_data:

        try:

            await bot.edit_message_text(
                chat_id=menu_data["chat_id"],
                message_id=menu_data["message_id"],
                text=(
                    "📴 Оффлайн-ответ\n\n"
                    "TelegaOn сможет отправлять "
                    "автоматический ответ, когда "
                    "вы будете не в сети.\n\n"
                    f"Статус: "
                    f"{status_text(settings['offline'])}\n\n"
                    "Текущий ответ:\n"
                    f"«{new_text}»"
                ),
                reply_markup=function_controls(
                    "offline",
                    settings["offline"],
                    can_edit=True
                )
            )

        except Exception:

            logger.exception(
                "Не удалось отредактировать меню"
            )

    try:

        await message.delete()

    except Exception:

        pass

    user_menu_messages.pop(
        user_id,
        None
    )


# =========================================================
# MAIN MENU CALLBACK
# =========================================================

@dp.callback_query(F.data == "main")
async def main_callback(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    await callback.message.edit_text(
        "💎 TelegaOn\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu(user_id)
    )

    await callback.answer()


# =========================================================
# CONNECT
# =========================================================

@dp.callback_query(F.data == "connect")
async def connect_callback(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "⚡ Подключение TelegaOn\n\n"
        "Чтобы подключить TelegaOn:\n\n"
        "1️⃣ Откройте настройки Telegram.\n\n"
        "2️⃣ Перейдите в раздел "
        "автоматизаций чатов.\n\n"
        "3️⃣ Добавьте туда TelegaOn.\n\n"
        "4️⃣ Выдайте необходимые разрешения.\n\n"
        "После подключения TelegaOn автоматически "
        "получит Business Connection.",
        reply_markup=back_to_main(
            callback.from_user.id
        )
    )

    await callback.answer()


# =========================================================
# SETTINGS
# =========================================================

@dp.callback_query(F.data == "settings")
async def settings_callback(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "⚙️ Настройки TelegaOn\n\n"
        "Выберите функцию, которую хотите настроить:",
        reply_markup=settings_menu()
    )

    await callback.answer()


# =========================================================
# SETTINGS FUNCTIONS
# =========================================================

@dp.callback_query(F.data == "deleted")
async def deleted_callback(
    callback: CallbackQuery
):

    await show_function_page(
        callback,
        "deleted"
    )

    await callback.answer()


@dp.callback_query(F.data == "edited")
async def edited_callback(
    callback: CallbackQuery
):

    await show_function_page(
        callback,
        "edited"
    )

    await callback.answer()


@dp.callback_query(F.data == "audio")
async def audio_callback(
    callback: CallbackQuery
):

    await show_function_page(
        callback,
        "audio"
    )

    await callback.answer()


@dp.callback_query(F.data == "video")
async def video_callback(
    callback: CallbackQuery
):

    await show_function_page(
        callback,
        "video"
    )

    await callback.answer()


@dp.callback_query(F.data == "photos")
async def photos_callback(
    callback: CallbackQuery
):

    await show_function_page(
        callback,
        "photos"
    )

    await callback.answer()


@dp.callback_query(F.data == "files")
async def files_callback(
    callback: CallbackQuery
):

    await show_function_page(
        callback,
        "files"
    )

    await callback.answer()


@dp.callback_query(F.data == "stickers")
async def stickers_callback(
    callback: CallbackQuery
):

    await show_function_page(
        callback,
        "stickers"
    )

    await callback.answer()


# =========================================================
# ENABLE / DISABLE FUNCTIONS
# =========================================================

@dp.callback_query(F.data.startswith("enable:"))
async def enable_function_callback(
    callback: CallbackQuery
):

    function_name = callback.data.split(
        ":",
        1
    )[1]

    settings = get_settings(
        callback.from_user.id
    )

    if function_name not in settings:

        await callback.answer(
            "Неизвестная функция.",
            show_alert=True
        )

        return

    settings[function_name] = True

    if function_name == "offline":

        await show_offline_page(callback)

    else:

        await show_function_page(
            callback,
            function_name
        )

    await callback.answer(
        "🟢 Функция включена!"
    )


@dp.callback_query(F.data.startswith("disable:"))
async def disable_function_callback(
    callback: CallbackQuery
):

    function_name = callback.data.split(
        ":",
        1
    )[1]

    settings = get_settings(
        callback.from_user.id
    )

    if function_name not in settings:

        await callback.answer(
            "Неизвестная функция.",
            show_alert=True
        )

        return

    settings[function_name] = False

    if function_name == "offline":

        await show_offline_page(callback)

    else:

        await show_function_page(
            callback,
            function_name
        )

    await callback.answer(
        "🔴 Функция выключена!"
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@dp.callback_query(F.data == "notifications")
async def notifications_callback(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "🔔 Уведомления\n\n"
        "Выберите, какие события должны "
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


# =========================================================
# OFFLINE AUTO-REPLY
# =========================================================

async def show_offline_page(
    callback: CallbackQuery
):

    settings = get_settings(
        callback.from_user.id
    )

    await callback.message.edit_text(
        "📴 Оффлайн-ответ\n\n"
        "TelegaOn сможет отправлять "
        "автоматический ответ, когда "
        "вы будете не в сети.\n\n"
        f"Статус: "
        f"{status_text(settings['offline'])}\n\n"
        "Текущий ответ:\n"
        f"«{settings['offline_text']}»",
        reply_markup=function_controls(
            "offline",
            settings["offline"],
            can_edit=True
        )
    )


@dp.callback_query(F.data == "offline")
async def offline_callback(
    callback: CallbackQuery
):

    await show_offline_page(callback)

    await callback.answer()


@dp.callback_query(F.data == "edit:offline")
async def edit_offline_callback(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    waiting_for_offline_text.add(
        user_id
    )

    user_menu_messages[user_id] = {
        "chat_id": callback.message.chat.id,
        "message_id": callback.message.message_id
    }

    await callback.message.edit_text(
        "✏️ Изменение оффлайн-ответа\n\n"
        "Отправьте следующим сообщением "
        "новый текст автоответа.",
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================================================
# BAN WORDS
# =========================================================

@dp.callback_query(F.data == "banwords")
async def banwords_callback(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "🚫 Бан-слова\n\n"
        "Сейчас эта функция недоступна "
        "или находится в бета-тесте.\n\n"
        "Информация будет позже.",
        reply_markup=back_to_settings()
    )

    await callback.answer()


# =========================================================
# STAFF MENU
# =========================================================

def staff_menu(user_id: int):

    kb = InlineKeyboardBuilder()

    kb.button(
        text="👑 Список админов",
        callback_data="admins"
    )

    kb.button(
        text="🧪 Список тестеров",
        callback_data="testers"
    )

    # Добавлять админов может только владелец.
    if is_owner(user_id):

        kb.button(
            text="➕ Добавить админа",
            callback_data="add_admin"
        )

    # Админы тоже могут добавлять тестеров.
    if is_admin(user_id):

        kb.button(
            text="➕ Добавить тестера",
            callback_data="add_tester"
        )

    kb.button(
        text="◀️ Назад",
        callback_data="main"
    )

    kb.adjust(1)

    return kb.as_markup()


@dp.callback_query(F.data == "staff")
async def staff_callback(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    if not is_admin(user_id):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "👥 Админы и тестеры\n\n"
        "Здесь можно управлять "
        "администраторами и участниками "
        "бета-тестирования.",
        reply_markup=staff_menu(user_id)
    )

    await callback.answer()


# =========================================================
# ADMIN LIST
# =========================================================

@dp.callback_query(F.data == "admins")
async def admins_callback(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True
        )

        return

    admins = get_users_by_role("admin")

    text = "👑 Администраторы\n\n"

    if not admins:

        text += "Пока нет добавленных администраторов."

    else:

        for index, user in enumerate(
            admins,
            start=1
        ):

            username = user.get("username")

            if username:
                name = f"@{username}"

            else:
                name = user.get(
                    "full_name",
                    str(user["telegram_id"])
                )

            text += f"{index}. {name}\n"

    await callback.message.edit_text(
        text,
        reply_markup=staff_menu(
            callback.from_user.id
        )
    )

    await callback.answer()


# =========================================================
# TESTER LIST
# =========================================================

@dp.callback_query(F.data == "testers")
async def testers_callback(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True
        )

        return

    testers = get_users_by_role("tester")

    text = "🧪 Тестеры\n\n"

    if not testers:

        text += "Пока нет добавленных тестеров."

    else:

        for index, user in enumerate(
            testers,
            start=1
        ):

            username = user.get("username")

            if username:
                name = f"@{username}"

            else:
                name = user.get(
                    "full_name",
                    str(user["telegram_id"])
                )

            text += f"{index}. {name}\n"

    await callback.message.edit_text(
        text,
        reply_markup=staff_menu(
            callback.from_user.id
        )
    )

    await callback.answer()


# =========================================================
# ADD ADMIN
# =========================================================

@dp.callback_query(F.data == "add_admin")
async def add_admin_callback(
    callback: CallbackQuery
):

    if not is_owner(callback.from_user.id):

        await callback.answer(
            "⛔ Только владелец может добавлять админов.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "➕ Добавление администратора\n\n"
        "Для добавления пользователя отправьте "
        "его Telegram ID отдельным сообщением.\n\n"
        "Пример:\n"
        "`123456789`\n\n"
        "После этого мы автоматически выдадим "
        "ему роль администратора.",
        reply_markup=back_to_main(
            callback.from_user.id
        ),
        parse_mode="Markdown"
    )

    await callback.answer()


# =========================================================
# ADD TESTER
# =========================================================

@dp.callback_query(F.data == "add_tester")
async def add_tester_callback(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Только админы могут добавлять тестеров.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "🧪 Добавление тестера\n\n"
        "Для добавления пользователя отправьте "
        "его Telegram ID отдельным сообщением.\n\n"
        "Пример:\n"
        "`123456789`\n\n"
        "После добавления пользователь получит "
        "доступ к бета-функциям.",
        reply_markup=back_to_main(
            callback.from_user.id
        ),
        parse_mode="Markdown"
    )

    await callback.answer()


# =========================================================
# BUSINESS CONNECTION
# =========================================================

@dp.business_connection()
async def business_connection_handler(
    connection: BusinessConnection
):

    logger.info("========================================")
    logger.info("📡 BUSINESS CONNECTION UPDATE")

    logger.info(
        "Connection ID: %s",
        connection.id
    )

    logger.info(
        "Business user ID: %s",
        connection.user.id
    )

    logger.info(
        "User name: %s",
        connection.user.full_name
    )

    logger.info(
        "Username: @%s",
        connection.user.username
    )

    logger.info(
        "Enabled: %s",
        connection.is_enabled
    )

    save_business_connection(connection)

    logger.info("========================================")


# =========================================================
# BUSINESS MESSAGE
# =========================================================

@dp.business_message()
async def business_message_handler(
    message: Message
):

    logger.info("========================================")
    logger.info("📨 NEW BUSINESS MESSAGE")

    logger.info(
        "Message ID: %s",
        message.message_id
    )

    logger.info(
        "Chat ID: %s",
        message.chat.id
    )

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

        logger.info(
            "Text: %s",
            message.text
        )

    save_business_message(message)

    logger.info("========================================")


# =========================================================
# EDITED BUSINESS MESSAGE
# =========================================================

@dp.edited_business_message()
async def edited_business_message_handler(
    message: Message
):

    logger.info("========================================")
    logger.info("✏️ EDITED BUSINESS MESSAGE")

    logger.info(
        "Message ID: %s",
        message.message_id
    )

    logger.info(
        "Chat ID: %s",
        message.chat.id
    )

    logger.info(
        "Business Connection ID: %s",
        message.business_connection_id
    )

    if message.text:

        logger.info(
            "New text: %s",
            message.text
        )

    save_business_message(message)

    logger.info("========================================")


# =========================================================
# DELETED BUSINESS MESSAGES
# =========================================================

@dp.deleted_business_messages()
async def deleted_business_messages_handler(
    event
):

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
# STAFF HELP
# =========================================================

@dp.callback_query(F.data == "staff_help")
async def staff_help_callback(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "🧑‍💻 Помощь сотрудников\n\n"
        "Функция находится в бета-тесте.\n\n"
        "Информация будет позже.",
        reply_markup=back_to_main(
            callback.from_user.id
        )
    )

    await callback.answer()


# =========================================================
# HTTP SERVER
# =========================================================

async def health(request):

    return web.Response(
        text="TelegaOn is running!"
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get(
        "/",
        health
    )

    app.router.add_get(
        "/health",
        health
    )

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
# START BOT
# =========================================================

async def main():

    await start_web_server()

    # Проверяем подключение к Supabase.
    try:

        (
            supabase
            .table("users")
            .select("telegram_id")
            .limit(1)
            .execute()
        )

        logger.info(
            "🗄️ Supabase подключён успешно!"
        )

    except Exception:

        logger.exception(
            "❌ Не удалось подключиться к Supabase"
        )

    logger.info(
        "🤖 TelegaOn started!"
    )

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
