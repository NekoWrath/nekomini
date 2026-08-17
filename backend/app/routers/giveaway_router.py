import datetime
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models import User, Giveaway, GiveawayTicket
from app.schemas import GiveawayCreate, GiveawayUpdate, GiveawayOut, BuyTicketsRequest
from app.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/api/giveaways", tags=["giveaways"])
admin_router = APIRouter(prefix="/api/admin/giveaways", tags=["admin-giveaways"])


# ==================== Public Viewer Endpoints ====================

@router.get("", response_model=List[GiveawayOut])
async def list_giveaways(
    status_filter: Optional[str] = Query(None, description="active, completed, or all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns list of active and recent giveaways with user's ticket counts and win chance."""
    query = select(Giveaway)
    if status_filter and status_filter != "all":
        query = query.where(Giveaway.status == status_filter)

    query = query.order_by(
        desc(Giveaway.status == "active"),
        desc(Giveaway.created_at)
    )

    res = await db.execute(query)
    giveaways = res.scalars().all()

    output = []
    for g in giveaways:
        t_res = await db.execute(
            select(func.count(GiveawayTicket.id)).where(
                GiveawayTicket.giveaway_id == g.id,
                GiveawayTicket.user_telegram_id == current_user.telegram_id
            )
        )
        user_tickets = t_res.scalar() or 0

        total = g.total_tickets or 0
        chance = round((user_tickets / total * 100.0), 1) if total > 0 and user_tickets > 0 else 0.0

        out_item = GiveawayOut(
            id=g.id,
            title=g.title,
            description=g.description or "",
            image_url=g.image_url,
            ticket_price=g.ticket_price,
            max_tickets_per_user=g.max_tickets_per_user,
            end_time=g.end_time,
            status=g.status,
            winner_telegram_id=g.winner_telegram_id,
            winner_name=g.winner_name,
            winner_avatar=g.winner_avatar,
            winning_ticket_number=g.winning_ticket_number,
            total_tickets=g.total_tickets or 0,
            user_tickets_count=user_tickets,
            user_win_chance_percent=chance,
            created_at=g.created_at
        )
        output.append(out_item)

    return output


@router.get("/{giveaway_id}", response_model=GiveawayOut)
async def get_giveaway_details(
    giveaway_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns details of a specific giveaway."""
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    g = res.scalars().first()
    if not g:
        raise HTTPException(status_code=404, detail="Розыгрыш не найден")

    t_res = await db.execute(
        select(func.count(GiveawayTicket.id)).where(
            GiveawayTicket.giveaway_id == g.id,
            GiveawayTicket.user_telegram_id == current_user.telegram_id
        )
    )
    user_tickets = t_res.scalar() or 0
    total = g.total_tickets or 0
    chance = round((user_tickets / total * 100.0), 1) if total > 0 and user_tickets > 0 else 0.0

    return GiveawayOut(
        id=g.id,
        title=g.title,
        description=g.description or "",
        image_url=g.image_url,
        ticket_price=g.ticket_price,
        max_tickets_per_user=g.max_tickets_per_user,
        end_time=g.end_time,
        status=g.status,
        winner_telegram_id=g.winner_telegram_id,
        winner_name=g.winner_name,
        winner_avatar=g.winner_avatar,
        winning_ticket_number=g.winning_ticket_number,
        total_tickets=g.total_tickets or 0,
        user_tickets_count=user_tickets,
        user_win_chance_percent=chance,
        created_at=g.created_at
    )


@router.post("/{giveaway_id}/buy-tickets")
async def buy_giveaway_tickets(
    giveaway_id: int,
    req: BuyTicketsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Buys one or multiple tickets for a giveaway using points balance."""
    tickets_count = req.tickets_count
    if tickets_count < 1:
        raise HTTPException(status_code=400, detail="Количество билетов должно быть не менее 1")
    if tickets_count > 100:
        raise HTTPException(status_code=400, detail="За один раз можно купить не более 100 билетов")

    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    g = res.scalars().first()
    if not g:
        raise HTTPException(status_code=404, detail="Розыгрыш не найден")

    if g.status != "active":
        raise HTTPException(status_code=400, detail="Этот розыгрыш уже завершен или отменен")

    if g.end_time and g.end_time < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Время розыгрыша истекло")

    # Check user's current tickets in this giveaway
    t_res = await db.execute(
        select(func.count(GiveawayTicket.id)).where(
            GiveawayTicket.giveaway_id == g.id,
            GiveawayTicket.user_telegram_id == current_user.telegram_id
        )
    )
    current_user_tickets = t_res.scalar() or 0

    if g.max_tickets_per_user and (current_user_tickets + tickets_count > g.max_tickets_per_user):
        remaining_allowed = max(0, g.max_tickets_per_user - current_user_tickets)
        raise HTTPException(
            status_code=400,
            detail=f"Лимит на человека: {g.max_tickets_per_user} билетов. Вы можете докупить еще только {remaining_allowed} шт."
        )

    # Check points balance
    total_cost = tickets_count * g.ticket_price
    user_points = current_user.points_balance or 0
    if user_points < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно баллов! Нужно {total_cost:,} PTS, у вас на балансе {user_points:,} PTS."
        )

    # Deduct points
    current_user.points_balance = user_points - total_cost

    # Issue tickets with consecutive numbers
    start_num = (g.total_tickets or 0) + 1
    for i in range(tickets_count):
        ticket = GiveawayTicket(
            giveaway_id=g.id,
            user_telegram_id=current_user.telegram_id,
            ticket_number=start_num + i
        )
        db.add(ticket)

    g.total_tickets = (g.total_tickets or 0) + tickets_count

    await db.commit()
    await db.refresh(g)
    await db.refresh(current_user)

    total = g.total_tickets or 0
    new_user_total = current_user_tickets + tickets_count
    chance = round((new_user_total / total * 100.0), 1) if total > 0 else 100.0

    return {
        "success": True,
        "tickets_bought": tickets_count,
        "total_cost": total_cost,
        "new_points_balance": current_user.points_balance,
        "user_tickets_count": new_user_total,
        "giveaway_total_tickets": g.total_tickets,
        "user_win_chance_percent": chance,
        "message": f"🎉 Вы успешно купили {tickets_count} билет(ов) за {total_cost:,} PTS! Ваш шанс: {chance}%"
    }


# ==================== Admin Endpoints ====================

@admin_router.post("", response_model=GiveawayOut)
async def create_giveaway(
    req: GiveawayCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new giveaway."""
    # 1. Parse ticket price
    try:
        t_price = max(1, int(req.ticket_price)) if req.ticket_price is not None else 100
    except Exception:
        t_price = 100

    # 2. Parse max tickets per user
    try:
        m_tickets = int(req.max_tickets_per_user) if (req.max_tickets_per_user is not None and str(req.max_tickets_per_user).strip() != "") else None
        if m_tickets is not None and m_tickets <= 0:
            m_tickets = None
    except Exception:
        m_tickets = None

    # 3. Parse end time
    end_time_val = None
    if req.end_time:
        if isinstance(req.end_time, datetime.datetime):
            end_time_val = req.end_time
        elif isinstance(req.end_time, str) and req.end_time.strip():
            try:
                clean_str = req.end_time.strip().replace("Z", "+00:00")
                end_time_val = datetime.datetime.fromisoformat(clean_str)
            except Exception:
                try:
                    end_time_val = datetime.datetime.strptime(req.end_time[:16], "%Y-%m-%dT%H:%M")
                except Exception:
                    end_time_val = datetime.datetime.utcnow() + datetime.timedelta(days=3)

    if not end_time_val:
        end_time_val = datetime.datetime.utcnow() + datetime.timedelta(days=3)

    if hasattr(end_time_val, "tzinfo") and end_time_val.tzinfo is not None:
        end_time_val = end_time_val.replace(tzinfo=None)

    giveaway = Giveaway(
        title=req.title.strip(),
        description=req.description or "",
        image_url=req.image_url,
        ticket_price=t_price,
        max_tickets_per_user=m_tickets,
        end_time=end_time_val,
        status="active",
        total_tickets=0
    )
    db.add(giveaway)
    await db.commit()
    await db.refresh(giveaway)

    return GiveawayOut(
        id=giveaway.id,
        title=giveaway.title,
        description=giveaway.description or "",
        image_url=giveaway.image_url,
        ticket_price=giveaway.ticket_price,
        max_tickets_per_user=giveaway.max_tickets_per_user,
        end_time=giveaway.end_time,
        status=giveaway.status,
        winner_telegram_id=None,
        winner_name=None,
        winner_avatar=None,
        winning_ticket_number=None,
        total_tickets=0,
        user_tickets_count=0,
        user_win_chance_percent=0.0,
        created_at=giveaway.created_at
    )


@admin_router.put("/{giveaway_id}", response_model=GiveawayOut)
async def update_giveaway(
    giveaway_id: int,
    req: GiveawayUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates giveaway details."""
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    g = res.scalars().first()
    if not g:
        raise HTTPException(status_code=404, detail="Розыгрыш не найден")

    if req.title is not None:
        g.title = req.title.strip()
    if req.description is not None:
        g.description = req.description
    if req.image_url is not None:
        g.image_url = req.image_url
    if req.ticket_price is not None:
        try:
            g.ticket_price = max(1, int(req.ticket_price))
        except Exception:
            pass
    if req.max_tickets_per_user is not None:
        try:
            m = int(req.max_tickets_per_user)
            g.max_tickets_per_user = m if m > 0 else None
        except Exception:
            pass
    if req.end_time is not None:
        end_time_val = None
        if isinstance(req.end_time, datetime.datetime):
            end_time_val = req.end_time
        elif isinstance(req.end_time, str) and req.end_time.strip():
            try:
                clean_str = req.end_time.strip().replace("Z", "+00:00")
                end_time_val = datetime.datetime.fromisoformat(clean_str)
            except Exception:
                try:
                    end_time_val = datetime.datetime.strptime(req.end_time[:16], "%Y-%m-%dT%H:%M")
                except Exception:
                    pass
        if end_time_val:
            if hasattr(end_time_val, "tzinfo") and end_time_val.tzinfo is not None:
                end_time_val = end_time_val.replace(tzinfo=None)
            g.end_time = end_time_val
    if req.status is not None:
        g.status = req.status

    await db.commit()
    await db.refresh(g)

    return GiveawayOut(
        id=g.id,
        title=g.title,
        description=g.description or "",
        image_url=g.image_url,
        ticket_price=g.ticket_price,
        max_tickets_per_user=g.max_tickets_per_user,
        end_time=g.end_time,
        status=g.status,
        winner_telegram_id=g.winner_telegram_id,
        winner_name=g.winner_name,
        winner_avatar=g.winner_avatar,
        winning_ticket_number=g.winning_ticket_number,
        total_tickets=g.total_tickets or 0,
        user_tickets_count=0,
        user_win_chance_percent=0.0,
        created_at=g.created_at
    )


@admin_router.post("/{giveaway_id}/pick-winner")
async def pick_giveaway_winner(
    giveaway_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Picks a random winner from all purchased tickets for the giveaway."""
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    g = res.scalars().first()
    if not g:
        raise HTTPException(status_code=404, detail="Розыгрыш не найден")

    t_res = await db.execute(select(GiveawayTicket).where(GiveawayTicket.giveaway_id == g.id))
    tickets = t_res.scalars().all()

    if not tickets:
        g.status = "completed"
        g.winner_name = "Нет участников"
        await db.commit()
        return {
            "success": True,
            "has_winner": False,
            "message": "В розыгрыше не было участников. Статус изменен на завершенный."
        }

    winning_ticket = secrets.choice(tickets)

    u_res = await db.execute(select(User).where(User.telegram_id == winning_ticket.user_telegram_id))
    winner = u_res.scalars().first()

    winner_display = "Зритель"
    winner_avatar = None
    if winner:
        if winner.username:
            winner_display = f"@{winner.username}"
        elif winner.first_name:
            winner_display = f"{winner.first_name} {winner.last_name or ''}".strip()
        winner_avatar = winner.photo_url or winner.twitch_avatar

    g.winner_telegram_id = winning_ticket.user_telegram_id
    g.winner_name = winner_display
    g.winner_avatar = winner_avatar
    g.winning_ticket_number = winning_ticket.ticket_number
    g.status = "completed"

    await db.commit()
    await db.refresh(g)

    return {
        "success": True,
        "has_winner": True,
        "winner_telegram_id": g.winner_telegram_id,
        "winner_name": g.winner_name,
        "winner_avatar": g.winner_avatar,
        "winning_ticket_number": g.winning_ticket_number,
        "total_tickets": len(tickets),
        "message": f"🎉 Победитель определен: {winner_display} (Билет #{winning_ticket.ticket_number})!"
    }


@admin_router.delete("/{giveaway_id}")
async def delete_giveaway(
    giveaway_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a giveaway and its associated tickets."""
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    g = res.scalars().first()
    if not g:
        raise HTTPException(status_code=404, detail="Розыгрыш не найден")

    await db.delete(g)
    await db.commit()
    return {"success": True, "message": "Розыгрыш удален"}
