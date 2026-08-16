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

@router.get("/me", response_model=AuthMeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user info and streamer metadata."""
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
            "name": settings.STREAMER_NAME,
            "avatar": settings.STREAMER_AVATAR,
            "twitch_url": settings.TWITCH_URL,
            "kick_url": settings.KICK_URL,
            "vk_url": settings.VK_URL,
            "telegram_channel": settings.TELEGRAM_CHANNEL,
        }
    )
