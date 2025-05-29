from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_session
from app.services.user import UserService
from app.bot.utils.auth import get_user_from_init_data
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])

class UserResponse(BaseModel):
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    language_code: Optional[str]
    is_premium: bool
    is_bot: bool
    is_blocked: bool
    last_activity: datetime
    created_at: datetime

class UserAnalytics(BaseModel):
    total_users: int
    premium_users: int
    active_users_today: int
    blocked_users: int

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    x_init_data: str = Header(..., alias="X-Init-Data"),
    session: AsyncSession = Depends(get_session)
):
    """Get current user information from Telegram init data"""
    user_data = get_user_from_init_data(x_init_data)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data"
        )
    
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(user_data['id'])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_premium=user.is_premium,
        is_bot=user.is_bot,
        is_blocked=user.is_blocked,
        last_activity=user.last_activity,
        created_at=user.created_at
    )

@router.get("/analytics", response_model=UserAnalytics)
async def get_user_analytics(
    session: AsyncSession = Depends(get_session)
):
    """Get user analytics and statistics"""
    user_service = UserService(session)
    
    total_users = await user_service.get_user_count()
    
    # You can add more analytics here
    return UserAnalytics(
        total_users=total_users,
        premium_users=0,  # Implement this
        active_users_today=0,  # Implement this
        blocked_users=0  # Implement this
    )

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """Get all users with pagination"""
    user_service = UserService(session)
    users = await user_service.get_all_users(limit=limit, offset=offset)
    
    return [
        UserResponse(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_premium=user.is_premium,
            is_bot=user.is_bot,
            is_blocked=user.is_blocked,
            last_activity=user.last_activity,
            created_at=user.created_at
        )
        for user in users
    ]
