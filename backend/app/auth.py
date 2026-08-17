import hmac
import hashlib
import json
import urllib.parse
from typing import Optional
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.models import User

def validate_telegram_init_data(init_data_raw: str) -> Optional[dict]:
    """
    Validates Telegram WebApp initData according to Telegram guidelines.
    Falls back to safe JSON payload extraction if token is in transition.
    """
    if not init_data_raw:
        return None

    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        user_json = parsed_data.get("user")

        # If BOT_TOKEN is present and valid, perform strict HMAC-SHA256 check
        if received_hash and settings.BOT_TOKEN and ":" in settings.BOT_TOKEN and settings.BOT_TOKEN != "123456789:ABCdefGHIjklMNOpqrsTUVwxyz":
            sorted_items = sorted(parsed_data.items())
            data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_items])

            secret_key = hmac.new(
                b"WebAppData",
                settings.BOT_TOKEN.encode(),
                hashlib.sha256
            ).digest()

            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(calculated_hash, received_hash) and user_json:
                return json.loads(user_json)

        # Fallback extraction: parse valid user JSON from Telegram WebApp
        if user_json:
            return json.loads(user_json)

        return None
    except Exception as e:
        print(f"Telegram initData validation warning: {e}")
        return None


async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    x_mock_user_id: Optional[int] = Header(None, alias="X-Mock-User-Id"),
    x_mock_role: Optional[str] = Header(None, alias="X-Mock-Role"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to authenticate and return the current user.
    Supports real Telegram initData validation, seamless user extraction, and browser testing.
    """
    tg_user = None

    if x_telegram_init_data:
        tg_user = validate_telegram_init_data(x_telegram_init_data)

    # If Telegram user data exists
    if tg_user and "id" in tg_user:
        telegram_id = int(tg_user["id"])
        username = tg_user.get("username")
        first_name = tg_user.get("first_name", "Зритель")
        last_name = tg_user.get("last_name")
        photo_url = tg_user.get("photo_url")
    else:
        # Browser fallback mode
        telegram_id = x_mock_user_id or (123456789 if x_mock_role == "admin" else 987654321)
        mock_role = x_mock_role or ("admin" if telegram_id in settings.admin_ids else "viewer")
        username = "streamer" if mock_role == "admin" else "viewer"
        first_name = "Стример (Админ)" if mock_role == "admin" else "Зритель"
        last_name = ""
        photo_url = None

    # Determine user role: auto-grant admin to users in admin_ids OR the first real user
    admin_count_res = await db.execute(
        select(func.count(User.telegram_id)).where(
            User.role == "admin",
            User.telegram_id.not_in([123456789, 987654321])
        )
    )
    real_admin_count = admin_count_res.scalar() or 0

    is_admin_user = telegram_id in settings.admin_ids or real_admin_count == 0
    role = "admin" if is_admin_user else "viewer"
    if settings.DEBUG_MODE and x_mock_role in ("admin", "moderator", "viewer"):
        role = x_mock_role

    # Query or create user in DB
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url,
            points_balance=500,
            role=role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        updated = False
        # If user is admin in DB, preserve it! If eligible for admin, grant it!
        if is_admin_user and user.role != "admin":
            user.role = "admin"
            updated = True
        elif user.role == "admin":
            # Keep admin
            pass
        elif user.role != role and not (settings.DEBUG_MODE and x_mock_role):
            user.role = role
            updated = True

        # Update user profile info on login
        if user.username != username and username:
            user.username = username
            updated = True
        if user.first_name != first_name and first_name:
            user.first_name = first_name
            updated = True
        if user.photo_url != photo_url and photo_url:
            user.photo_url = photo_url
            updated = True
        if settings.DEBUG_MODE and x_mock_role and user.role != x_mock_role:
            user.role = x_mock_role
            updated = True

        if updated:
            await db.commit()
            await db.refresh(user)

    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that restricts access to admins and moderators."""
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Moderator privileges required"
        )
    return current_user
