from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.auth import get_current_user
from app.models import User
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class AuthMeResponse(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: str
    notify_stream_start: bool
    notify_announcements: bool
    notify_answers: bool
    streamer_info: dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import StreamerProfile

@router.get("/me", response_model=AuthMeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns the authenticated user info and dynamic streamer metadata."""
    prof_res = await db.execute(select(StreamerProfile).where(StreamerProfile.id == 1))
    prof = prof_res.scalars().first()

    if not prof:
        # Initialize default from settings
        prof = StreamerProfile(
            id=1,
            name=settings.STREAMER_NAME,
            avatar=settings.STREAMER_AVATAR,
            twitch_url=settings.TWITCH_URL if "streamer" not in settings.TWITCH_URL else None,
            telegram_channel=settings.TELEGRAM_CHANNEL if "streamer_channel" not in settings.TELEGRAM_CHANNEL else None,
            donation_url="https://donatex.ru/",
            donation_title="Поддержать на DonateX"
        )
        db.add(prof)
        await db.commit()
        await db.refresh(prof)

    return AuthMeResponse(
        telegram_id=current_user.telegram_id,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        photo_url=current_user.photo_url,
        role=current_user.role,
        notify_stream_start=current_user.notify_stream_start,
        notify_announcements=current_user.notify_announcements,
        notify_answers=current_user.notify_answers,
        streamer_info={
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
            "donation_title": prof.donation_title or "Поддержать на DonateX",
        }
    )
