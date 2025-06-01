from fastapi import APIRouter
from app.api.routes import roulette, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(roulette.router)
api_router.include_router(users.router)
