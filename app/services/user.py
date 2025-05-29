from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from app.models.database import User, UserGift
from aiogram.types import User as TelegramUser
from datetime import datetime
from typing import Optional

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, telegram_user: TelegramUser) -> User:
        try:
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
                    is_premium=getattr(telegram_user, 'is_premium', False),
                    language_code=getattr(telegram_user, 'language_code', 'en'),
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                )
                self.session.add(user)
                await self.session.commit()
                await self.session.refresh(user)
            else:
                # Update user info
                user.username = telegram_user.username
                user.first_name = telegram_user.first_name
                user.last_name = telegram_user.last_name
                user.is_premium = getattr(telegram_user, 'is_premium', False)
                user.language_code = getattr(telegram_user, 'language_code', 'en')
                await self.session.commit()
            
            return user
        except Exception as e:
            await self.session.rollback()
            print(f"Error in get_or_create_user: {e}")
            raise

    async def update_last_activity(self, telegram_id: int):
        try:
            await self.session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(last_activity=datetime.utcnow())
            )
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            print(f"Error updating last activity: {e}")

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting user by telegram_id: {e}")
            return None

    async def get_user_gifts(self, telegram_id: int):
        try:
            result = await self.session.execute(
                select(User)
                .options(selectinload(User.gifts))
                .where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            return user.gifts if user else []
        except Exception as e:
            print(f"Error getting user gifts: {e}")
            return []

    async def get_total_users(self) -> int:
        try:
            result = await self.session.execute(select(func.count(User.id)))
            return result.scalar() or 0
        except Exception as e:
            print(f"Error getting total users: {e}")
            return 0
