import asyncio
import logging
from typing import List, Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings

logger = logging.getLogger(__name__)

async def send_stream_reminder_notification(
    bot: Bot,
    telegram_id: int,
    stream_title: str,
    game_category: str,
    platform: str,
    platform_url: str,
    minutes_left: int = 15
) -> bool:
    """Sends a stream reminder to a viewer via Telegram bot."""
    try:
        text = (
            f"⏰ <b>Напоминание о стриме!</b>\n\n"
            f"🎬 <b>{stream_title}</b>\n"
            f"🎮 <i>Категория: {game_category}</i>\n"
            f"📡 <i>Платформа: {platform}</i>\n\n"
            f"⏳ Трансляция начнется через <b>{minutes_left} минут</b>!\n"
            f"Готовьте чай и вкусняшки! ☕️🍿"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"📺 Открыть {platform}", url=platform_url)
            ],
            [
                InlineKeyboardButton(text="📱 Открыть Mini App", web_app=WebAppInfo(url=settings.WEBAPP_URL))
            ]
        ])
        await bot.send_message(chat_id=telegram_id, text=text, reply_markup=keyboard)
        return True
    except Exception as e:
        logger.error(f"Failed to send stream reminder to {telegram_id}: {e}")
        return False


async def send_suggestion_reply_notification(
    bot: Bot,
    telegram_id: int,
    suggestion_title: str,
    status_text: str,
    admin_reply: Optional[str] = None
) -> bool:
    """Sends a notification when streamer moderates or replies to viewer's suggestion."""
    try:
        status_emoji = "✅" if status_text == "accepted" else ("❌" if status_text == "rejected" else "💬")
        status_label = "Взято на стрим!" if status_text == "accepted" else ("Отклонено" if status_text == "rejected" else "Отвечено")

        text = (
            f"{status_emoji} <b>Стример ответил на вашу идею!</b>\n\n"
            f"💡 <b>Идея / Вопрос:</b>\n<i>«{suggestion_title}»</i>\n\n"
            f"📌 <b>Статус:</b> <b>{status_label}</b>\n"
        )
        if admin_reply:
            text += f"\n💬 <b>Ответ стримера:</b>\n<i>«{admin_reply}»</i>\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💡 Открыть предложку", web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}#suggestions"))
            ]
        ])
        await bot.send_message(chat_id=telegram_id, text=text, reply_markup=keyboard)
        return True
    except Exception as e:
        logger.error(f"Failed to send suggestion reply to {telegram_id}: {e}")
        return False


async def send_stream_live_broadcast(
    bot: Bot,
    users_ids: List[int],
    stream_title: str,
    game_category: str,
    platform: str,
    platform_url: str
) -> dict:
    """Broadcasts a 'Stream is Live' notification to subscribed users."""
    text = (
        f"🔴 <b>СТРИМ НАЧАЛСЯ! В ЭФИРЕ!</b> 🔴\n\n"
        f"🎮 <b>{stream_title}</b>\n"
        f"🏷 <i>Категория: {game_category}</i>\n"
        f"📺 <i>Платформа: {platform}</i>\n\n"
        f"Залетайте на трансляцию, стример уже в сети! 🔥"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🔥 Смотреть на {platform}", url=platform_url)
        ],
        [
            InlineKeyboardButton(text="📱 Открыть Mini App", web_app=WebAppInfo(url=settings.WEBAPP_URL))
        ]
    ])

    success_count = 0
    failed_count = 0

    for uid in users_ids:
        try:
            await bot.send_message(chat_id=uid, text=text, reply_markup=keyboard)
            success_count += 1
            await asyncio.sleep(0.05)  # Rate limiting
        except Exception as e:
            failed_count += 1
            logger.warning(f"Live broadcast failed for user {uid}: {e}")

    return {"sent_count": success_count, "failed_count": failed_count}


async def send_custom_broadcast(
    bot: Bot,
    users_ids: List[int],
    title: str,
    content: str,
    image_url: Optional[str] = None,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None
) -> dict:
    """Sends custom announcement broadcast to all subscribed users."""
    text = f"📢 <b>{title}</b>\n\n{content}"
    
    inline_buttons = []
    if button_text and button_url:
        inline_buttons.append([InlineKeyboardButton(text=button_text, url=button_url)])
    inline_buttons.append([InlineKeyboardButton(text="📱 Открыть Mini App", web_app=WebAppInfo(url=settings.WEBAPP_URL))])
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)

    success_count = 0
    failed_count = 0

    for uid in users_ids:
        try:
            if image_url:
                await bot.send_photo(chat_id=uid, photo=image_url, caption=text, reply_markup=keyboard)
            else:
                await bot.send_message(chat_id=uid, text=text, reply_markup=keyboard)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed_count += 1
            logger.warning(f"Broadcast failed for user {uid}: {e}")

    return {"sent_count": success_count, "failed_count": failed_count}
