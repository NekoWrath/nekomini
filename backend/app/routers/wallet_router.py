import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.types import LabeledPrice

from app.database import get_db
from app.models import User, PaymentTransaction
from app.schemas import (
    WalletStateOut, StarsPackage, CreateStarsInvoiceRequest, InvoiceLinkResponse,
    LinkTwitchRequest, ClaimTwitchPointsRequest, DailyBonusResponse
)
from app.routers.auth_router import get_current_user
from app.bot.bot_instance import bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wallet", tags=["Wallet & Payments"])

STARS_PACKAGES: List[StarsPackage] = [
    StarsPackage(
        id="stars_50",
        stars=50,
        points=2500,
        title="🌟 Стартовый набор",
        bonus_label="Базовый",
        badge_color="bg-slate-800 text-slate-300"
    ),
    StarsPackage(
        id="stars_100",
        stars=100,
        points=5500,
        title="🔥 Набор Стримера",
        bonus_label="+10% Бонус",
        badge_color="bg-amber-500/20 text-amber-300 border border-amber-500/40"
    ),
    StarsPackage(
        id="stars_250",
        stars=250,
        points=15000,
        title="👑 VIP Набор",
        bonus_label="+20% Бонус",
        badge_color="bg-purple-500/20 text-purple-300 border border-purple-500/40"
    ),
    StarsPackage(
        id="stars_500",
        stars=500,
        points=35000,
        title="⚡️ Набор Легенды",
        bonus_label="+40% Супербонус",
        badge_color="bg-rose-500/20 text-rose-300 border border-rose-500/40"
    )
]

@router.get("", response_model=WalletStateOut)
async def get_wallet_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.datetime.utcnow()
    can_claim_daily = True
    next_daily_at = None

    if current_user.last_daily_bonus:
        diff = now - current_user.last_daily_bonus
        if diff.total_seconds() < 86400:
            can_claim_daily = False
            next_daily_at = current_user.last_daily_bonus + datetime.timedelta(seconds=86400)

    return WalletStateOut(
        points_balance=current_user.points_balance or 0,
        twitch_username=current_user.twitch_username,
        packages=STARS_PACKAGES,
        can_claim_daily=can_claim_daily,
        next_daily_at=next_daily_at
    )

@router.post("/create-invoice", response_model=InvoiceLinkResponse)
async def create_stars_invoice(
    payload: CreateStarsInvoiceRequest,
    current_user: User = Depends(get_current_user)
):
    package = next((p for p in STARS_PACKAGES if p.id == payload.package_id), None)
    if not package:
        raise HTTPException(status_code=400, detail="Неверный пакет Telegram Stars")

    try:
        invoice_payload = f"stars_{package.id}_{current_user.telegram_id}_{int(datetime.datetime.utcnow().timestamp())}"
        
        # Create native Telegram Stars invoice link (XTR currency)
        invoice_link = await bot.create_invoice_link(
            title=f"{package.title} ({package.points:,} баллов)",
            description=f"Пополнение баланса баллов для рулетки и аукциона ({package.points:,} очков)",
            payload=invoice_payload,
            currency="XTR",
            prices=[LabeledPrice(label=package.title, amount=package.stars)]
        )

        return InvoiceLinkResponse(
            invoice_link=invoice_link,
            package=package
        )
    except Exception as e:
        logger.error(f"Error creating Telegram Stars invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать ссылку на оплату Звёздами: {str(e)}"
        )

@router.post("/daily-bonus", response_model=DailyBonusResponse)
async def claim_daily_bonus(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.datetime.utcnow()
    if current_user.last_daily_bonus:
        diff = now - current_user.last_daily_bonus
        if diff.total_seconds() < 86400:
            remaining_hours = int((86400 - diff.total_seconds()) // 3600)
            raise HTTPException(
                status_code=400,
                detail=f"Ежедневный бонус уже получен! Следующий через {remaining_hours} ч."
            )

    bonus_points = 100
    current_user.points_balance = (current_user.points_balance or 0) + bonus_points
    current_user.last_daily_bonus = now

    tx = PaymentTransaction(
        telegram_id=current_user.telegram_id,
        provider="daily_bonus",
        points_credited=bonus_points,
        payload="daily_bonus_100",
        status="completed"
    )
    db.add(tx)
    await db.commit()

    return DailyBonusResponse(
        success=True,
        points_credited=bonus_points,
        new_balance=current_user.points_balance,
        message=f"+{bonus_points} баллов начислено за ежедневный вход!"
    )

@router.post("/link-twitch")
async def link_twitch_account(
    req: LinkTwitchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cleaned = req.twitch_username.strip().replace("@", "").lower()
    if not cleaned or len(cleaned) < 3:
        raise HTTPException(status_code=400, detail="Укажите корректный никнейм Twitch")

    is_first_time = not bool(current_user.twitch_username)
    current_user.twitch_username = cleaned
    
    # Welcome bonus for linking Twitch
    bonus = 0
    if is_first_time:
        bonus = 250
        current_user.points_balance = (current_user.points_balance or 0) + bonus
        tx = PaymentTransaction(
            telegram_id=current_user.telegram_id,
            provider="twitch_welcome_bonus",
            points_credited=bonus,
            payload=f"twitch_{cleaned}_welcome",
            status="completed"
        )
        db.add(tx)

    await db.commit()
    return {
        "success": True,
        "twitch_username": cleaned,
        "bonus_awarded": bonus,
        "new_balance": current_user.points_balance,
        "message": f"Twitch аккаунт @{cleaned} успешно привязан! {f'+{bonus} приветственных баллов!' if bonus > 0 else ''}"
    }

@router.post("/twitch-claim")
async def claim_twitch_points(
    req: ClaimTwitchPointsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.twitch_username:
        raise HTTPException(status_code=400, detail="Сначала привяжите ваш Twitch-аккаунт!")

    points = max(100, min(req.points, 50000))
    current_user.points_balance = (current_user.points_balance or 0) + points

    tx = PaymentTransaction(
        telegram_id=current_user.telegram_id,
        provider="twitch",
        points_credited=points,
        payload=f"twitch_{current_user.twitch_username}_{points}",
        status="completed"
    )
    db.add(tx)
    await db.commit()

    return {
        "success": True,
        "points_credited": points,
        "new_balance": current_user.points_balance,
        "message": f"+{points:,} баллов Twitch успешно синхронизировано и зачислено!"
    }
