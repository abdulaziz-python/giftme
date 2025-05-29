from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.core.config import settings
from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.handlers import start, admin, payments

def create_bot() -> Bot:
    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    
    # Register middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # Register handlers
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(payments.router)
    
    return dp
