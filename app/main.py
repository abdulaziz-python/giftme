from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import os
from datetime import datetime
from app.core.config import settings
from app.core.database import init_db
from app.api import api_router
from app.bot import create_bot, create_dispatcher
from app.services.gift import GiftService
from app.services.admin_session import AdminSessionService
from app.services.admin import AdminService
from app.core.database import async_session_maker

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHARTS_DIR, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    async with async_session_maker() as session:
        gift_service = GiftService(session)
        await gift_service.seed_gifts()
        
        admin_service = AdminService(session)
        await admin_service.seed_initial_admins()
    
    bot = create_bot()
    dp = create_dispatcher()
    
    if settings.WEBHOOK_URL:
        await bot.set_webhook(
            url=f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}",
            allowed_updates=dp.resolve_used_update_types()
        )
    else:
        asyncio.create_task(dp.start_polling(bot))
    
    async def cleanup_sessions():
        while True:
            try:
                async with async_session_maker() as session:
                    admin_session_service = AdminSessionService(session)
                    await admin_session_service.cleanup_expired_sessions()
                await asyncio.sleep(3600)
            except Exception as e:
                print(f"Session cleanup error: {e}")
                await asyncio.sleep(300)
    
    asyncio.create_task(cleanup_sessions())
    
    yield
    
    await bot.session.close()

app = FastAPI(
    title="Telegram Gift Roulette Bot",
    description="Professional Telegram Bot with Mini App for Gift Roulette Game",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/charts", StaticFiles(directory=settings.CHARTS_DIR), name="charts")

app.include_router(api_router)

@app.post(settings.WEBHOOK_PATH)
async def webhook_handler(request: Request):
    bot = create_bot()
    dp = create_dispatcher()
    
    update_data = await request.json()
    await dp.feed_webhook_update(bot, update_data)
    
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "message": "Telegram Gift Roulette Bot API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
