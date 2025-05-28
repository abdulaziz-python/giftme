from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import Transaction, SpinSession
from app.core.config import settings
import uuid
from datetime import datetime, timedelta
from typing import Optional

class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_spin_session(self, user_id: int) -> SpinSession:
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        spin_session = SpinSession(
            user_id=user_id,
            session_id=session_id,
            status="pending",
            expires_at=expires_at
        )
        
        self.session.add(spin_session)
        await self.session.commit()
        await self.session.refresh(spin_session)
        return spin_session
    
    async def create_transaction(self, user_id: int, amount: int, transaction_id: str) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            transaction_id=transaction_id,
            amount=amount,
            status="pending"
        )
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def update_transaction_status(self, transaction_id: str, status: str) -> Optional[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.transaction_id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if transaction:
            transaction.status = status
            if status == "completed":
                transaction.completed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(transaction)
        
        return transaction
    
    async def get_spin_session(self, session_id: str) -> Optional[SpinSession]:
        result = await self.session.execute(
            select(SpinSession).where(SpinSession.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def update_spin_session_status(self, session_id: str, status: str) -> Optional[SpinSession]:
        result = await self.session.execute(
            select(SpinSession).where(SpinSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.status = status
            if status == "completed":
                session.completed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(session)
        
        return session
