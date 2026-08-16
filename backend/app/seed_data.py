import datetime
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import AsyncSessionLocal
from app.models import User, Stream, Suggestion, SuggestionVote
from app.config import settings

async def seed_initial_data():
    """Seeds the database with realistic sample streams and suggestions if empty."""
    async with AsyncSessionLocal() as db:
        streams_count = await db.scalar(select(func.count(Stream.id)))
        if streams_count and streams_count > 0:
            return

        now = datetime.datetime.utcnow()

        # Create Admin User if configured
        admin_id = settings.admin_ids[0] if settings.admin_ids else 123456789
        admin_user = User(
            telegram_id=admin_id,
            username="streamer_boss",
            first_name=settings.STREAMER_NAME,
            last_name="🔥",
            photo_url=settings.STREAMER_AVATAR,
            role="admin",
            notify_stream_start=True,
            notify_announcements=True,
            notify_answers=True
        )
        db.add(admin_user)

        # Create Sample Viewer Users
        v1 = User(
            telegram_id=987654321,
            username="cyber_samurai",
            first_name="Алексей",
            last_name="Смирнов",
            photo_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&auto=format&fit=crop&q=80",
            role="viewer"
        )
        v2 = User(
            telegram_id=555444333,
            username="neon_cat",
            first_name="Мария",
            last_name="",
            photo_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80",
            role="viewer"
        )
        v3 = User(
            telegram_id=777888999,
            username="dota_enjoyer",
            first_name="Дмитрий",
            last_name="К.",
            photo_url="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100&auto=format&fit=crop&q=80",
            role="viewer"
        )
        db.add_all([v1, v2, v3])
        await db.commit()

        # Create Sample Streams
        # 1. Today/Soon Stream
        s1 = Stream(
            title="🎮 GRAND TOURNAMENT: Финал турнира по CS2 + Розыгрыш скинов!",
            description="Смотрим финальные матчи турнира, комментируем в прямом эфире и разыгрываем ножи среди зрителей в чате!",
            game_category="Counter-Strike 2",
            platform="Twitch",
            platform_url=settings.TWITCH_URL,
            start_time=now + datetime.timedelta(hours=2, minutes=30),
            is_live=False,
            status="scheduled",
            preview_image_url="https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80",
            tags="турнир,cs2,розыгрыш,ножи",
            viewers_count=1420
        )

        # 2. Tomorrow Stream
        s2 = Stream(
            title="🎙️ JUST CHATTING: Обсуждаем новинки недели + Секретный гость!",
            description="Ламповый вечер, ответы на вопросы из предложки и проверка инди-хорроров.",
            game_category="Just Chatting",
            platform="Kick",
            platform_url=settings.KICK_URL,
            start_time=now + datetime.timedelta(days=1, hours=4),
            is_live=False,
            status="scheduled",
            preview_image_url="https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&auto=format&fit=crop&q=80",
            tags="чилл,вопросы,гость,подкаст",
            viewers_count=850
        )

        # 3. Day after tomorrow Stream
        s3 = Stream(
            title="💀 HARDCORE: Прохождение ELDEN RING без смертей на бананах!",
            description="Безумный челлендж от зрителей. Если умираю — сабгифт 50 сабок!",
            game_category="Elden Ring",
            platform="Twitch",
            platform_url=settings.TWITCH_URL,
            start_time=now + datetime.timedelta(days=2, hours=5),
            is_live=False,
            status="scheduled",
            preview_image_url="https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&auto=format&fit=crop&q=80",
            tags="челлендж,hardcore,rage,gameplay",
            viewers_count=2100
        )

        # 4. Weekend Stream
        s4 = Stream(
            title="🔥 СТРИМ С ПОДПИСЧИКАМИ: Кастомки в Dota 2 и Jackbox Party",
            description="Играем со всеми зрителями с голосовым в Discord!",
            game_category="Dota 2",
            platform="VK Video",
            platform_url=settings.VK_URL,
            start_time=now + datetime.timedelta(days=4, hours=3),
            is_live=False,
            status="scheduled",
            preview_image_url="https://images.unsplash.com/photo-1560253023-3ec5d502959f?w=800&auto=format&fit=crop&q=80",
            tags="кастомки,пати,discord,jackbox",
            viewers_count=1200
        )

        db.add_all([s1, s2, s3, s4])
        await db.commit()

        # Create Sample Suggestions
        sug1 = Suggestion(
            telegram_id=v1.telegram_id,
            author_name="Алексей Смирнов",
            author_username="cyber_samurai",
            author_avatar=v1.photo_url,
            category="challenge",
            title="Пройти хоррор с пульсометром на экране!",
            content="Сыграй в Outlast или Resident Evil Village с кардиодатчиком на экране: каждый раз, когда пульс выше 130 — донатишь в благотворительный фонд!",
            upvotes_count=42,
            status="accepted",
            admin_reply="Супер идея! Взял на пятничный стрим, датчик уже заказал! 🎯",
            replied_at=now - datetime.timedelta(hours=5),
            created_at=now - datetime.timedelta(days=2)
        )

        sug2 = Suggestion(
            telegram_id=v2.telegram_id,
            author_name="Мария",
            author_username="neon_cat",
            author_avatar=v2.photo_url,
            category="question",
            title="Какое твоё самое яркое воспоминание с первых стримов 5 лет назад?",
            content="Расскажи на ближайшем Just Chatting, как ты начинал, было ли страшно говорить в пустоту и сколько было зрителей на первом эфире?",
            upvotes_count=28,
            status="answered",
            admin_reply="Отличный вопрос, подробно расскажу на ламповом эфире в субботу!",
            replied_at=now - datetime.timedelta(hours=12),
            created_at=now - datetime.timedelta(days=1)
        )

        sug3 = Suggestion(
            telegram_id=v3.telegram_id,
            author_name="Дмитрий К.",
            author_username="dota_enjoyer",
            author_avatar=v3.photo_url,
            category="game_idea",
            title="Попробуй кооперативный инди-хит 'Lethal Company' со зрителями",
            content="Очень угарная игра на 4 человека, где нужно собирать лут на заброшенных лунах и спасаться от монстров. Будет много смешных клипов!",
            upvotes_count=19,
            status="pending",
            created_at=now - datetime.timedelta(hours=3)
        )

        sug4 = Suggestion(
            telegram_id=v1.telegram_id,
            author_name="Алексей Смирнов",
            author_username="cyber_samurai",
            author_avatar=v1.photo_url,
            category="other",
            title="Сделай мерч с твоей коронной фразой!",
            content="Давно пора выпустить худи или оверсайз футболки с фирменным логотипом и артом. Сделай опрос среди зрителей!",
            upvotes_count=35,
            status="pending",
            created_at=now - datetime.timedelta(hours=18)
        )

        db.add_all([sug1, sug2, sug3, sug4])
        await db.commit()

        # Add initial votes
        v1_vote = SuggestionVote(telegram_id=v1.telegram_id, suggestion_id=sug1.id)
        v2_vote = SuggestionVote(telegram_id=v2.telegram_id, suggestion_id=sug1.id)
        v3_vote = SuggestionVote(telegram_id=v3.telegram_id, suggestion_id=sug2.id)
        db.add_all([v1_vote, v2_vote, v3_vote])
        await db.commit()
