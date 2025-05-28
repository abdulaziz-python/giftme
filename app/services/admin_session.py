from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.database import AdminSession
from datetime import datetime, timedelta
import json
from typing import Dict, Optional, Any

class AdminSessionService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_session(
        self,
        admin_id: int,
        session_type: str,
        session_data: Dict = None,
        expires_in_minutes: int = 30
    ) -> AdminSession:
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        admin_session = AdminSession(
            admin_id=admin_id,
            session_type=session_type,
            session_data=session_data,
            expires_at=expires_at
        )
        
        self.session.add(admin_session)
        await self.session.commit()
        await self.session.refresh(admin_session)
        
        return admin_session
    
    async def get_session(self, admin_id: int, session_type: str) -> Optional[AdminSession]:
        result = await self.session.execute(
            select(AdminSession).where(
                AdminSession.admin_id == admin_id,
                AdminSession.session_type == session_type,
                AdminSession.expires_at > datetime.utcnow()
            ).order_by(AdminSession.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def update_session_data(
        self,
        admin_id: int,
        session_type: str,
        session_data: Dict
    ) -> Optional[AdminSession]:
        admin_session = await self.get_session(admin_id, session_type)
        if admin_session:
            admin_session.session_data = session_data
            await self.session.commit()
            await self.session.refresh(admin_session)
        return admin_session
    
    async def delete_session(self, admin_id: int, session_type: str):
        await self.session.execute(
            delete(AdminSession).where(
                AdminSession.admin_id == admin_id,
                AdminSession.session_type == session_type
            )
        )
        await self.session.commit()
    
    async def cleanup_expired_sessions(self):
        await self.session.execute(
            delete(AdminSession).where(
                AdminSession.expires_at <= datetime.utcnow()
            )
        )
        await self.session.commit()
