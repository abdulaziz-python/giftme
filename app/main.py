from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import os
from datetime import datetime
from app.core.config import settings
from app.core.database import init_db
from app.api import api_router
from app.services.gift import GiftService
from app.services.admin import AdminService
from app.core.database import async_session_maker

# Bot initialization
bot = None
dp = None

if settings.BOT_TOKEN:
    try:
        from app.bot import create_bot, create_dispatcher
        bot = create_bot()
        dp = create_dispatcher()
        print("✅ Bot initialized successfully")
    except Exception as e:
        print(f"⚠️ Bot initialization failed: {e}")
else:
    print("⚠️ BOT_TOKEN not provided, bot will not start")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Create directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHARTS_DIR, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # Seed data
    try:
        async with async_session_maker() as session:
            gift_service = GiftService(session)
            await gift_service.seed_gifts()
            
            admin_service = AdminService(session)
            await admin_service.seed_initial_admins()
        print("✅ Data seeded successfully")
    except Exception as e:
        print(f"⚠️ Data seeding failed: {e}")
    
    # Start bot
    if bot and dp:
        try:
            if settings.WEBHOOK_URL:
                await bot.set_webhook(
                    url=f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}",
                    allowed_updates=dp.resolve_used_update_types()
                )
                print(f"✅ Webhook set: {settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}")
            else:
                asyncio.create_task(dp.start_polling(bot))
                print("✅ Bot started in polling mode")
        except Exception as e:
            print(f"❌ Bot start failed: {e}")
    
    print("🚀 Application started successfully")
    
    yield
    
    # Cleanup
    if bot:
        try:
            await bot.session.close()
            print("✅ Bot session closed")
        except Exception as e:
            print(f"⚠️ Bot cleanup error: {e}")

app = FastAPI(
    title="🎰 Telegram Gift Roulette Bot API",
    description="""
    ## Professional Telegram Bot with Mini App for Gift Roulette Game
    
    ### Features:
    - 🎰 **Roulette Game**: Spin to win amazing gifts
    - 👥 **User Management**: Complete user analytics and management
    - 🎁 **Gift System**: Weighted probability gift distribution
    - 👑 **Admin Panel**: Comprehensive admin management
    - 📊 **Analytics**: Real-time statistics and charts
    - 💳 **Payments**: Telegram Stars integration
    - 📱 **Mini App**: Seamless Telegram Web App experience
    
    ### Authentication:
    Most endpoints require Telegram authentication via `X-Init-Data` header.
    
    ### Getting Started:
    1. Start the bot in Telegram
    2. Use the Web App to interact with the API
    3. Check the roulette endpoints to test functionality
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
try:
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
    if os.path.exists(settings.UPLOAD_DIR):
        app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    if os.path.exists(settings.CHARTS_DIR):
        app.mount("/charts", StaticFiles(directory=settings.CHARTS_DIR), name="charts")
except Exception as e:
    print(f"⚠️ Static files mount error: {e}")

# Include API routes
app.include_router(api_router)

@app.post(settings.WEBHOOK_PATH)
async def webhook_handler(request: Request):
    """Telegram webhook handler"""
    if not bot or not dp:
        return {"status": "bot_not_configured"}
    
    try:
        update_data = await request.json()
        await dp.feed_webhook_update(bot, update_data)
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "bot_configured": bot is not None,
        "database_configured": bool(settings.DATABASE_URL)
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
