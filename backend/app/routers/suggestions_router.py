import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import get_db
from app.models import Suggestion, SuggestionVote, User
from app.schemas import SuggestionCreate, SuggestionModerate, SuggestionOut
from app.auth import get_current_user, get_admin_user
from app.bot.bot_instance import get_bot
from app.bot.notifications import send_suggestion_reply_notification

router = APIRouter(prefix="/api/suggestions", tags=["Suggestions"])

@router.get("", response_model=List[SuggestionOut])
async def list_suggestions(
    tab: str = Query("new", description="new, popular, answered, my, pending"),
    category: Optional[str] = Query(None, description="game_idea, question, challenge, other"),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists suggestions according to filter tab and category."""
    query = select(Suggestion)

    # Category filter
    if category and category != "all":
        query = query.where(Suggestion.category == category)

    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Suggestion.title.ilike(search_pattern)) | (Suggestion.content.ilike(search_pattern))
        )

    # Tab filters & ordering
    if tab == "popular":
        query = query.where(Suggestion.status != "rejected").order_by(Suggestion.upvotes_count.desc(), Suggestion.created_at.desc())
    elif tab == "my":
        query = query.where(Suggestion.telegram_id == current_user.telegram_id)
        query = query.order_by(Suggestion.created_at.desc())
    elif tab == "pending":
        query = query.where(Suggestion.status == "pending")
        query = query.order_by(Suggestion.created_at.desc())
    else:  # 'new'
        query = query.where(Suggestion.status != "rejected").order_by(Suggestion.created_at.desc())

    result = await db.execute(query)
    suggestions = result.scalars().all()

    # User's votes
    votes_result = await db.execute(
        select(SuggestionVote.suggestion_id).where(SuggestionVote.telegram_id == current_user.telegram_id)
    )
    user_voted_ids = set(votes_result.scalars().all())

    response = []
    for item in suggestions:
        response.append(SuggestionOut(
            id=item.id,
            telegram_id=item.telegram_id,
            author_name=item.author_name,
            author_username=item.author_username,
            author_avatar=item.author_avatar,
            category=item.category,
            title=item.title,
            content=item.content,
            media_url=item.media_url,
            upvotes_count=item.upvotes_count,
            has_voted=item.id in user_voted_ids,
            is_author=item.telegram_id == current_user.telegram_id,
            status=item.status,
            admin_reply=item.admin_reply,
            replied_at=item.replied_at,
            created_at=item.created_at
        ))

    return response


@router.post("", response_model=SuggestionOut)
async def create_suggestion(
    sug_in: SuggestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new suggestion/question from viewer."""
    author_name = current_user.first_name
    if current_user.last_name:
        author_name += f" {current_user.last_name}"
    if not author_name.strip():
        author_name = current_user.username or f"Viewer_{current_user.telegram_id % 1000}"

    new_sug = Suggestion(
        telegram_id=current_user.telegram_id,
        author_name=author_name,
        author_username=current_user.username,
        author_avatar=current_user.photo_url,
        category=sug_in.category,
        title=sug_in.title,
        content=sug_in.content,
        media_url=sug_in.media_url,
        upvotes_count=1,  # Auto 1 upvote from author
        status="pending",
        created_at=datetime.datetime.utcnow()
    )
    db.add(new_sug)
    await db.commit()
    await db.refresh(new_sug)

    # Add auto-vote from creator if not exists
    v_res = await db.execute(
        select(SuggestionVote).where(
            SuggestionVote.telegram_id == current_user.telegram_id,
            SuggestionVote.suggestion_id == new_sug.id
        )
    )
    if not v_res.scalars().first():
        auto_vote = SuggestionVote(
            telegram_id=current_user.telegram_id,
            suggestion_id=new_sug.id
        )
        db.add(auto_vote)
        await db.commit()

    return SuggestionOut(
        id=new_sug.id,
        telegram_id=new_sug.telegram_id,
        author_name=new_sug.author_name,
        author_username=new_sug.author_username,
        author_avatar=new_sug.author_avatar,
        category=new_sug.category,
        title=new_sug.title,
        content=new_sug.content,
        media_url=new_sug.media_url,
        upvotes_count=new_sug.upvotes_count,
        has_voted=True,
        is_author=True,
        status=new_sug.status,
        admin_reply=new_sug.admin_reply,
        replied_at=new_sug.replied_at,
        created_at=new_sug.created_at
    )


@router.post("/{suggestion_id}/vote")
async def vote_suggestion(
    suggestion_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggles upvote for suggestion."""
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    sug = result.scalars().first()
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    vote_result = await db.execute(
        select(SuggestionVote).where(
            SuggestionVote.telegram_id == current_user.telegram_id,
            SuggestionVote.suggestion_id == suggestion_id
        )
    )
    existing_vote = vote_result.scalars().first()

    if existing_vote:
        await db.delete(existing_vote)
        sug.upvotes_count = max(0, sug.upvotes_count - 1)
        has_voted = False
    else:
        new_vote = SuggestionVote(
            telegram_id=current_user.telegram_id,
            suggestion_id=suggestion_id
        )
        db.add(new_vote)
        sug.upvotes_count += 1
        has_voted = True

    await db.commit()
    await db.refresh(sug)

    return {
        "success": True,
        "has_voted": has_voted,
        "upvotes_count": sug.upvotes_count
    }


@router.post("/{suggestion_id}/moderate", response_model=SuggestionOut)
async def moderate_suggestion(
    suggestion_id: int,
    mod_in: SuggestionModerate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Moderates a suggestion and dispatches direct notification to the author via Telegram bot."""
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    sug = result.scalars().first()
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    sug.status = mod_in.status
    if mod_in.admin_reply is not None:
        sug.admin_reply = mod_in.admin_reply
        sug.replied_at = datetime.datetime.utcnow()

    await db.commit()
    await db.refresh(sug)

    # Check author notification settings & send Telegram Bot DM
    author_res = await db.execute(select(User).where(User.telegram_id == sug.telegram_id))
    author = author_res.scalars().first()

    if author and author.notify_answers:
        bot = get_bot()
        await send_suggestion_reply_notification(
            bot=bot,
            telegram_id=author.telegram_id,
            suggestion_title=sug.title,
            status_text=sug.status,
            admin_reply=sug.admin_reply
        )

    return SuggestionOut(
        id=sug.id,
        telegram_id=sug.telegram_id,
        author_name=sug.author_name,
        author_username=sug.author_username,
        author_avatar=sug.author_avatar,
        category=sug.category,
        title=sug.title,
        content=sug.content,
        media_url=sug.media_url,
        upvotes_count=sug.upvotes_count,
        has_voted=False,
        is_author=sug.telegram_id == admin_user.telegram_id,
        status=sug.status,
        admin_reply=sug.admin_reply,
        replied_at=sug.replied_at,
        created_at=sug.created_at
    )


@router.delete("/{suggestion_id}")
async def delete_suggestion(
    suggestion_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes suggestion (Admin or Author)."""
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    sug = result.scalars().first()
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if current_user.role not in ("admin", "moderator") and sug.telegram_id != current_user.telegram_id:
        raise HTTPException(status_code=403, detail="Permission denied")

    await db.delete(sug)
    await db.commit()
    return {"success": True, "message": f"Suggestion {suggestion_id} deleted"}
