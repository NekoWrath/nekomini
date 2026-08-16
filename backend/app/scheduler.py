import datetime
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models import Stream, StreamReminder, User
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


def start_scheduler():
    """Starts the AsyncIOScheduler job."""
    if not scheduler.running:
        scheduler.add_job(
            check_and_send_stream_reminders,
            "interval",
            minutes=1,
            id="stream_reminder_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler started: stream reminder check every 1 minute.")


def shutdown_scheduler():
    """Gracefully shuts down scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped.")
