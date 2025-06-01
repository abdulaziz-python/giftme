from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from app.models.database import User, WonGift
from aiogram.types import User as TelegramUser
from datetime import datetime
from typing import Optional, List

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
                    last_activity=datetime.utcnow(),
                    is_blocked=False,
                    reminder_sent_at=None
                )
                self.session.add(user)
                await self.session.commit()
                await self.session.refresh(user)
            else:
                user.username = telegram_user.username
                user.first_name = telegram_user.first_name
                user.last_name = telegram_user.last_name
                user.is_premium = getattr(telegram_user, 'is_premium', False)
                user.language_code = getattr(telegram_user, 'language_code', 'en')
                user.last_activity = datetime.utcnow()
                user.reminder_sent_at = None
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
                .values(
                    last_activity=datetime.utcnow(),
                    reminder_sent_at=None
                )
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

    async def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    async def get_user_won_gifts(self, telegram_id: int) -> List[WonGift]:
        try:
            result = await self.session.execute(
                select(WonGift)
                .options(selectinload(WonGift.gift))
                .where(WonGift.user_id == telegram_id)
                .order_by(WonGift.won_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error getting user won gifts: {e}")
            return []

    async def get_user_count(self) -> int:
        try:
            result = await self.session.execute(select(func.count(User.id)))
            return result.scalar() or 0
        except Exception as e:
            print(f"Error getting user count: {e}")
            return 0

    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        try:
            result = await self.session.execute(
                select(User)
                .order_by(User.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    async def block_user(self, telegram_id: int) -> bool:
        try:
            await self.session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(is_blocked=True)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            print(f"Error blocking user: {e}")
            return False

    async def unblock_user(self, telegram_id: int) -> bool:
        try:
            await self.session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(is_blocked=False)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            print(f"Error unblocking user: {e}")
            return False
