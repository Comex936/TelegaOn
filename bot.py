```python
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
```
