from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserSettingsUpdate, UserOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("", response_model=UserOut)
async def get_settings(current_user: User = Depends(get_current_user)):
    """Returns current user's profile and notification preferences."""
    return current_user

@router.put("", response_model=UserOut)
async def update_settings(
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates user notification preferences."""
    if settings_in.notify_stream_start is not None:
        current_user.notify_stream_start = settings_in.notify_stream_start
    if settings_in.notify_announcements is not None:
        current_user.notify_announcements = settings_in.notify_announcements
    if settings_in.notify_answers is not None:
        current_user.notify_answers = settings_in.notify_answers

    await db.commit()
    await db.refresh(current_user)
    return current_user
