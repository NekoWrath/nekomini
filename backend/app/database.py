import re
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

def prepare_async_db(raw_url: str):
    if not raw_url or "sqlite" in raw_url:
        return "sqlite+aiosqlite:///./tma_streamer.db", {"check_same_thread": False}

    url = raw_url.strip().strip("'").strip('"')
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    connect_args = {}
    if "postgresql+asyncpg" in url:
        connect_args["ssl"] = "require"
        if "?sslmode=" in url or "&sslmode=" in url:
            url = re.sub(r'[?&]sslmode=[^&]+', '', url)
            if '?' not in url and '&' in url:
                url = url.replace('&', '?', 1)

    return url, connect_args

db_url, db_connect_args = prepare_async_db(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=db_connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
