from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import get_db
from app.models import User, Stream, Suggestion, SuggestionVote, Announcement
from app.schemas import BroadcastRequest, BroadcastResponse
from app.auth import get_admin_user
from app.bot.bot_instance import get_bot
from app.bot.notifications import send_custom_broadcast

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/stats")
async def get_admin_stats(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns analytics and count statistics for the streamer admin dashboard."""
    users_count = await db.scalar(select(func.count(User.telegram_id)))
    pending_suggestions = await db.scalar(
        select(func.count(Suggestion.id)).where(Suggestion.status == "pending")
    )
    total_suggestions = await db.scalar(select(func.count(Suggestion.id)))
    total_votes = await db.scalar(select(func.count(SuggestionVote.id)))
    total_streams = await db.scalar(select(func.count(Stream.id)))
    
    live_stream_res = await db.execute(select(Stream).where(Stream.is_live == True))
    live_stream = live_stream_res.scalars().first()

    return {
        "users_count": users_count or 0,
        "pending_suggestions": pending_suggestions or 0,
        "total_suggestions": total_suggestions or 0,
        "total_votes": total_votes or 0,
        "total_streams": total_streams or 0,
        "is_live": live_stream is not None,
        "live_stream_title": live_stream.title if live_stream else None
    }


@router.post("/broadcast", response_model=BroadcastResponse)
async def create_and_send_broadcast(
    req: BroadcastRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Broadcasts a custom announcement message via Telegram bot to all subscribers."""
    # Find all users with notify_announcements=True
    users_result = await db.execute(
        select(User.telegram_id).where(User.notify_announcements == True)
    )
    user_ids = users_result.scalars().all()

    if not user_ids:
        return BroadcastResponse(
            success=True,
            sent_count=0,
            failed_count=0,
            message="Нет подписанных пользователей для рассылки"
        )

    bot = get_bot()
    broadcast_result = await send_custom_broadcast(
        bot=bot,
        users_ids=user_ids,
        title=req.title,
        content=req.content,
        image_url=req.image_url,
        button_text=req.button_text,
        button_url=req.button_url
    )

    # Save to history
    announcement = Announcement(
        title=req.title,
        content=req.content,
        image_url=req.image_url,
        button_text=req.button_text,
        button_url=req.button_url,
        sent_count=broadcast_result["sent_count"]
    )
    db.add(announcement)
    await db.commit()

    return BroadcastResponse(
        success=True,
        sent_count=broadcast_result["sent_count"],
        failed_count=broadcast_result["failed_count"],
        message=f"Рассылка завершена: доставлено {broadcast_result['sent_count']}, ошибок {broadcast_result['failed_count']}"
    )


from app.models import StreamerProfile
from app.schemas import StreamerProfileOut, StreamerProfileUpdate

@router.get("/profile", response_model=StreamerProfileOut)
async def get_streamer_profile(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns editable streamer profile & social links (Admin)."""
    prof_res = await db.execute(select(StreamerProfile).where(StreamerProfile.id == 1))
    prof = prof_res.scalars().first()
    if not prof:
        prof = StreamerProfile(id=1)
        db.add(prof)
        await db.commit()
        await db.refresh(prof)
    return prof


@router.put("/profile", response_model=StreamerProfileOut)
async def update_streamer_profile(
    prof_in: StreamerProfileUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates streamer profile, social networks, and DonateX link (Admin)."""
    prof_res = await db.execute(select(StreamerProfile).where(StreamerProfile.id == 1))
    prof = prof_res.scalars().first()
    if not prof:
        prof = StreamerProfile(id=1)
        db.add(prof)

    update_data = prof_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prof, field, value)

    await db.commit()
    await db.refresh(prof)
    return prof


@router.get("/videos")
async def get_suggested_youtube_videos(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns all suggestions that have a YouTube video attached."""
    query = (
        select(Suggestion)
        .where(
            Suggestion.media_url.isnot(None),
            (Suggestion.media_url.ilike("%youtube.com%")) | (Suggestion.media_url.ilike("%youtu.be%"))
        )
        .order_by(Suggestion.created_at.desc())
    )
    result = await db.execute(query)
    suggestions = result.scalars().all()

    videos = []
    for s in suggestions:
        videos.append({
            "id": s.id,
            "title": s.title,
            "content": s.content or "",
            "media_url": s.media_url,
            "author_name": s.author_name,
            "author_username": s.author_username,
            "author_avatar": s.author_avatar,
            "upvotes_count": s.upvotes_count,
            "status": s.status,
            "admin_reply": s.admin_reply,
            "created_at": s.created_at
        })

    return videos
