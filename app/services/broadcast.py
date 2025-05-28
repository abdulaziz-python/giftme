from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.database import Broadcast, BroadcastLog, User, BroadcastStatus
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List, Optional
import asyncio
import json
from datetime import datetime

class BroadcastService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
    
    async def create_broadcast(
        self,
        title: str,
        text: str,
        created_by: int,
        image_url: Optional[str] = None,
        inline_keyboard: Optional[Dict] = None
    ) -> Broadcast:
        broadcast = Broadcast(
            title=title,
            text=text,
            image_url=image_url,
            inline_keyboard=inline_keyboard,
            created_by=created_by
        )
        
        self.session.add(broadcast)
        await self.session.commit()
        await self.session.refresh(broadcast)
        
        target_users = await self.session.scalar(
            select(func.count(User.id)).where(User.is_blocked == False)
        )
        
        broadcast.target_users = target_users or 0
        await self.session.commit()
        
        return broadcast
    
    async def get_broadcast(self, broadcast_id: int) -> Optional[Broadcast]:
        result = await self.session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_broadcasts(self, admin_id: int) -> List[Broadcast]:
        result = await self.session.execute(
            select(Broadcast)
            .where(Broadcast.created_by == admin_id)
            .order_by(Broadcast.created_at.desc())
        )
        return result.scalars().all()
    
    async def start_broadcast(self, broadcast_id: int) -> bool:
        broadcast = await self.get_broadcast(broadcast_id)
        if not broadcast or broadcast.status != BroadcastStatus.DRAFT:
            return False
        
        await self.session.execute(
            update(Broadcast)
            .where(Broadcast.id == broadcast_id)
            .values(
                status=BroadcastStatus.SENDING,
                started_at=datetime.utcnow()
            )
        )
        await self.session.commit()
        
        asyncio.create_task(self._send_broadcast(broadcast))
        return True
    
    async def _send_broadcast(self, broadcast: Broadcast):
        users_result = await self.session.execute(
            select(User.telegram_id).where(User.is_blocked == False)
        )
        users = users_result.scalars().all()
        
        sent_count = 0
        failed_count = 0
        
        keyboard = None
        if broadcast.inline_keyboard:
            keyboard = self._build_keyboard(broadcast.inline_keyboard)
        
        for user_id in users:
            try:
                if broadcast.image_url:
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=broadcast.image_url,
                        caption=broadcast.text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                else:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=broadcast.text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                
                log = BroadcastLog(
                    broadcast_id=broadcast.id,
                    user_id=user_id,
                    status="sent"
                )
                self.session.add(log)
                sent_count += 1
                
            except Exception as e:
                log = BroadcastLog(
                    broadcast_id=broadcast.id,
                    user_id=user_id,
                    status="failed",
                    error_message=str(e)
                )
                self.session.add(log)
                failed_count += 1
            
            if (sent_count + failed_count) % 100 == 0:
                await self.session.commit()
                await asyncio.sleep(1)
        
        await self.session.execute(
            update(Broadcast)
            .where(Broadcast.id == broadcast.id)
            .values(
                status=BroadcastStatus.COMPLETED,
                sent_count=sent_count,
                failed_count=failed_count,
                completed_at=datetime.utcnow()
            )
        )
        await self.session.commit()
    
    def _build_keyboard(self, keyboard_data: Dict) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for row in keyboard_data.get('inline_keyboard', []):
            button_row = []
            for button in row:
                btn = InlineKeyboardButton(
                    text=button['text'],
                    url=button.get('url'),
                    callback_data=button.get('callback_data'),
                    web_app=button.get('web_app')
                )
                button_row.append(btn)
            keyboard.inline_keyboard.append(button_row)
        
        return keyboard
