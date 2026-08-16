from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.config import settings

bot: Bot = None
dp: Dispatcher = None

def get_bot() -> Bot:
    global bot
    if bot is None:
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    return bot

def get_dispatcher() -> Dispatcher:
    global dp
    if dp is None:
        dp = Dispatcher()
    return dp
