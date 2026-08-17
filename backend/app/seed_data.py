import logging
from sqlalchemy.future import select
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models import Stream, Suggestion, SuggestionVote, AuctionItem

logger = logging.getLogger(__name__)

async def seed_initial_data():
    """
    Cleans up filler streams and seeds initial starter auction lots
    so the Roulette Wheel is immediately active and colorful.
    """
    async with AsyncSessionLocal() as db:
        # Delete old filler demo streams if present
        demo_titles = [
            "🎮 GRAND TOURNAMENT: Финал турнира по CS2 + Розыгрыш скинов!",
            "🎙️ JUST CHATTING: Обсуждаем новинки недели + Секретный гость!",
            "💀 HARDCORE: Прохождение ELDEN RING без смертей на бананах!",
            "🔥 СТРИМ С ПОДПИСЧИКАМИ: Кастомки в Dota 2 и Jackbox Party"
        ]
        for title in demo_titles:
            await db.execute(delete(Stream).where(Stream.title == title))

        # Check auction items
        auc_res = await db.execute(select(AuctionItem))
        existing_lots = auc_res.scalars().all()
        if not existing_lots:
            starter_lots = [
                AuctionItem(title="🎮 Elden Ring (Без брони)", user_name="Стример", points=15000, color="#ec4899", is_active=True),
                AuctionItem(title="💀 Хоррор-игра ночью", user_name="Зритель", points=10000, color="#8b5cf6", is_active=True),
                AuctionItem(title="🎬 Смотрим фильм на стриме", user_name="VIP Чат", points=8000, color="#3b82f6", is_active=True),
                AuctionItem(title="🔥 Турнир с подписчиками", user_name="Модератор", points=5000, color="#10b981", is_active=True),
            ]
            db.add_all(starter_lots)

        await db.commit()
        logger.info("Database seeded: initial roulette lots ready.")
