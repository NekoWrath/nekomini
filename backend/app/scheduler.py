import os
import datetime
import logging
import zoneinfo
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy import func

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Stream, StreamReminder, User, Suggestion
from app.bot.bot_instance import get_bot
from app.bot.notifications import send_stream_reminder_notification

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def check_and_send_stream_reminders():
    """
    Background cron task:
    Checks for scheduled streams starting in the next 15-30 minutes,
    finds all users who subscribed to reminders for that stream (or have notify_stream_start=True),
    and sends them a reminder message via Telegram Bot.
    """
    now = datetime.datetime.utcnow()
    window_start = now
    window_end = now + datetime.timedelta(minutes=30)

    try:
        async with AsyncSessionLocal() as db:
            # Find streams starting soon that are not live yet
            result = await db.execute(
                select(Stream).where(
                    Stream.status == "scheduled",
                    Stream.start_time >= window_start,
                    Stream.start_time <= window_end
                )
            )
            upcoming_streams = result.scalars().all()

            if not upcoming_streams:
                return

            bot = get_bot()

            for stream in upcoming_streams:
                minutes_left = max(1, int((stream.start_time - now).total_seconds() / 60))

                # Find all un-sent reminders for this stream
                rem_result = await db.execute(
                    select(StreamReminder).where(
                        StreamReminder.stream_id == stream.id,
                        StreamReminder.is_sent == False
                    )
                )
                reminders = rem_result.scalars().all()

                for rem in reminders:
                    # Check if user exists and has telegram_id
                    success = await send_stream_reminder_notification(
                        bot=bot,
                        telegram_id=rem.telegram_id,
                        stream_title=stream.title,
                        game_category=stream.game_category,
                        platform=stream.platform,
                        platform_url=stream.platform_url,
                        minutes_left=minutes_left
                    )
                    if success:
                        rem.is_sent = True

                await db.commit()
    except Exception as e:
        logger.error(f"Error checking stream reminders in background: {e}")


async def send_daily_admin_backup():
    """
    Sends automatic database backup to all admins every day at 22:00 MSK.
    """
    try:
        bot = get_bot()
        if not bot or not settings.BOT_TOKEN:
            return

        db_path = "tma_streamer.db"
        if not os.path.exists(db_path):
            if os.path.exists("../tma_streamer.db"):
                db_path = "../tma_streamer.db"
            elif os.path.exists("backend/tma_streamer.db"):
                db_path = "backend/tma_streamer.db"

        if not os.path.exists(db_path):
            logger.warning("Daily backup: tma_streamer.db not found on disk.")
            return

        # Find all admin IDs
        admin_ids = set(settings.admin_ids)
        async with AsyncSessionLocal() as db:
            admins_res = await db.execute(select(User.telegram_id).where(User.role == "admin"))
            for tid in admins_res.scalars().all():
                admin_ids.add(tid)

            users_count = await db.scalar(select(func.count(User.telegram_id))) or 0
            streams_count = await db.scalar(select(func.count(Stream.id))) or 0
            sug_count = await db.scalar(select(func.count(Suggestion.id))) or 0

        msk_tz = zoneinfo.ZoneInfo("Europe/Moscow")
        now_str = datetime.datetime.now(msk_tz).strftime("%d.%m.%Y в 22:00 МСК")
        caption = (
            f"🌙 <b>Ежедневный авто-бэкап базы данных ({now_str})</b>\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"📅 Стримов: {streams_count}\n"
            f"💡 Идей в предложке: {sug_count}\n\n"
            f"<i>Файл базы данных сохранен и прикреплен к этому сообщению.</i>"
        )

        date_tag = datetime.datetime.now(msk_tz).strftime("%Y%m%d")
        for admin_id in admin_ids:
            try:
                doc = FSInputFile(db_path, filename=f"tma_streamer_backup_{date_tag}.db")
                await bot.send_document(chat_id=admin_id, document=doc, caption=caption)
                logger.info(f"Daily backup sent successfully to admin {admin_id}")
            except Exception as e:
                logger.warning(f"Could not send daily backup to admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Error in send_daily_admin_backup job: {e}")


def start_scheduler():
    """Starts the AsyncIOScheduler jobs."""
    if not scheduler.running:
        # 1. Stream push reminders every 1 minute
        scheduler.add_job(
            check_and_send_stream_reminders,
            "interval",
            minutes=1,
            id="stream_reminder_job",
            replace_existing=True
        )

        # 2. Daily Database Auto-Backup to Admins at 22:00 MSK
        scheduler.add_job(
            send_daily_admin_backup,
            "cron",
            hour=22,
            minute=0,
            timezone=zoneinfo.ZoneInfo("Europe/Moscow"),
            id="daily_backup_job",
            replace_existing=True
        )

        scheduler.start()
        logger.info("APScheduler started: stream reminder check (1 min) & daily auto-backup (22:00 MSK).")


def shutdown_scheduler():
    """Gracefully shuts down scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped.")
