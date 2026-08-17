import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import AuctionItem, User
from app.auth import get_current_user, get_admin_user
from app.schemas import (
    AuctionItemCreate,
    AuctionItemAddPoints,
    AuctionItemOut,
    AuctionStateOut
)

router = APIRouter(prefix="/api/auction", tags=["Auction & Roulette"])

SECTOR_COLORS = [
    "#ec4899", "#8b5cf6", "#3b82f6", "#06b6d4", "#10b981",
    "#f59e0b", "#f43f5e", "#a855f7", "#14b8a6", "#eab308",
    "#6366f1", "#d946ef", "#0ea5e9", "#84cc16", "#fb923c"
]

@router.get("", response_model=AuctionStateOut)
async def get_auction_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns current auction state with items and computed winning/elimination chances."""
    result = await db.execute(
        select(AuctionItem).order_by(AuctionItem.points.desc(), AuctionItem.created_at.asc())
    )
    items = result.scalars().all()

    active_items = [it for it in items if it.is_active]
    total_active_points = sum(it.points for it in active_items)

    out_items = []
    for item in items:
        if item.is_active and total_active_points > 0:
            chance = round((item.points / total_active_points) * 100, 1)
        else:
            chance = 0.0

        out_items.append(AuctionItemOut(
            id=item.id,
            title=item.title,
            user_name=item.user_name,
            points=item.points,
            color=item.color,
            is_active=item.is_active,
            chance_percent=chance,
            created_at=item.created_at
        ))

    return AuctionStateOut(
        items=out_items,
        total_points=total_active_points,
        active_count=len(active_items)
    )


@router.post("/items", response_model=AuctionItemOut)
async def create_auction_item(
    item_in: AuctionItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Adds a new item/game/movie to the auction."""
    user_name = item_in.user_name or current_user.first_name
    if current_user.last_name and not item_in.user_name:
        user_name += f" {current_user.last_name}"

    color = item_in.color or random.choice(SECTOR_COLORS)
    points = max(100, item_in.points)

    new_item = AuctionItem(
        title=item_in.title.strip(),
        user_name=user_name.strip(),
        points=points,
        color=color,
        is_active=True
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    return AuctionItemOut(
        id=new_item.id,
        title=new_item.title,
        user_name=new_item.user_name,
        points=new_item.points,
        color=new_item.color,
        is_active=new_item.is_active,
        chance_percent=100.0,
        created_at=new_item.created_at
    )


@router.post("/items/{item_id}/add-points", response_model=AuctionItemOut)
async def add_points_to_item(
    item_id: int,
    payload: AuctionItemAddPoints,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Adds channel points to an existing auction item (increases sector size)."""
    result = await db.execute(select(AuctionItem).where(AuctionItem.id == item_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Лот не найден")

    item.points = max(100, item.points + payload.points)
    item.is_active = True  # Reactivate if points added
    await db.commit()
    await db.refresh(item)

    return AuctionItemOut(
        id=item.id,
        title=item.title,
        user_name=item.user_name,
        points=item.points,
        color=item.color,
        is_active=item.is_active,
        chance_percent=0.0,
        created_at=item.created_at
    )


@router.post("/items/{item_id}/toggle-active", response_model=AuctionItemOut)
async def toggle_item_active(
    item_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggles item active state (for Elimination / Drop mode)."""
    result = await db.execute(select(AuctionItem).where(AuctionItem.id == item_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Лот не найден")

    item.is_active = not item.is_active
    await db.commit()
    await db.refresh(item)

    return AuctionItemOut(
        id=item.id,
        title=item.title,
        user_name=item.user_name,
        points=item.points,
        color=item.color,
        is_active=item.is_active,
        chance_percent=0.0,
        created_at=item.created_at
    )


@router.delete("/items/{item_id}")
async def delete_auction_item(
    item_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes an item from the auction (Admin)."""
    result = await db.execute(select(AuctionItem).where(AuctionItem.id == item_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Лот не найден")

    await db.delete(item)
    await db.commit()
    return {"success": True, "message": f"Лот #{item_id} удален"}


@router.post("/reset")
async def reset_auction(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Clears all items from the auction wheel (Admin)."""
    result = await db.execute(select(AuctionItem))
    items = result.scalars().all()
    for item in items:
        await db.delete(item)
    await db.commit()
    return {"success": True, "message": "Аукцион очищен"}
