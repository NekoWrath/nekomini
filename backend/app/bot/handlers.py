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


import os
import json
import shutil
import datetime
from aiogram import Bot
from aiogram.types import FSInputFile
from app.models import PromoCode, Giveaway

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
        "• /restore — Восстановить базу данных из прикрепленного файла (.db / .json)\n"
        "• /help — Справка по боту"
    )
    await message.answer(text=text)


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


async def is_user_admin(telegram_id: int) -> bool:
    if telegram_id in settings.admin_ids:
        return True
    async with AsyncSessionLocal() as db:
        u_res = await db.execute(select(User).where(User.telegram_id == telegram_id))
        u = u_res.scalars().first()
        return bool(u and u.role == "admin")


async def restore_from_json_content(backup_data: dict, db) -> str:
    """Restores database from JSON backup dictionary."""
    # 1. Profile
    if "streamer_profile" in backup_data and backup_data["streamer_profile"]:
        prof_data = backup_data["streamer_profile"]
        prof_res = await db.execute(select(StreamerProfile).where(StreamerProfile.id == 1))
        prof = prof_res.scalars().first()
        if not prof:
            prof = StreamerProfile(id=1)
            db.add(prof)
        for k, v in prof_data.items():
            if hasattr(prof, k):
                setattr(prof, k, v)

    # 2. Users
    if "users" in backup_data:
        for u_data in backup_data["users"]:
            tid = u_data.get("telegram_id")
            if not tid:
                continue
            u_res = await db.execute(select(User).where(User.telegram_id == tid))
            user = u_res.scalars().first()
            if not user:
                user = User(
                    telegram_id=tid,
                    username=u_data.get("username"),
                    first_name=u_data.get("first_name", ""),
                    last_name=u_data.get("last_name"),
                    photo_url=u_data.get("photo_url"),
                    role=u_data.get("role", "viewer"),
                    points_balance=u_data.get("points_balance", 500),
                    twitch_id=u_data.get("twitch_id"),
                    twitch_username=u_data.get("twitch_username"),
                    twitch_display_name=u_data.get("twitch_display_name"),
                    twitch_avatar=u_data.get("twitch_avatar"),
                    notify_stream_start=u_data.get("notify_stream_start", True),
                    notify_announcements=u_data.get("notify_announcements", True),
                    notify_answers=u_data.get("notify_answers", True)
                )
                db.add(user)
            else:
                user.first_name = u_data.get("first_name", user.first_name)
                user.username = u_data.get("username", user.username)
                if "points_balance" in u_data:
                    user.points_balance = u_data["points_balance"]
                if "twitch_username" in u_data and u_data["twitch_username"]:
                    user.twitch_username = u_data["twitch_username"]
                    user.twitch_display_name = u_data.get("twitch_display_name", u_data["twitch_username"])
                    user.twitch_id = u_data.get("twitch_id", user.twitch_id)
                    user.twitch_avatar = u_data.get("twitch_avatar", user.twitch_avatar)

    # 3. Streams
    if "streams" in backup_data:
        for s_data in backup_data["streams"]:
            s_id = s_data.get("id")
            stream = None
            if s_id:
                s_res = await db.execute(select(Stream).where(Stream.id == s_id))
                stream = s_res.scalars().first()
            start_time = datetime.datetime.utcnow()
            if s_data.get("start_time"):
                try:
                    start_time = datetime.datetime.fromisoformat(s_data["start_time"])
                except Exception:
                    pass
            if not stream:
                stream = Stream(
                    title=s_data.get("title", "Стрим"),
                    description=s_data.get("description", ""),
                    game_category=s_data.get("game_category", "Just Chatting"),
                    platform=s_data.get("platform", "Twitch"),
                    platform_url=s_data.get("platform_url", "https://twitch.tv"),
                    start_time=start_time,
                    tags=s_data.get("tags", "gaming"),
                    is_live=s_data.get("is_live", False),
                    status=s_data.get("status", "scheduled")
                )
                db.add(stream)

    # 4. Suggestions
    if "suggestions" in backup_data:
        for sg_data in backup_data["suggestions"]:
            sg_id = sg_data.get("id")
            sug = None
            if sg_id:
                sg_res = await db.execute(select(Suggestion).where(Suggestion.id == sg_id))
                sug = sg_res.scalars().first()
            if not sug:
                sug = Suggestion(
                    telegram_id=sg_data.get("telegram_id"),
                    author_name=sg_data.get("author_name", "Зритель"),
                    author_username=sg_data.get("author_username"),
                    author_avatar=sg_data.get("author_avatar"),
                    category=sg_data.get("category", "other"),
                    title=sg_data.get("title", ""),
                    content=sg_data.get("content", ""),
                    media_url=sg_data.get("media_url"),
                    upvotes_count=sg_data.get("upvotes_count", 0),
                    status=sg_data.get("status", "pending"),
                    admin_reply=sg_data.get("admin_reply")
                )
                db.add(sug)

    # 5. Promocodes
    if "promocodes" in backup_data:
        for p_data in backup_data["promocodes"]:
            p_code = p_data.get("code")
            if not p_code:
                continue
            pr_res = await db.execute(select(PromoCode).where(PromoCode.code == p_code))
            if not pr_res.scalars().first():
                promo = PromoCode(
                    code=p_code,
                    points_reward=p_data.get("points_reward", 1000),
                    max_activations=p_data.get("max_activations", 1),
                    activations_count=p_data.get("activations_count", 0),
                    is_active=p_data.get("is_active", True)
                )
                db.add(promo)

    # 6. Giveaways
    if "giveaways" in backup_data:
        for g_data in backup_data["giveaways"]:
            g_id = g_data.get("id")
            g = None
            if g_id:
                g_res = await db.execute(select(Giveaway).where(Giveaway.id == g_id))
                g = g_res.scalars().first()
            if not g:
                end_time_val = datetime.datetime.utcnow() + datetime.timedelta(days=3)
                if g_data.get("end_time"):
                    try:
                        end_time_val = datetime.datetime.fromisoformat(g_data["end_time"])
                    except Exception:
                        pass
                g = Giveaway(
                    title=g_data.get("title", "Розыгрыш"),
                    description=g_data.get("description", ""),
                    image_url=g_data.get("image_url"),
                    ticket_price=g_data.get("ticket_price", 100),
                    max_tickets_per_user=g_data.get("max_tickets_per_user", 10),
                    end_time=end_time_val,
                    status=g_data.get("status", "active"),
                    winner_telegram_id=g_data.get("winner_telegram_id"),
                    winner_name=g_data.get("winner_name"),
                    winner_avatar=g_data.get("winner_avatar"),
                    winning_ticket_number=g_data.get("winning_ticket_number"),
                    total_tickets=g_data.get("total_tickets", 0)
                )
                db.add(g)

    await db.commit()
    return (
        f"✅ <b>Данные успешно восстановлены из JSON!</b>\n\n"
        f"📅 Стримов: {len(backup_data.get('streams', []))}\n"
        f"👥 Пользователей: {len(backup_data.get('users', []))}\n"
        f"💡 Предложений: {len(backup_data.get('suggestions', []))}\n"
        f"🎟️ Промокодов: {len(backup_data.get('promocodes', []))}\n"
        f"🎁 Розыгрышей: {len(backup_data.get('giveaways', []))}"
    )


@router.message(Command("restore"))
@router.message(F.document)
async def handle_restore(message: Message, bot: Bot):
    """Restores database from .db or .json file sent by Admin."""
    if not await is_user_admin(message.from_user.id):
        if message.text and message.text.startswith("/restore"):
            await message.answer("⛔️ Команда доступна только администраторам.")
        return

    doc = message.document
    if not doc and message.reply_to_message and message.reply_to_message.document:
        doc = message.reply_to_message.document

    if not doc:
        await message.answer(
            "📥 <b>Как восстановить базу данных через бота:</b>\n\n"
            "1. Отправьте файл резервной копии (<b>.db</b> или <b>.json</b>) прямо в этот чат.\n"
            "2. В подписи к файлу укажите команду <code>/restore</code> (или ответьте командой <code>/restore</code> на ранее отправленный файл).\n"
            "3. Бот автоматически восстановит все данные (пользователей, стримы, баллы, промокоды и розыгрыши)!",
            parse_mode="HTML"
        )
        return

    file_name = (doc.file_name or "").lower()
    if not (file_name.endswith(".db") or file_name.endswith(".sqlite") or file_name.endswith(".json")):
        if message.text and message.text.startswith("/restore"):
            await message.answer("⚠️ Пожалуйста, отправьте файл с расширением <b>.db</b> или <b>.json</b>.")
        return

    status_msg = await message.answer("⏳ Скачивание и проверка файла резервной копии...")

    try:
        temp_path = f"/tmp/restore_{doc.file_id}_{doc.file_name}"
        await bot.download(doc, destination=temp_path)

        if file_name.endswith(".json"):
            with open(temp_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            async with AsyncSessionLocal() as db:
                result_text = await restore_from_json_content(backup_data, db)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            await status_msg.edit_text(result_text, parse_mode="HTML")
            return

        # Handle .db SQLite file
        with open(temp_path, "rb") as f:
            header = f.read(16)
        if header != b"SQLite format 3\x00":
            if os.path.exists(temp_path):
                os.remove(temp_path)
            await status_msg.edit_text("❌ Ошибка: файл не является валидной базой данных SQLite.")
            return

        # Target db paths
        paths_to_update = ["tma_streamer.db", "backend/tma_streamer.db", "../tma_streamer.db"]
        for p in paths_to_update:
            if os.path.exists(p) or p == "tma_streamer.db":
                shutil.copy2(temp_path, p)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Run migrations on restored DB
        try:
            from main import run_db_migrations
            if run_db_migrations:
                await run_db_migrations()
        except Exception:
            pass

        async with AsyncSessionLocal() as db:
            users_count = await db.scalar(select(func.count(User.telegram_id))) or 0
            streams_count = await db.scalar(select(func.count(Stream.id))) or 0
            sug_count = await db.scalar(select(func.count(Suggestion.id))) or 0

        await status_msg.edit_text(
            f"✅ <b>База данных SQLite успешно восстановлена!</b>\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"📅 Стримов: {streams_count}\n"
            f"💡 Предложений: {sug_count}\n\n"
            f"Все данные активны в Mini App.",
            parse_mode="HTML"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при восстановлении: {e}")
