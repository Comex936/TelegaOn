import asyncio
import logging
import os
from collections import defaultdict
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Переменная BOT_TOKEN не установлена")

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()


# =========================================================
# ВРЕМЕННОЕ ХРАНИЛИЩЕ
# =========================================================
# Позже заменим это на Supabase.
#
# users[user_id] = {
#     "username": "...",
#     "name": "...",
#     "balance": 1000,
# }

users = {}

# История операций
history = defaultdict(list)

# Язык пользователя
languages = defaultdict(lambda: "ru")


# =========================================================
# БАЗОВЫЕ ФУНКЦИИ
# =========================================================

START_BALANCE = 1000


def get_user(tg_user):
    """
    Создаёт игрока при первом взаимодействии.
    """

    user_id = tg_user.id

    if user_id not in users:
        users[user_id] = {
            "username": tg_user.username,
            "name": tg_user.first_name or "Игрок",
            "balance": START_BALANCE,
        }

        history[user_id].append({
            "type": "bonus",
            "amount": START_BALANCE,
            "description": "Стартовый баланс",
            "date": datetime.now(),
        })

    else:
        # Обновляем данные Telegram-профиля
        users[user_id]["username"] = tg_user.username
        users[user_id]["name"] = tg_user.first_name or "Игрок"

    return users[user_id]


def get_username(user):
    if user.get("username"):
        return f"@{user['username']}"

    return user["name"]


def add_history(
    user_id: int,
    operation_type: str,
    amount: int,
    description: str,
):
    history[user_id].append({
        "type": operation_type,
        "amount": amount,
        "description": description,
        "date": datetime.now(),
    })


def change_balance(
    user_id: int,
    amount: int,
    operation_type: str,
    description: str,
):
    users[user_id]["balance"] += amount

    add_history(
        user_id,
        operation_type,
        amount,
        description,
    )


# =========================================================
# /start
# =========================================================

@dp.message(Command("start"))
async def start(message: Message):
    user = get_user(message.from_user)

    await message.answer(
        "🎰 <b>Добро пожаловать в игровой бот!</b>\n\n"
        f"💰 Твой баланс: <b>{user['balance']:,} BON</b>\n\n"
        "Используй <b>б</b> или <b>баланс</b>, "
        "чтобы проверить баланс.",
        parse_mode="HTML",
    )


# =========================================================
# БАЛАНС
# =========================================================

async def show_balance(message: Message):
    user = get_user(message.from_user)

    await message.answer(
        f"💰 <b>Твой баланс:</b> {user['balance']:,} BON",
        parse_mode="HTML",
    )


@dp.message(
    F.text.lower().in_({
        "б",
        "баланс",
    })
)
async def balance(message: Message):
    await show_balance(message)


@dp.message(Command("balance"))
async def balance_command(message: Message):
    await show_balance(message)


# =========================================================
# ПРОФИЛЬ
# =========================================================

@dp.message(Command("профиль"))
async def profile(message: Message):
    user = get_user(message.from_user)

    username = get_username(user)

    await message.answer(
        "👤 <b>Профиль</b>\n\n"
        f"Игрок: <b>{username}</b>\n"
        f"💰 Баланс: <b>{user['balance']:,} BON</b>",
        parse_mode="HTML",
    )


# =========================================================
# ПЕРЕВОДЫ
# =========================================================

def parse_amount(value: str):
    try:
        amount = int(value)

        if amount <= 0:
            return None

        return amount

    except ValueError:
        return None


async def transfer(
    message: Message,
    target_id: int,
    amount: int,
):
    sender = get_user(message.from_user)

    if target_id == message.from_user.id:
        await message.reply(
            "❌ Нельзя перевести BON самому себе."
        )
        return

    if amount <= 0:
        await message.reply(
            "❌ Сумма должна быть больше нуля."
        )
        return

    if sender["balance"] < amount:
        await message.reply(
            "❌ Недостаточно BON."
        )
        return

    # Получатель
    if target_id not in users:
        users[target_id] = {
            "username": None,
            "name": "Игрок",
            "balance": 0,
        }

    receiver = users[target_id]

    sender["balance"] -= amount
    receiver["balance"] += amount

    add_history(
        message.from_user.id,
        "transfer",
        -amount,
        f"Перевод пользователю {get_username(receiver)}",
    )

    add_history(
        target_id,
        "transfer",
        amount,
        f"Получено от {get_username(sender)}",
    )

    await message.answer(
        "💸 <b>Перевод выполнен!</b>\n\n"
        f"👤 Отправитель: {get_username(sender)}\n"
        f"👤 Получатель: {get_username(receiver)}\n"
        f"💰 Сумма: <b>{amount:,} BON</b>",
        parse_mode="HTML",
    )


# ---------------------------------------------------------
# Перевод ответом:
#
# п 500
#
# ---------------------------------------------------------

@dp.message(F.text)
async def reply_transfer(message: Message):
    text = message.text.strip()

    if not text.lower().startswith("п "):
        return

    if not message.reply_to_message:
        return

    parts = text.split()

    if len(parts) != 2:
        await message.reply(
            "❌ Использование:\n"
            "<code>п 500</code>\n\n"
            "Команду нужно написать ответом на сообщение.",
            parse_mode="HTML",
        )
        return

    amount = parse_amount(parts[1])

    if amount is None:
        await message.reply(
            "❌ Укажи корректную сумму."
        )
        return

    target = message.reply_to_message.from_user

    # Регистрируем получателя
    get_user(target)

    await transfer(
        message,
        target.id,
        amount,
    )


# ---------------------------------------------------------
# Перевод по ID:
#
# п 123456789 500
#
# ---------------------------------------------------------

@dp.message(F.text)
async def id_transfer(message: Message):
    text = message.text.strip()

    if not text.lower().startswith("п "):
        return

    if message.reply_to_message:
        return

    parts = text.split()

    if len(parts) != 3:
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.reply(
            "❌ ID пользователя должен быть числом."
        )
        return

    amount = parse_amount(parts[2])

    if amount is None:
        await message.reply(
            "❌ Укажи корректную сумму."
        )
        return

    await transfer(
        message,
        target_id,
        amount,
    )


# =========================================================
# /ИСТОРИЯ
# =========================================================

@dp.message(Command("история"))
async def history_command(message: Message):
    get_user(message.from_user)

    records = history[message.from_user.id]

    if not records:
        await message.answer(
            "📜 История пока пуста."
        )
        return

    records = records[-10:]

    text = "📜 <b>Последние операции</b>\n\n"

    for record in reversed(records):
        amount = record["amount"]

        if amount > 0:
            amount_text = f"+{amount:,}"
        else:
            amount_text = f"{amount:,}"

        text += (
            f"• {record['description']}\n"
            f"  💰 {amount_text} BON\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


# =========================================================
# TOP
# =========================================================

async def show_top(message: Message, amount: int):
    get_user(message.from_user)

    amount = max(1, min(amount, 50))

    sorted_users = sorted(
        users.items(),
        key=lambda item: item[1]["balance"],
        reverse=True,
    )

    text = "🏆 <b>ТОП игроков</b>\n\n"

    for position, (user_id, user) in enumerate(
        sorted_users[:amount],
        start=1,
    ):
        text += (
            f"<b>{position}.</b> "
            f"{get_username(user)} — "
            f"💰 {user['balance']:,} BON\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


@dp.message(Command("top"))
async def top_command(message: Message):
    parts = message.text.split()

    amount = 10

    if len(parts) > 1:
        try:
            amount = int(parts[1])
        except ValueError:
            await message.reply(
                "❌ Количество должно быть числом."
            )
            return

    await show_top(message, amount)


# =========================================================
# ЯЗЫК
# =========================================================

@dp.message(Command("lang"))
async def lang_command(message: Message):
    parts = message.text.split()

    if len(parts) != 2:
        await message.answer(
            "🌐 Выбери язык:\n\n"
            "/lang ru\n"
            "/lang uk\n"
            "/lang en"
        )
        return

    lang = parts[1].lower()

    if lang not in {"ru", "uk", "en"}:
        await message.answer(
            "❌ Доступные языки: ru, uk, en."
        )
        return

    languages[message.from_user.id] = lang

    names = {
        "ru": "русский 🇷🇺",
        "uk": "українська 🇺🇦",
        "en": "English 🇬🇧",
    }

    await message.answer(
        f"🌐 Язык изменён на {names[lang]}."
    )


# =========================================================
# МИННОЕ ПОЛЕ
# =========================================================

@dp.message(
    F.text.lower().regexp(r"^мины\s+\d+$")
)
async def mines(message: Message):
    user = get_user(message.from_user)

    parts = message.text.split()

    bet = int(parts[1])

    if bet <= 0:
        await message.reply(
            "❌ Ставка должна быть больше нуля."
        )
        return

    if user["balance"] < bet:
        await message.reply(
            "❌ Недостаточно BON."
        )
        return

    # Пока только интерфейс.
    # Игровую механику подключим следующим этапом.

    user["balance"] -= bet

    add_history(
        message.from_user.id,
        "game",
        -bet,
        "Ставка в минном поле",
    )

    keyboard = []

    row = []

    for number in range(1, 30):
        row.append(
            InlineKeyboardButton(
                text="❓",
                callback_data=f"mine:{message.from_user.id}:{number}",
            )
        )

        if len(row) == 5:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    await message.answer(
        f"💣 <b>{get_username(user)}, вы начали игру "
        f"минное поле!</b>\n\n"
        f"💰 Ставка: <b>{bet:,} BON</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )


# =========================================================
# ЗАГЛУШКА КНОПОК МИННОГО ПОЛЯ
# =========================================================

@dp.callback_query(F.data.startswith("mine:"))
async def mine_button(callback: CallbackQuery):
    await callback.answer(
        "🚧 Механика минного поля будет добавлена следующим этапом.",
        show_alert=True,
    )


# =========================================================
# ДЖОКЕР
# =========================================================

@dp.message(
    F.text.lower().regexp(r"^джокер\s+\d+$")
)
async def joker(message: Message):
    user = get_user(message.from_user)

    parts = message.text.split()

    bet = int(parts[1])

    if bet <= 0:
        await message.reply(
            "❌ Ставка должна быть больше нуля."
        )
        return

    if user["balance"] < bet:
        await message.reply(
            "❌ Недостаточно BON."
        )
        return

    user["balance"] -= bet

    add_history(
        message.from_user.id,
        "game",
        -bet,
        "Ставка в Джокере",
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text="❓",
                callback_data=f"joker:{message.from_user.id}:1",
            ),
            InlineKeyboardButton(
                text="❓",
                callback_data=f"joker:{message.from_user.id}:2",
            ),
            InlineKeyboardButton(
                text="❓",
                callback_data=f"joker:{message.from_user.id}:3",
            ),
        ]
    ]

    await message.answer(
        f"🃏 <b>{get_username(user)}, вы начали игру Джокер!</b>\n\n"
        f"💰 Ставка: <b>{bet:,} BON</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML",
    )


# =========================================================
# CALLBACK ДЖОКЕРА
# =========================================================

@dp.callback_query(F.data.startswith("joker:"))
async def joker_button(callback: CallbackQuery):
    await callback.answer(
        "🚧 Механика Джокера будет добавлена следующим этапом.",
        show_alert=True,
    )


# =========================================================
# ЗАПУСК
# =========================================================

async def main():
    logging.info("запускается...")

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
