from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.database import Admin, User
from app.core.config import settings
from typing import List, Optional
from aiogram.types import User as TelegramUser

class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def is_admin(self, user_id: int = None, username: str = None) -> bool:
        if user_id in settings.ADMIN_IDS:
            return True
        
        if username and username in settings.ADMIN_USERNAMES:
            return True
        
        if user_id:
            result = await self.session.execute(
                select(Admin).where(
                    Admin.telegram_id == user_id,
                    Admin.is_active == True
                )
            )
            return result.scalar_one_or_none() is not None
        
        return False
    
    async def add_admin(self, telegram_user: TelegramUser, added_by: int) -> Admin:
        existing_admin = await self.session.execute(
            select(Admin).where(Admin.telegram_id == telegram_user.id)
        )
        
        if existing_admin.scalar_one_or_none():
            raise ValueError("User is already an admin")
        
        admin = Admin(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            added_by=added_by
        )
        
        self.session.add(admin)
        await self.session.commit()
        await self.session.refresh(admin)
        return admin
    
    async def remove_admin(self, telegram_id: int) -> bool:
        result = await self.session.execute(
            update(Admin)
            .where(Admin.telegram_id == telegram_id)
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_all_admins(self) -> List[Admin]:
        result = await self.session.execute(
            select(Admin).where(Admin.is_active == True)
            .order_by(Admin.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_admin_by_id(self, telegram_id: int) -> Optional[Admin]:
        result = await self.session.execute(
            select(Admin).where(
                Admin.telegram_id == telegram_id,
                Admin.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def seed_initial_admins(self):
        for username in settings.ADMIN_USERNAMES:
            existing = await self.session.execute(
                select(Admin).where(Admin.username == username)
            )
            if not existing.scalar_one_or_none():
                admin = Admin(
                    telegram_id=0,  # Will be updated when they first use the bot
                    username=username,
                    first_name="Initial Admin",
                    added_by=0
                )
                self.session.add(admin)
        
        await self.session.commit()
