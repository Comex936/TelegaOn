import asyncio
import logging
import os
import re
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не найдена переменная BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()


# ============================================================
# ROLES
# ============================================================

RANK_NAMES = {
    0: "Участник",
    1: "Младший модератор",
    2: "Модератор",
    3: "Младший админ",
    4: "Админ",
    5: "Владелец",
}

# Временное хранилище.
# Позже здесь будет Supabase.
ranks = {}
warnings = {}
mutes = {}
bans = {}


# ============================================================
# HELPERS
# ============================================================

def key(chat_id: int, user_id: int):
    return chat_id, user_id


def get_rank(chat_id: int, user_id: int) -> int:
    return ranks.get(key(chat_id, user_id), 0)


def set_rank(chat_id: int, user_id: int, rank: int):
    ranks[key(chat_id, user_id)] = rank


def mention(user):
    if user.username:
        return f"@{user.username}"

    return user.first_name


def parse_duration(text: str | None):
    """
    Поддерживает:

    30с
    10м
    2ч
    7д
    2н
    """

    if not text:
        return None

    text = text.lower().strip()

    match = re.fullmatch(
        r"(\d+)\s*(с|сек|м|мин|ч|час|д|дн|н|нед)",
        text
    )

    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit in ("с", "сек"):
        delta = timedelta(seconds=amount)

    elif unit in ("м", "мин"):
        delta = timedelta(minutes=amount)

    elif unit in ("ч", "час"):
        delta = timedelta(hours=amount)

    elif unit in ("д", "дн"):
        delta = timedelta(days=amount)

    elif unit in ("н", "нед"):
        delta = timedelta(weeks=amount)

    else:
        return None

    return datetime.now(timezone.utc) + delta


def duration_text(date):
    if date is None:
        return "навсегда"

    return date.strftime("%d.%m.%Y %H:%M UTC")


async def get_target(message: Message, args: list[str]):
    """
    Приоритет:

    1. Ответ на сообщение
    2. @username

    Telegram не позволяет боту надёжно получить
    любого пользователя только по username,
    поэтому reply является предпочтительным способом.
    """

    if message.reply_to_message:
        return message.reply_to_message.from_user

    if not args:
        return None

    username = args[0]

    if not username.startswith("@"):
        return None

    username = username[1:].lower()

    # Ищем среди известных пользователей этого чата.
    for (chat_id, user_id), rank in ranks.items():
        if chat_id != message.chat.id:
            continue

        try:
            member = await bot.get_chat_member(
                message.chat.id,
                user_id
            )

            if (
                member.user.username
                and member.user.username.lower() == username
            ):
                return member.user

        except Exception:
            pass

    return None


async def can_manage(
    message: Message,
    target_id: int,
    minimum_rank: int = 1
):
    actor_rank = get_rank(
        message.chat.id,
        message.from_user.id
    )

    target_rank = get_rank(
        message.chat.id,
        target_id
    )

    if actor_rank < minimum_rank:
        await message.reply(
            f"❌ Недостаточно прав.\n"
            f"Требуется: {minimum_rank} — "
            f"{RANK_NAMES[minimum_rank]}"
        )
        return False

    if target_id == message.from_user.id:
        await message.reply(
            "❌ Нельзя применить это действие к себе."
        )
        return False

    if target_rank >= actor_rank:
        await message.reply(
            "❌ Нельзя управлять пользователем "
            "с равным или более высоким рангом."
        )
        return False

    return True


# ============================================================
# START
# ============================================================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 <b>EcstaZy</b>\n\n"
        "Помощник администрации.\n\n"
        f"Твой ранг: "
        f"<b>{RANK_NAMES[get_rank(message.chat.id, message.from_user.id)]}</b>",
        parse_mode="HTML"
    )


# ============================================================
# /rank
# ============================================================

@dp.message(Command("rank"))
async def rank_command(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя через @username "
            "или ответь на его сообщение."
        )
        return

    if message.reply_to_message:
        if not args:
            await message.reply(
                "❌ Укажи ранг от 1 до 5.\n"
                "Пример: <code>/rank 2</code>",
                parse_mode="HTML"
            )
            return

        rank_arg = args[0]

    else:
        if len(args) < 2:
            await message.reply(
                "❌ Использование:\n"
                "<code>/rank @username 2</code>",
                parse_mode="HTML"
            )
            return

        rank_arg = args[1]

    if not rank_arg.isdigit():
        await message.reply("❌ Ранг должен быть числом от 1 до 5.")
        return

    new_rank = int(rank_arg)

    if new_rank < 1 or new_rank > 5:
        await message.reply("❌ Ранг должен быть от 1 до 5.")
        return

    actor_rank = get_rank(
        message.chat.id,
        message.from_user.id
    )

    if actor_rank <= new_rank:
        await message.reply(
            "❌ Нельзя выдать ранг, равный или выше своего."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    set_rank(
        message.chat.id,
        target.id,
        new_rank
    )

    await message.answer(
        f"🎖 {mention(target)} получает ранг "
        f"<b>{new_rank} — {RANK_NAMES[new_rank]}</b>.",
        parse_mode="HTML"
    )


# ============================================================
# /promote
# ============================================================

@dp.message(Command("promote"))
async def promote(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на его сообщение."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    current = get_rank(message.chat.id, target.id)

    if current >= 5:
        await message.reply("❌ У пользователя максимальный ранг.")
        return

    new_rank = current + 1
    actor_rank = get_rank(
        message.chat.id,
        message.from_user.id
    )

    if new_rank >= actor_rank:
        await message.reply(
            "❌ Нельзя повысить пользователя "
            "до своего ранга или выше."
        )
        return

    set_rank(
        message.chat.id,
        target.id,
        new_rank
    )

    await message.answer(
        f"⬆️ {mention(target)} повышен.\n\n"
        f"{current} — {RANK_NAMES[current]}\n"
        f"⬇️\n"
        f"{new_rank} — {RANK_NAMES[new_rank]}"
    )


# ============================================================
# /demote
# ============================================================

@dp.message(Command("demote"))
async def demote(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на его сообщение."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    current = get_rank(message.chat.id, target.id)

    if current <= 1:
        await message.reply(
            "❌ Минимальный ранг для администрации — 1."
        )
        return

    new_rank = current - 1

    set_rank(
        message.chat.id,
        target.id,
        new_rank
    )

    await message.answer(
        f"⬇️ {mention(target)} понижен.\n\n"
        f"{current} — {RANK_NAMES[current]}\n"
        f"⬇️\n"
        f"{new_rank} — {RANK_NAMES[new_rank]}"
    )


# ============================================================
# /unrank
# ============================================================

@dp.message(Command("unrank"))
async def unrank(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на его сообщение."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    set_rank(
        message.chat.id,
        target.id,
        0
    )

    await message.answer(
        f"👤 С {mention(target)} снят ранг."
    )


# ============================================================
# /warn
# ============================================================

@dp.message(Command("warn"))
async def warn(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на сообщение."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    if message.reply_to_message:
        data = args
    else:
        data = args[1:]

    duration = None

    if data and parse_duration(data[-1]):
        duration = parse_duration(data.pop())

    reason = " ".join(data)

    if not reason:
        reason = "Не указана"

    user_key = key(message.chat.id, target.id)

    if user_key not in warnings:
        warnings[user_key] = []

    warnings[user_key].append({
        "reason": reason,
        "expires": duration
    })

    count = len(warnings[user_key])

    await message.answer(
        f"⚠️ {mention(target)} получает варн.\n\n"
        f"Причина: <b>{reason}</b>\n"
        f"Срок: <b>{duration_text(duration)}</b>\n"
        f"Всего варнов: <b>{count}</b>",
        parse_mode="HTML"
    )


# ============================================================
# /unwarn
# ============================================================

@dp.message(Command("unwarn"))
async def unwarn(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на сообщение."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    user_key = key(message.chat.id, target.id)

    if user_key not in warnings or not warnings[user_key]:
        await message.reply("❌ У пользователя нет варнов.")
        return

    amount = 1

    if args:
        last = args[-1]

        if last.isdigit():
            amount = int(last)

    if amount <= 0:
        await message.reply("❌ Некорректное количество.")
        return

    if amount >= len(warnings[user_key]):
        removed = len(warnings[user_key])
        warnings[user_key].clear()
    else:
        removed = amount

        for _ in range(amount):
            warnings[user_key].pop()

    await message.answer(
        f"✅ С {mention(target)} снято варнов: <b>{removed}</b>.",
        parse_mode="HTML"
    )


# ============================================================
# /mute
# ============================================================

@dp.message(Command("mute"))
async def mute(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на сообщение."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    if message.reply_to_message:
        data = args
    else:
        data = args[1:]

    duration = None

    if data and parse_duration(data[-1]):
        duration = parse_duration(data.pop())

    reason = " ".join(data) or "Не указана"

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            permissions={
                "can_send_messages": False
            },
            until_date=duration
        )

    except Exception as e:
        logging.error(e)

        await message.reply(
            "❌ Не удалось выдать мут.\n"
            "Проверь, что EcstaZy — администратор "
            "и имеет право ограничивать участников."
        )
        return

    mutes[key(message.chat.id, target.id)] = {
        "reason": reason,
        "expires": duration
    }

    await message.answer(
        f"🔇 {mention(target)} получил мут.\n\n"
        f"Причина: <b>{reason}</b>\n"
        f"До: <b>{duration_text(duration)}</b>",
        parse_mode="HTML"
    )


# ============================================================
# /unmute
# ============================================================

@dp.message(Command("unmute"))
async def unmute(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на сообщение."
        )
        return

    if not await can_manage(message, target.id, 1):
        return

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            permissions={
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_video_notes": True,
                "can_send_voice_notes": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True
            }
        )

    except Exception as e:
        logging.error(e)

        await message.reply("❌ Не удалось снять мут.")
        return

    mutes.pop(
        key(message.chat.id, target.id),
        None
    )

    await message.answer(
        f"🔊 {mention(target)} снова может разговаривать."
    )


# ============================================================
# /ban
# ============================================================

@dp.message(Command("ban"))
async def ban(message: Message):
    args = message.text.split()[1:]

    target = await get_target(message, args)

    if not target:
        await message.reply(
            "❌ Укажи пользователя или ответь на сообщение."
        )
        return

    if not await can_manage(message, target.id, 2):
        return

    if message.reply_to_message:
        data = args
    else:
        data = args[1:]

    duration = None

    if data and parse_duration(data[-1]):
        duration = parse_duration(data.pop())

    reason = " ".join(data) or "Не указана"

    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            until_date=duration
        )

    except Exception as e:
        logging.error(e)

        await message.reply(
            "❌ Не удалось заблокировать пользователя."
        )
        return

    bans[key(message.chat.id, target.id)] = {
        "reason": reason,
        "expires": duration
    }

    await message.answer(
        f"🔨 {mention(target)} заблокирован.\n\n"
        f"Причина: <b>{reason}</b>\n"
        f"До: <b>{duration_text(duration)}</b>",
        parse_mode="HTML"
    )


# ============================================================
# /unban
# ============================================================

@dp.message(Command("unban"))
async def unban(message: Message):
    args = message.text.split()[1:]

    if not args:
        await message.reply(
            "❌ Укажи @username."
        )
        return

    username = args[0].lstrip("@")

    actor_rank = get_rank(
        message.chat.id,
        message.from_user.id
    )

    if actor_rank < 2:
        await message.reply(
            "❌ Для разбана нужен ранг 2+."
        )
        return

    # Ищем среди сохранённых банов.
    target_id = None

    for (chat_id, user_id), data in bans.items():
        if chat_id != message.chat.id:
            continue

        try:
            member = await bot.get_chat_member(
                message.chat.id,
                user_id
            )

            if (
                member.user.username
                and member.user.username.lower() == username.lower()
            ):
                target_id = user_id
                target = member.user
                break

        except Exception:
            pass

    if target_id is None:
        await message.reply(
            "❌ Не удалось найти этого пользователя.\n"
            "Для разбана лучше использовать username "
            "пользователя, который был забанен EcstaZy."
        )
        return

    target_rank = get_rank(
        message.chat.id,
        target_id
    )

    if target_rank >= actor_rank:
        await message.reply(
            "❌ Нельзя управлять пользователем "
            "с равным или более высоким рангом."
        )
        return

    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_id
        )

    except Exception as e:
        logging.error(e)

        await message.reply("❌ Не удалось разбанить пользователя.")
        return

    bans.pop(
        key(message.chat.id, target_id),
        None
    )

    await message.answer(
        f"✅ {mention(target)} разбанен."
    )


# ============================================================
# RUN
# ============================================================

async def main():
    print("EcstaZy запущен.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
