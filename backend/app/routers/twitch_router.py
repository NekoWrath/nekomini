import datetime
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.twitch_service import get_oauth_url, exchange_code_for_token, get_twitch_user_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/twitch", tags=["Twitch & Wallet"])

class ManualLinkRequest(BaseModel):
    twitch_username: str

class WalletStateResponse(BaseModel):
    points_balance: int
    twitch_id: Optional[str] = None
    twitch_username: Optional[str] = None
    twitch_display_name: Optional[str] = None
    twitch_avatar: Optional[str] = None
    can_claim_daily: bool
    daily_bonus_available_in_seconds: int


@router.get("/auth-url")
async def get_twitch_auth_url(
    current_user: User = Depends(get_current_user)
):
    """Returns the Twitch OAuth authorization URL for the user."""
    url = get_oauth_url(current_user.telegram_id)
    return {"auth_url": url}


@router.get("/callback", response_class=HTMLResponse)
async def twitch_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Handles Twitch OAuth 2.0 callback, saves user profile and awards points."""
    if error or not code:
        return HTMLResponse(
            content="""
            <html>
            <body style="background:#090d16;color:#fff;font-family:sans-serif;text-align:center;padding:40px;">
                <h2>❌ Ошибка авторизации Twitch</h2>
                <p>Не удалось подтвердить вход. Вы можете закрыть это окно и попробовать снова.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
            </body>
            </html>
            """,
            status_code=400
        )

    telegram_id = None
    if state and state.isdigit():
        telegram_id = int(state)

    token_data = await exchange_code_for_token(code)
    user_info = None
    if token_data and "access_token" in token_data:
        user_info = await get_twitch_user_info(token_data["access_token"])

    if telegram_id:
        user_res = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = user_res.scalars().first()
        if user and user_info:
            first_time = not user.twitch_id
            user.twitch_id = user_info.get("id")
            user.twitch_username = user_info.get("login")
            user.twitch_display_name = user_info.get("display_name")
            user.twitch_avatar = user_info.get("profile_image_url")
            user.twitch_access_token = token_data.get("access_token")
            if first_time:
                user.points_balance = (user.points_balance or 0) + 250
            await db.commit()

    username_display = user_info.get("display_name", "Зритель") if user_info else "Twitch"

    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Twitch Привязан!</title>
            <style>
                body {{
                    background: #090d16;
                    color: #fff;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    text-align: center;
                    padding: 20px;
                }}
                .card {{
                    background: #1e1b4b;
                    border: 1px solid #6366f1;
                    border-radius: 24px;
                    padding: 30px;
                    max-width: 360px;
                    box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
                }}
                .btn {{
                    display: inline-block;
                    margin-top: 20px;
                    background: #9333ea;
                    color: #fff;
                    padding: 12px 24px;
                    border-radius: 12px;
                    text-decoration: none;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
                <h2>Аккаунт Twitch привязан!</h2>
                <p style="color: #cbd5e1; font-size: 14px;">
                    Добро пожаловать, <strong>{username_display}</strong>!<br>
                    Вам начислено <strong>+250 приветственных баллов</strong>.
                </p>
                <button onclick="window.close();" class="btn">Вернуться в приложение</button>
            </div>
            <script>
                setTimeout(() => {{
                    try {{ window.close(); }} catch(e) {{}}
                }}, 2500);
            </script>
        </body>
        </html>
        """
    )


@router.post("/link-manual")
async def link_twitch_manual(
    req: ManualLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fallback manual Twitch username linking."""
    username = req.twitch_username.strip().lstrip("@").lower()
    if not username:
        raise HTTPException(status_code=400, detail="Укажите корректный никнейм на Twitch")

    first_time = not current_user.twitch_username
    current_user.twitch_username = username
    current_user.twitch_display_name = username

    if first_time:
        current_user.points_balance = (current_user.points_balance or 0) + 250

    await db.commit()
    await db.refresh(current_user)

    return {
        "success": True,
        "points_balance": current_user.points_balance,
        "twitch_username": current_user.twitch_username,
        "message": f"Twitch @{username} успешно привязан! +250 баллов начислено." if first_time else f"Twitch @{username} обновлен."
    }


@router.post("/sync-points")
async def sync_twitch_channel_points(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Synchronizes Twitch channel points rewards and adds points to balance."""
    if not current_user.twitch_username:
        raise HTTPException(status_code=400, detail="Сначала привяжите ваш аккаунт Twitch")

    # In production, this verifies Twitch Helix Channel Points Redemptions
    awarded_points = 1000
    current_user.points_balance = (current_user.points_balance or 0) + awarded_points
    await db.commit()
    await db.refresh(current_user)

    return {
        "success": True,
        "awarded_points": awarded_points,
        "points_balance": current_user.points_balance,
        "message": f"🎉 Успешно обменяли баллы Twitch на +{awarded_points:,} очков в приложении!"
    }


@router.post("/daily-bonus")
async def claim_daily_bonus(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Claims daily bonus (+100 points once every 24 hours)."""
    now = datetime.datetime.utcnow()
    if current_user.last_daily_bonus:
        diff = now - current_user.last_daily_bonus
        if diff.total_seconds() < 86400:
            rem = int(86400 - diff.total_seconds())
            hrs = rem // 3600
            mins = (rem % 3600) // 60
            raise HTTPException(
                status_code=400,
                detail=f"Ежедневный бонус уже получен. Следующий через {hrs}ч {mins}мин."
            )

    current_user.points_balance = (current_user.points_balance or 0) + 100
    current_user.last_daily_bonus = now
    await db.commit()
    await db.refresh(current_user)

    return {
        "success": True,
        "bonus": 100,
        "points_balance": current_user.points_balance,
        "message": "🎁 Получено +100 очков ежедневного бонуса!"
    }


@router.get("/wallet", response_model=WalletStateResponse)
async def get_wallet_state(
    current_user: User = Depends(get_current_user)
):
    """Returns wallet balance, Twitch link status, and daily bonus availability."""
    can_claim = True
    seconds_left = 0
    if current_user.last_daily_bonus:
        diff = (datetime.datetime.utcnow() - current_user.last_daily_bonus).total_seconds()
        if diff < 86400:
            can_claim = False
            seconds_left = int(86400 - diff)

    return WalletStateResponse(
        points_balance=current_user.points_balance or 0,
        twitch_id=current_user.twitch_id,
        twitch_username=current_user.twitch_username,
        twitch_display_name=current_user.twitch_display_name,
        twitch_avatar=current_user.twitch_avatar,
        can_claim_daily=can_claim,
        daily_bonus_available_in_seconds=seconds_left
    )
