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


import os
import json
import datetime
from fastapi.responses import JSONResponse, FileResponse
from fastapi import UploadFile, File, Body

@router.get("/backup/export")
async def export_backup_json(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Exports full database contents to a downloadable JSON file."""
    # 1. Profile
    prof_res = await db.execute(select(StreamerProfile).where(StreamerProfile.id == 1))
    prof = prof_res.scalars().first()
    profile_data = {}
    if prof:
        profile_data = {
            "name": prof.name,
            "avatar": prof.avatar,
            "bio": prof.bio,
            "twitch_url": prof.twitch_url,
            "telegram_channel": prof.telegram_channel,
            "youtube_url": prof.youtube_url,
            "kick_url": prof.kick_url,
            "vk_url": prof.vk_url,
            "discord_url": prof.discord_url,
            "donation_url": prof.donation_url,
            "donation_title": prof.donation_title
        }

    # 2. Streams
    streams_res = await db.execute(select(Stream))
    streams = streams_res.scalars().all()
    streams_data = [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "game_category": s.game_category,
            "platform": s.platform,
            "platform_url": s.platform_url,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "is_live": s.is_live,
            "status": s.status,
            "preview_image_url": s.preview_image_url,
            "tags": s.tags,
            "viewers_count": s.viewers_count
        }
        for s in streams
    ]

    # 3. Suggestions
    sug_res = await db.execute(select(Suggestion))
    suggestions = sug_res.scalars().all()
    suggestions_data = [
        {
            "id": s.id,
            "telegram_id": s.telegram_id,
            "author_name": s.author_name,
            "author_username": s.author_username,
            "author_avatar": s.author_avatar,
            "category": s.category,
            "title": s.title,
            "content": s.content,
            "media_url": s.media_url,
            "upvotes_count": s.upvotes_count,
            "status": s.status,
            "admin_reply": s.admin_reply,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in suggestions
    ]

    # 4. Users
    users_res = await db.execute(select(User))
    users = users_res.scalars().all()
    users_data = [
        {
            "telegram_id": u.telegram_id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "photo_url": u.photo_url,
            "role": u.role,
            "notify_stream_start": u.notify_stream_start,
            "notify_announcements": u.notify_announcements,
            "notify_answers": u.notify_answers
        }
        for u in users
    ]

    backup_payload = {
        "version": "1.0",
        "exported_at": datetime.datetime.utcnow().isoformat(),
        "streamer_profile": profile_data,
        "streams": streams_data,
        "suggestions": suggestions_data,
        "users": users_data
    }

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"nekomini_backup_{timestamp}.json"

    return JSONResponse(
        content=backup_payload,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/backup/download-db")
async def download_raw_database(
    admin_user: User = Depends(get_admin_user)
):
    """Directly downloads the local SQLite database file."""
    db_path = "tma_streamer.db"
    if not os.path.exists(db_path):
        # Look in current or parent directory
        if os.path.exists("../tma_streamer.db"):
            db_path = "../tma_streamer.db"
        elif os.path.exists("backend/tma_streamer.db"):
            db_path = "backend/tma_streamer.db"

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found on disk")

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        db_path,
        media_type="application/x-sqlite3",
        filename=f"nekomini_database_{timestamp}.db"
    )


@router.post("/backup/import")
async def import_backup_json(
    backup_data: dict = Body(...),
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Imports and restores streams, suggestions, profile, and users from JSON backup."""
    # 1. Restore Profile
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

    # 2. Restore Users
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
                    notify_stream_start=u_data.get("notify_stream_start", True),
                    notify_announcements=u_data.get("notify_announcements", True),
                    notify_answers=u_data.get("notify_answers", True)
                )
                db.add(user)
            else:
                user.first_name = u_data.get("first_name", user.first_name)
                user.username = u_data.get("username", user.username)
                if u_data.get("role"):
                    user.role = u_data.get("role")

    # 3. Restore Streams
    if "streams" in backup_data:
        for s_data in backup_data["streams"]:
            sid = s_data.get("id")
            stream = None
            if sid:
                s_res = await db.execute(select(Stream).where(Stream.id == sid))
                stream = s_res.scalars().first()
            if not stream:
                start_dt = datetime.datetime.fromisoformat(s_data["start_time"]) if s_data.get("start_time") else datetime.datetime.utcnow()
                stream = Stream(
                    title=s_data.get("title", "Стрим"),
                    description=s_data.get("description", ""),
                    game_category=s_data.get("game_category", "Just Chatting"),
                    platform=s_data.get("platform", "Twitch"),
                    platform_url=s_data.get("platform_url", "https://twitch.tv/"),
                    start_time=start_dt,
                    is_live=s_data.get("is_live", False),
                    status=s_data.get("status", "scheduled"),
                    preview_image_url=s_data.get("preview_image_url"),
                    tags=s_data.get("tags", "")
                )
                db.add(stream)

    # 4. Restore Suggestions
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

    await db.commit()
    return {
        "success": True,
        "message": f"Бэкап успешно применен! Восстановлено: {len(backup_data.get('streams', []))} стримов, {len(backup_data.get('suggestions', []))} предложений."
    }
