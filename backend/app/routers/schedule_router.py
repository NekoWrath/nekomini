import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Stream, StreamReminder, User
from app.schemas import StreamCreate, StreamUpdate, StreamOut
from app.auth import get_current_user, get_admin_user
from app.bot.bot_instance import get_bot
from app.bot.notifications import send_stream_live_broadcast

router = APIRouter(prefix="/api/schedule", tags=["Schedule"])

@router.get("", response_model=List[StreamOut])
async def list_streams(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all streams sorted by start time, including user reminder state."""
    query = select(Stream).order_by(Stream.start_time.asc())
    if status_filter:
        query = query.where(Stream.status == status_filter)

    result = await db.execute(query)
    streams = result.scalars().all()

    # Get reminders for current user
    user_reminders_result = await db.execute(
        select(StreamReminder.stream_id).where(StreamReminder.telegram_id == current_user.telegram_id)
    )
    user_reminder_stream_ids = set(user_reminders_result.scalars().all())

    response = []
    for s in streams:
        data = StreamOut(
            id=s.id,
            title=s.title,
            description=s.description or "",
            game_category=s.game_category,
            platform=s.platform,
            platform_url=s.platform_url,
            start_time=s.start_time,
            end_time=s.end_time,
            is_live=s.is_live,
            status=s.status,
            preview_image_url=s.preview_image_url,
            tags=s.tags or "",
            viewers_count=s.viewers_count,
            has_reminder=s.id in user_reminder_stream_ids,
            created_at=s.created_at
        )
        response.append(data)

    return response


@router.get("/current", response_model=Optional[StreamOut])
async def get_current_or_next_stream(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns the live stream if currently on air, or the closest upcoming stream."""
    # Check if live
    live_result = await db.execute(
        select(Stream).where(Stream.is_live == True).order_by(Stream.start_time.desc())
    )
    live_stream = live_result.scalars().first()

    target_stream = live_stream
    if not target_stream:
        # Closest upcoming stream
        now = datetime.datetime.utcnow()
        upcoming_result = await db.execute(
            select(Stream)
            .where(Stream.status == "scheduled", Stream.start_time >= now - datetime.timedelta(hours=2))
            .order_by(Stream.start_time.asc())
        )
        target_stream = upcoming_result.scalars().first()

    if not target_stream:
        return None

    # Check reminder
    rem_result = await db.execute(
        select(StreamReminder).where(
            StreamReminder.telegram_id == current_user.telegram_id,
            StreamReminder.stream_id == target_stream.id
        )
    )
    has_reminder = rem_result.scalars().first() is not None

    return StreamOut(
        id=target_stream.id,
        title=target_stream.title,
        description=target_stream.description or "",
        game_category=target_stream.game_category,
        platform=target_stream.platform,
        platform_url=target_stream.platform_url,
        start_time=target_stream.start_time,
        end_time=target_stream.end_time,
        is_live=target_stream.is_live,
        status=target_stream.status,
        preview_image_url=target_stream.preview_image_url,
        tags=target_stream.tags or "",
        viewers_count=target_stream.viewers_count,
        has_reminder=has_reminder,
        created_at=target_stream.created_at
    )


@router.post("", response_model=StreamOut)
async def create_stream(
    stream_in: StreamCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new scheduled stream (Admin)."""
    stream = Stream(
        title=stream_in.title,
        description=stream_in.description,
        game_category=stream_in.game_category,
        platform=stream_in.platform,
        platform_url=stream_in.platform_url,
        start_time=stream_in.start_time,
        end_time=stream_in.end_time,
        preview_image_url=stream_in.preview_image_url,
        tags=stream_in.tags or "gaming",
        status="scheduled"
    )
    db.add(stream)
    await db.commit()
    await db.refresh(stream)
    return stream


@router.put("/{stream_id}", response_model=StreamOut)
async def update_stream(
    stream_id: int,
    stream_in: StreamUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates an existing stream (Admin)."""
    result = await db.execute(select(Stream).where(Stream.id == stream_id))
    stream = result.scalars().first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    update_data = stream_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stream, field, value)

    await db.commit()
    await db.refresh(stream)
    return stream


@router.delete("/{stream_id}")
async def delete_stream(
    stream_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a stream (Admin)."""
    result = await db.execute(select(Stream).where(Stream.id == stream_id))
    stream = result.scalars().first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    await db.delete(stream)
    await db.commit()
    return {"success": True, "message": f"Stream {stream_id} deleted"}


@router.post("/{stream_id}/toggle-live")
async def toggle_live_status(
    stream_id: int,
    send_broadcast: bool = False,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggles stream is_live status. If switching to live and send_broadcast=True, sends alert via bot."""
    result = await db.execute(select(Stream).where(Stream.id == stream_id))
    stream = result.scalars().first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    stream.is_live = not stream.is_live
    if stream.is_live:
        stream.status = "live"
    else:
        stream.status = "completed"

    await db.commit()
    await db.refresh(stream)

    broadcast_result = None
    if stream.is_live and send_broadcast:
        # Find all users with notify_stream_start=True
        users_result = await db.execute(
            select(User.telegram_id).where(User.notify_stream_start == True)
        )
        user_ids = users_result.scalars().all()
        bot = get_bot()
        broadcast_result = await send_stream_live_broadcast(
            bot=bot,
            users_ids=user_ids,
            stream_title=stream.title,
            game_category=stream.game_category,
            platform=stream.platform,
            platform_url=stream.platform_url
        )

    return {
        "success": True,
        "is_live": stream.is_live,
        "status": stream.status,
        "broadcast": broadcast_result
    }


@router.post("/{stream_id}/toggle-reminder")
async def toggle_reminder(
    stream_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggles reminder subscription for a given stream for current user."""
    # Check stream exists
    s_result = await db.execute(select(Stream).where(Stream.id == stream_id))
    stream = s_result.scalars().first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    rem_result = await db.execute(
        select(StreamReminder).where(
            StreamReminder.telegram_id == current_user.telegram_id,
            StreamReminder.stream_id == stream_id
        )
    )
    reminder = rem_result.scalars().first()

    if reminder:
        await db.delete(reminder)
        await db.commit()
        return {"has_reminder": False, "message": "Напоминание выключено"}
    else:
        new_reminder = StreamReminder(
            telegram_id=current_user.telegram_id,
            stream_id=stream_id,
            is_sent=False
        )
        db.add(new_reminder)
        await db.commit()
        return {"has_reminder": True, "message": "Напоминание включено! Бот пришлет пуш за 15-30 минут."}
