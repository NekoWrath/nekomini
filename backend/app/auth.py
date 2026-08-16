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
    Validates Telegram WebApp initData according to Telegram guidelines:
    1. Parse query string into dictionary.
    2. Extract 'hash'.
    3. Sort remaining keys alphabetically into 'key=value' separated by '\n'.
    4. Compute HMAC-SHA256 signature using HMAC-SHA256(bot_token, "WebAppData").
    5. Compare calculated hash with provided hash.
    """
    if not init_data_raw:
        return None

    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None

        # Data check string
        sorted_items = sorted(parsed_data.items())
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_items])

        # Secret key: HMAC-SHA256(key="WebAppData", msg=BOT_TOKEN)
        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        # Calculated hash: HMAC-SHA256(key=secret_key, msg=data_check_string)
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(calculated_hash, received_hash):
            user_json = parsed_data.get("user")
            if user_json:
                return json.loads(user_json)
        return None
    except Exception as e:
        print(f"Telegram initData validation error: {e}")
        return None


async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    x_mock_user_id: Optional[int] = Header(None, alias="X-Mock-User-Id"),
    x_mock_role: Optional[str] = Header(None, alias="X-Mock-Role"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to authenticate and return the current user.
    Supports real Telegram initData validation and Dev Mock Mode.
    """
    tg_user = None

    if x_telegram_init_data:
        tg_user = validate_telegram_init_data(x_telegram_init_data)

    # If Telegram validation passed
    if tg_user and "id" in tg_user:
        telegram_id = int(tg_user["id"])
        username = tg_user.get("username")
        first_name = tg_user.get("first_name", "")
        last_name = tg_user.get("last_name")
        photo_url = tg_user.get("photo_url")
    elif settings.DEBUG_MODE:
        # Development fallback mode
        telegram_id = x_mock_user_id or 123456789
        mock_role = x_mock_role or ("admin" if telegram_id in settings.admin_ids else "viewer")
        username = "dev_streamer" if mock_role == "admin" else "dev_viewer"
        first_name = "Dev Admin" if mock_role == "admin" else "Dev Viewer"
        last_name = "User"
        photo_url = None
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Telegram authentication data"
        )

    # Determine user role
    role = "admin" if telegram_id in settings.admin_ids else "viewer"
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
            role=role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update user profile info on login
        updated = False
        if user.username != username:
            user.username = username
            updated = True
        if user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if user.photo_url != photo_url and photo_url:
            user.photo_url = photo_url
            updated = True
        if user.role != role and not (settings.DEBUG_MODE and x_mock_role):
            user.role = role
            updated = True
        elif settings.DEBUG_MODE and x_mock_role and user.role != x_mock_role:
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
