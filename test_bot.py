#!/usr/bin/env python3
"""
🔍 Telegram Bot Diagnostic & Test Runner
Позволяет быстро проверить токен бота, связь с Telegram API и запустить бота отдельно с подробными логами.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set path
ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Load .env
load_dotenv(BACKEND_DIR / ".env")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("test_bot")

async def test_bot():
    print("""
=============================================================
   🔍 ДИАГНОСТИКА И ТЕСТ ТЕЛЕГРАМ БОТА
=============================================================
""")

    if not BOT_TOKEN or BOT_TOKEN == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz":
        print("❌ ОШИБКА: Токен бота не настроен!")
        print("Откройте backend/.env и вставьте реальный BOT_TOKEN от @BotFather.")
        print("Или запустите ./start.sh для автоматической настройки.")
        return

    print(f"🔑 Проверяем BOT_TOKEN: {BOT_TOKEN[:10]}... (длина: {len(BOT_TOKEN)})")

    try:
        from aiogram import Bot, Dispatcher
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties
        from app.bot.handlers import router as bot_router
        from app.database import engine, Base
        from app.seed_data import seed_initial_data

        # Initialize DB
        print("📦 Инициализация локальной базы данных...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_initial_data()

        # Connect to Telegram
        print("🌐 Подключение к Telegram API...")
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        # Get bot info
        bot_info = await bot.get_me()
        print(f"\n✅ УСПЕШНОЕ ПОДКЛЮЧЕНИЕ К TELEGRAM!")
        print(f"🤖 Имя бота:      {bot_info.first_name}")
        print(f"🔗 Username:      @{bot_info.username}")
        print(f"🆔 ID бота:       {bot_info.id}")
        print(f"👥 Группы:        {'Разрешены' if bot_info.can_join_groups else 'Запрещены'}")

        # Delete any conflicting webhooks
        await bot.delete_webhook(drop_pending_updates=True)
        print("🧹 Очищены старые вебхуки и ожидающие обновления.")

        print(f"\n🚀 Запуск polling (прослушивание команд в Telegram)...")
        print(f"👉 Откройте https://t.me/{bot_info.username} и отправьте /start в чат!\n")
        print("Для остановки нажмите Ctrl + C\n")

        dp = Dispatcher()
        dp.include_router(bot_router)

        await dp.start_polling(bot)

    except Exception as e:
        print(f"\n❌ ОШИБКА ПРИ ЗАПУСКЕ БОТА:")
        print(f"{type(e).__name__}: {e}")
        if "Unauthorized" in str(e) or "Token is invalid" in str(e):
            print("\n💡 ПРИЧИНА: Неверный токен бота. Перепроверьте токен, выданный @BotFather.")
        elif "Cannot connect to host" in str(e) or "timeout" in str(e).lower():
            print("\n💡 ПРИЧИНА: Нет связи с серверами Telegram (api.telegram.org). Проверьте интернет или VPN.")
        elif "Conflict" in str(e):
            print("\n💡 ПРИЧИНА: Бот уже запущен в другом окне/процессе. Закройте другие запущенные копии.")
    finally:
        if 'bot' in locals() and bot.session:
            await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot())
