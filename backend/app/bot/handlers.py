from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy.future import select
from sqlalchemy import func

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import User, Stream, Suggestion, StreamerProfile

router = Router()

async def get_main_menu_keyboard(db):
    prof_res = await db.execute(select(StreamerProfile).where(StreamerProfile.id == 1))
    prof = prof_res.scalars().first()
    
    webapp_url = settings.WEBAPP_URL
    if not webapp_url or "your-domain.com" in webapp_url:
        webapp_url = "https://nekomini.onrender.com"

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 Открыть Mini App",
                web_app=WebAppInfo(url=webapp_url)
            )
        ],
        [
            InlineKeyboardButton(text="📅 Расписание", callback_data="btn_schedule"),
            InlineKeyboardButton(text="💡 Предложка", callback_data="btn_suggest")
        ]
    ]

    social_row = []
    if prof and prof.twitch_url:
        social_row.append(InlineKeyboardButton(text="📺 Twitch", url=prof.twitch_url))
    elif settings.TWITCH_URL and "streamer" not in settings.TWITCH_URL:
        social_row.append(InlineKeyboardButton(text="📺 Twitch", url=settings.TWITCH_URL))

    if prof and prof.telegram_channel:
        social_row.append(InlineKeyboardButton(text="📢 Telegram", url=prof.telegram_channel))
    elif settings.TELEGRAM_CHANNEL and "streamer_channel" not in settings.TELEGRAM_CHANNEL:
        social_row.append(InlineKeyboardButton(text="📢 Telegram", url=settings.TELEGRAM_CHANNEL))

    if social_row:
        inline_keyboard.append(social_row)

    if prof and prof.donation_url:
        inline_keyboard.append([
            InlineKeyboardButton(text=f"💰 {prof.donation_title or 'Поддержать на DonateX'}", url=prof.donation_url)
        ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handles /start command, registers user in DB, sends welcome banner."""
    tg_user = message.from_user
    
    # Save user to DB if not exists
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == tg_user.id))
        user = result.scalars().first()
        is_admin = tg_user.id in settings.admin_ids
        role = "admin" if is_admin else "viewer"
        
        if not user:
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name or "",
                last_name=tg_user.last_name or "",
                role=role
            )
            db.add(user)
            await db.commit()
        else:
            if is_admin and user.role != "admin":
                user.role = "admin"
                await db.commit()

    welcome_text = (
        f"👋 Привет, <b>{tg_user.first_name}</b>!\n\n"
        f"Добро пожаловать в официальное приложение стримера <b>{settings.STREAMER_NAME}</b>! 🎮✨\n\n"
        f"Здесь ты можешь:\n"
        f"📅 Смотреть актуальное <b>расписание стримов</b>\n"
        f"⏰ Включать <b>напоминания</b> о трансляциях\n"
        f"💡 Предлагать <b>игры, челленджи и вопросы</b> в «Предложку»\n"
        f"👍 Голосовать за лучшие идеи других зрителей\n"
        f"🔔 Получать уведомления о старте стримов и анонсах\n\n"
        f"Жми кнопку ниже, чтобы запустить Mini App 👇"
    )

    async with AsyncSessionLocal() as db:
        keyboard = await get_main_menu_keyboard(db)

    await message.answer(
        text=welcome_text,
        reply_markup=keyboard
    )


def get_clean_webapp_url() -> str:
    url = settings.WEBAPP_URL
    if not url or "your-domain.com" in url:
        return "https://nekomini.onrender.com"
    return url.rstrip("/")


@router.message(Command("schedule"))
async def cmd_schedule(message: Message):
    """Sends schedule preview and button to open TMA."""
    async with AsyncSessionLocal() as db:
        # Check if live
        live_result = await db.execute(select(Stream).where(Stream.is_live == True))
        live_stream = live_result.scalars().first()

        upcoming_result = await db.execute(
            select(Stream)
            .where(Stream.is_live == False, Stream.status == "scheduled")
            .order_by(Stream.start_time.asc())
            .limit(3)
        )
        upcoming_streams = upcoming_result.scalars().all()

    if live_stream:
        text = (
            f"🔴 <b>СЕЙЧАС В ЭФИРЕ!</b>\n\n"
            f"🎬 <b>{live_stream.title}</b>\n"
            f"🎮 {live_stream.game_category} | 📡 {live_stream.platform}\n\n"
            f"🔗 <a href='{live_stream.platform_url}'>Перейти на трансляцию</a>\n\n"
        )
    else:
        text = "📅 <b>Ближайшие запланированные стримы:</b>\n\n"
        if upcoming_streams:
            for s in upcoming_streams:
                dt_str = s.start_time.strftime("%d.%m в %H:%M")
                text += f"▫️ <b>{s.title}</b>\n   🕒 {dt_str} | 🎮 {s.game_category} ({s.platform})\n\n"
        else:
            text += "Пока нет запланированных стримов. Следите за анонсами!\n\n"

    webapp_url = get_clean_webapp_url()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 Открыть полное расписание",
                web_app=WebAppInfo(url=f"{webapp_url}#schedule")
            )
        ]
    ])
    await message.answer(text=text, reply_markup=keyboard)


@router.message(Command("suggest"))
async def cmd_suggest(message: Message):
    """Instructions for suggestions."""
    text = (
        "💡 <b>Предложка и Вопросы для стримера</b>\n\n"
        "Хочешь предложить крутую игру, челлендж или задать вопрос стримеру?\n\n"
        "1. Открой Mini App по кнопке ниже\n"
        "2. Перейди во вкладку «Предложка»\n"
        "3. Выбери категорию и отправь свою идею!\n"
        "4. Голосуй за предложения других зрителей — топ попадает на стрим! 🔥"
    )
    webapp_url = get_clean_webapp_url()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💡 Перейти в Предложку",
                web_app=WebAppInfo(url=f"{webapp_url}#suggestions")
            )
        ]
    ])
    await message.answer(text=text, reply_markup=keyboard)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin dashboard stats in Telegram."""
    if message.from_user.id not in settings.admin_ids:
        await message.answer("⛔️ У вас нет прав администратора.")
        return

    async with AsyncSessionLocal() as db:
        users_count = await db.scalar(select(func.count(User.telegram_id)))
        pending_count = await db.scalar(
            select(func.count(Suggestion.id)).where(Suggestion.status == "pending")
        )
        streams_count = await db.scalar(select(func.count(Stream.id)))
        live_stream = (await db.execute(select(Stream).where(Stream.is_live == True))).scalars().first()

    live_status = f"🔴 В эфире ({live_stream.title})" if live_stream else "⚪️ Офлайн"

    text = (
        f"🛡️ <b>Панель управления стримера:</b>\n\n"
        f"📊 <b>Статус:</b> {live_status}\n"
        f"👥 <b>Подписчиков бота:</b> {users_count}\n"
        f"⏳ <b>Идей на модерации:</b> {pending_count}\n"
        f"📅 <b>Всего стримов в базе:</b> {streams_count}\n\n"
        f"Управляйте расписанием и модерируйте предложку в Mini App 👇"
    )
    webapp_url = get_clean_webapp_url()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛡️ Открыть Админ-панель TMA",
                web_app=WebAppInfo(url=f"{webapp_url}#admin")
            )
        ]
    ])
    await message.answer(text=text, reply_markup=keyboard)


@router.callback_query(F.data == "btn_schedule")
async def cb_schedule(callback):
    """Callback for inline schedule button."""
    await callback.answer()
    await cmd_schedule(callback.message)


@router.callback_query(F.data == "btn_suggest")
async def cb_suggest(callback):
    """Callback for inline suggest button."""
    await callback.answer()
    await cmd_suggest(callback.message)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Help message."""
    text = (
        "🤖 <b>Доступные команды:</b>\n\n"
        "• /start — Главное меню и запуск Mini App\n"
        "• /schedule — Расписание ближайших стримов\n"
        "• /suggest — Как предложить идею или вопрос\n"
        "• /admin — Панель стримера (только для админов)\n"
        "• /backup — Выгрузить резервную копию базы данных (.db)\n"
        "• /help — Справка по боту"
    )
    await message.answer(text=text)


import os
import datetime
from aiogram.types import FSInputFile

@router.message(Command("backup"))
async def cmd_backup(message: Message):
    """Sends current SQLite database file and summary to Admin."""
    is_admin = message.from_user.id in settings.admin_ids
    if not is_admin:
        async with AsyncSessionLocal() as db:
            u_res = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
            u = u_res.scalars().first()
            if not u or u.role != "admin":
                await message.answer("⛔️ Команда доступна только администраторам.")
                return

    db_path = "tma_streamer.db"
    if not os.path.exists(db_path):
        if os.path.exists("../tma_streamer.db"):
            db_path = "../tma_streamer.db"
        elif os.path.exists("backend/tma_streamer.db"):
            db_path = "backend/tma_streamer.db"

    if not os.path.exists(db_path):
        await message.answer("⚠️ Файл базы данных не найден на диске.")
        return

    async with AsyncSessionLocal() as db:
        users_count = await db.scalar(select(func.count(User.telegram_id))) or 0
        streams_count = await db.scalar(select(func.count(Stream.id))) or 0
        sug_count = await db.scalar(select(func.count(Suggestion.id))) or 0

    now_str = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    caption = (
        f"📦 <b>Резервная копия базы данных ({now_str} UTC)</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📅 Стримов: {streams_count}\n"
        f"💡 Идей в предложке: {sug_count}\n\n"
        f"<i>Сохраните этот файл. В случае необходимости отправьте его боту с подписью <code>/restore</code> для моментального восстановления!</i>"
    )

    doc = FSInputFile(db_path, filename=f"tma_streamer_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.db")
    await message.answer_document(document=doc, caption=caption)
