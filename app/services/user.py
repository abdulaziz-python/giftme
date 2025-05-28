from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.database import User
from aiogram.types import User as TelegramUser
from datetime import datetime
from typing import Optional

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_user(self, telegram_user: TelegramUser) -> User:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                is_premium=telegram_user.is_premium or False,
                is_bot=telegram_user.is_bot or False
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        else:
            user.username = telegram_user.username
            user.first_name = telegram_user.first_name
            user.last_name = telegram_user.last_name
            user.is_premium = telegram_user.is_premium or False
            await self.session.commit()
        
        return user
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def update_last_activity(self, telegram_id: int):
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_activity=datetime.utcnow())
        )
        await self.session.commit()
    
    async def block_user(self, telegram_id: int):
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_blocked=True)
        )
        await self.session.commit()
    
    async def unblock_user(self, telegram_id: int):
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_blocked=False)
        )
        await self.session.commit()
