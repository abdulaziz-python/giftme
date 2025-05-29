from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.database import Admin, User
from app.core.config import settings
from typing import List, Optional

class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_admin(self, telegram_id: int, username: str = None) -> bool:
        if telegram_id in settings.ADMIN_IDS:
            return True
        
        if username and username in settings.ADMIN_USERNAMES:
            return True
        
        result = await self.session.execute(
            select(Admin).where(
                Admin.telegram_id == telegram_id,
                Admin.is_active == True
            )
        )
        admin = result.scalar_one_or_none()
        return admin is not None

    async def add_admin(self, telegram_id: int, added_by: int, username: str = None, first_name: str = None, last_name: str = None) -> Admin:
        existing_admin = await self.session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        
        if existing_admin.scalar_one_or_none():
            raise ValueError("User is already an admin")

        admin = Admin(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            added_by=added_by,
            is_active=True
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
            select(Admin).where(Admin.is_active == True).order_by(Admin.created_at.desc())
        )
        return result.scalars().all()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def seed_initial_admins(self):
        for username in settings.ADMIN_USERNAMES:
            user = await self.get_user_by_username(username)
            if user:
                existing_admin = await self.session.execute(
                    select(Admin).where(Admin.telegram_id == user.telegram_id)
                )
                
                if not existing_admin.scalar_one_or_none():
                    admin = Admin(
                        telegram_id=user.telegram_id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        added_by=user.telegram_id,
                        is_active=True
                    )
                    self.session.add(admin)
        
        await self.session.commit()
        print("✅ Initial admins seeded successfully")
