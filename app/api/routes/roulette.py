from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_session
from app.api.dependencies import get_current_user
from app.services.gift import GiftService
from app.services.payment import PaymentService
from app.core.config import settings
from typing import List, Dict

router = APIRouter(prefix="/roulette", tags=["roulette"])

class GiftResponse(BaseModel):
    id: int
    gift_id: str
    name: str
    description: str
    star_count: int
    image_url: str

class SpinRequest(BaseModel):
    init_data: str

class SpinResponse(BaseModel):
    session_id: str
    invoice_link: str

class ProfileResponse(BaseModel):
    user_id: int
    username: str
    won_gifts: List[GiftResponse]

@router.get("/gifts", response_model=List[GiftResponse])
async def get_available_gifts(
    session: AsyncSession = Depends(get_session)
):
    gift_service = GiftService(session)
    gifts = await gift_service.get_available_gifts()
    
    return [
        GiftResponse(
            id=gift.id,
            gift_id=gift.gift_id,
            name=gift.name,
            description=gift.description or "",
            star_count=gift.star_count,
            image_url=gift.image_url or ""
        )
        for gift in gifts
    ]

@router.post("/spin", response_model=SpinResponse)
async def create_spin_session(
    request: SpinRequest,
    session: AsyncSession = Depends(get_session)
):
    from app.bot.utils.auth import verify_telegram_auth
    from app.services.user import UserService
    
    auth_data = verify_telegram_auth(request.init_data)
    if not auth_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data"
        )
    
    try:
        user_data = eval(auth_data.get('user', '{}'))
        telegram_id = user_data.get('id')
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data"
        )
    
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(telegram_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    payment_service = PaymentService(session)
    spin_session = await payment_service.create_spin_session(user.telegram_id)
    
    invoice_link = f"https://t.me/{settings.BOT_TOKEN.split(':')[0]}/invoice"
    
    return SpinResponse(
        session_id=spin_session.session_id,
        invoice_link=invoice_link
    )

@router.get("/profile", response_model=ProfileResponse)
async def get_user_profile(
    init_data: str = Header(..., alias="X-Init-Data"),
    session: AsyncSession = Depends(get_session)
):
    from app.bot.utils.auth import verify_telegram_auth
    from app.services.user import UserService
    
    auth_data = verify_telegram_auth(init_data)
    if not auth_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data"
        )
    
    try:
        user_data = eval(auth_data.get('user', '{}'))
        telegram_id = user_data.get('id')
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data"
        )
    
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(telegram_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    gift_service = GiftService(session)
    won_gifts = await gift_service.get_user_won_gifts(user.telegram_id)
    
    gift_responses = []
    for won_gift in won_gifts:
        gift_responses.append(
            GiftResponse(
                id=won_gift.gift.id,
                gift_id=won_gift.gift.gift_id,
                name=won_gift.gift.name,
                description=won_gift.gift.description or "",
                star_count=won_gift.gift.star_count,
                image_url=won_gift.gift.image_url or ""
            )
        )
    
    return ProfileResponse(
        user_id=user.telegram_id,
        username=user.username or "",
        won_gifts=gift_responses
    )

@router.get("/session/{session_id}")
async def get_spin_session_status(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    payment_service = PaymentService(session)
    spin_session = await payment_service.get_spin_session(session_id)
    
    if not spin_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "session_id": spin_session.session_id,
        "status": spin_session.status,
        "created_at": spin_session.created_at,
        "expires_at": spin_session.expires_at
    }
