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


import random
import string
from pydantic import BaseModel
from typing import Optional
from app.models import PromoCode, PromoCodeActivation, Giveaway, GiveawayTicket

class GeneratePromoRequest(BaseModel):
    count: int = 1
    points_reward: int = 1000
    max_activations: int = 1
    prefix: Optional[str] = "NEKO"

@router.get("/promocodes")
async def list_promocodes(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns list of all generated promo codes."""
    res = await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
    codes = res.scalars().all()
    return [
        {
            "id": c.id,
            "code": c.code,
            "points_reward": c.points_reward,
            "max_activations": c.max_activations,
            "activations_count": c.activations_count,
            "is_active": c.is_active,
            "created_at": c.created_at.strftime("%d.%m.%Y %H:%M") if c.created_at else ""
        }
        for c in codes
    ]


@router.post("/promocodes/generate")
async def generate_promocodes(
    req: GeneratePromoRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates one or multiple unique single-use or multi-use promo codes."""
    generated = []
    prefix = (req.prefix or "NEKO").strip().upper().replace(" ", "")
    count = max(1, min(req.count, 50))  # Between 1 and 50

    for _ in range(count):
        rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        code_str = f"{prefix}-{rand_suffix}"
        
        promo = PromoCode(
            code=code_str,
            points_reward=max(10, req.points_reward),
            max_activations=max(1, req.max_activations),
            activations_count=0,
            is_active=True
        )
        db.add(promo)
        generated.append(code_str)

    await db.commit()
    return {
        "success": True,
        "count": len(generated),
        "codes": generated,
        "points_reward": req.points_reward,
        "message": f"Сгенерировано {len(generated)} кодов на {req.points_reward} PTS!"
    }


@router.delete("/promocodes/{promo_id}")
async def delete_promocode(
    promo_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a promo code."""
    res = await db.execute(select(PromoCode).where(PromoCode.id == promo_id))
    promo = res.scalars().first()
    if not promo:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    await db.delete(promo)
    await db.commit()
    return {"success": True, "message": "Промокод удален"}


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
            "points_balance": u.points_balance or 0,
            "twitch_id": u.twitch_id,
            "twitch_username": u.twitch_username,
            "twitch_display_name": u.twitch_display_name,
            "twitch_avatar": u.twitch_avatar,
            "notify_stream_start": u.notify_stream_start,
            "notify_announcements": u.notify_announcements,
            "notify_answers": u.notify_answers
        }
        for u in users
    ]

    # 5. Promocodes
    promo_res = await db.execute(select(PromoCode))
    promocodes = promo_res.scalars().all()
    promocodes_data = [
        {
            "code": p.code,
            "points_reward": p.points_reward,
            "max_activations": p.max_activations,
            "activations_count": p.activations_count,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in promocodes
    ]

    # 6. Giveaways
    giveaway_res = await db.execute(select(Giveaway))
    giveaways = giveaway_res.scalars().all()
    giveaways_data = [
        {
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "image_url": g.image_url,
            "ticket_price": g.ticket_price,
            "max_tickets_per_user": g.max_tickets_per_user,
            "end_time": g.end_time.isoformat() if g.end_time else None,
            "status": g.status,
            "winner_telegram_id": g.winner_telegram_id,
            "winner_name": g.winner_name,
            "winner_avatar": g.winner_avatar,
            "winning_ticket_number": g.winning_ticket_number,
            "total_tickets": g.total_tickets,
            "created_at": g.created_at.isoformat() if g.created_at else None
        }
        for g in giveaways
    ]

    backup_payload = {
        "version": "1.0",
        "exported_at": datetime.datetime.utcnow().isoformat(),
        "streamer_profile": profile_data,
        "streams": streams_data,
        "suggestions": suggestions_data,
        "users": users_data,
        "promocodes": promocodes_data,
        "giveaways": giveaways_data
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
    """Imports and restores streams, suggestions, profile, points, and users from JSON backup."""
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
    # 5. Restore Promocodes
    if "promocodes" in backup_data:
        for p_data in backup_data["promocodes"]:
            p_code = p_data.get("code")
            if not p_code:
                continue
            pr_res = await db.execute(select(PromoCode).where(PromoCode.code == p_code))
            promo = pr_res.scalars().first()
            if not promo:
                promo = PromoCode(
                    code=p_code,
                    points_reward=p_data.get("points_reward", 1000),
                    max_activations=p_data.get("max_activations", 1),
                    activations_count=p_data.get("activations_count", 0),
                    is_active=p_data.get("is_active", True)
                )
    # 6. Restore Giveaways
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
    return {
        "success": True,
        "message": f"Бэкап успешно применен! Восстановлено: {len(backup_data.get('streams', []))} стримов, {len(backup_data.get('suggestions', []))} предложений, {len(backup_data.get('promocodes', []))} кодов, {len(backup_data.get('giveaways', []))} розыгрышей."
    }
