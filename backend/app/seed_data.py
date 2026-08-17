import logging
from sqlalchemy.future import select
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models import Stream, Suggestion, SuggestionVote

logger = logging.getLogger(__name__)

async def seed_initial_data():
    """
    Cleans up any old placeholder/demo streams and suggestions,
    leaving the database clean and ready for real streamer usage.
    """
    async with AsyncSessionLocal() as db:
        # Delete demo streams if present
        demo_titles = [
            "🎮 GRAND TOURNAMENT: Финал турнира по CS2 + Розыгрыш скинов!",
            "🎙️ JUST CHATTING: Обсуждаем новинки недели + Секретный гость!",
            "💀 HARDCORE: Прохождение ELDEN RING без смертей на бананах!",
            "🔥 СТРИМ С ПОДПИСЧИКАМИ: Кастомки в Dota 2 и Jackbox Party"
        ]
        
        for title in demo_titles:
            await db.execute(delete(Stream).where(Stream.title == title))

        # Delete demo suggestions if present
        demo_sug_titles = [
            "Пройти хоррор с пульсометром на экране!",
            "Какое твоё самое яркое воспоминание с первых стримов 5 лет назад?",
            "Попробуй кооперативный инди-хит 'Lethal Company' со зрителями",
            "Сделай мерч с твоей коронной фразой!"
        ]
        for title in demo_sug_titles:
            await db.execute(delete(Suggestion).where(Suggestion.title == title))

        await db.commit()
        logger.info("Clean database ready: demo filler data removed.")
