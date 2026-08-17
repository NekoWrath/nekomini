import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.database import engine, Base
from app.seed_data import seed_initial_data
from app.scheduler import start_scheduler, shutdown_scheduler
from app.bot.bot_instance import get_bot, get_dispatcher
from app.bot.handlers import router as bot_router

from app.routers.auth_router import router as auth_router
from app.routers.schedule_router import router as schedule_router
from app.routers.suggestions_router import router as suggestions_router
from app.routers.settings_router import router as settings_router
from app.routers.admin_router import router as admin_router
from app.routers.upload_router import router as upload_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tma-streamer")

bot_task: asyncio.Task = None

async def start_bot_polling():
    """Starts Telegram Bot polling in background."""
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz" or ":" not in settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN is not configured or using default template. Bot polling will start once a valid token is set in backend/.env.")
        return

    try:
        bot = get_bot()
        dp = get_dispatcher()
        
        # Clean any webhook conflicts
        await bot.delete_webhook(drop_pending_updates=True)

        bot_info = await bot.get_me()
        logger.info(f"✅ Telegram Bot @{bot_info.username} (ID: {bot_info.id}) connected successfully!")

        dp.include_router(bot_router)
        logger.info("🚀 Telegram Bot polling started (aiogram 3.x)...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"❌ Telegram bot failed to start: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Database Tables
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_initial_data()
        logger.info("✅ Database tables initialized successfully!")
    except Exception as e:
        logger.error(f"⚠️ Warning: Could not initialize database tables: {e}")

    # 2. Start Background Scheduler (15-30m stream push alerts)
    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"⚠️ Scheduler warning: {e}")

    # 3. Start Telegram Bot in background
    global bot_task
    bot_task = asyncio.create_task(start_bot_polling())

    yield

    # Shutdown sequence
    try:
        shutdown_scheduler()
    except Exception:
        pass

    if bot_task and not bot_task.done():
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

    bot = get_bot()
    if bot and bot.session:
        await bot.session.close()


app = FastAPI(
    title=f"{settings.STREAMER_NAME} Telegram Mini App API",
    version="1.0.0",
    description="Backend API and Bot for Streamer Telegram Mini App",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(schedule_router)
app.include_router(suggestions_router)
app.include_router(settings_router)
app.include_router(admin_router)
app.include_router(upload_router)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Static UI directory
STATIC_DIR = Path(__file__).parent / "app" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_spa():
        """Serves the Telegram Mini App SPA."""
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "status": "online",
            "app": f"{settings.STREAMER_NAME} Mini App Backend",
            "version": "1.0.0",
            "docs_url": "/docs"
        }

from sqlalchemy import text

@app.get("/api/health")
async def health_check():
    """Health check and live database diagnostic endpoint."""
    db_status = "unknown"
    db_type = "postgresql" if "postgresql" in str(engine.url) else "sqlite"
    error = None
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "error"
        error = str(e)

    return {
        "status": "ok",
        "database": {
            "type": db_type,
            "status": db_status,
            "error": error
        },
        "bot_configured": bool(settings.BOT_TOKEN and ":" in settings.BOT_TOKEN and settings.BOT_TOKEN != "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"),
        "admin_ids_count": len(settings.admin_ids)
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG_MODE
    )
