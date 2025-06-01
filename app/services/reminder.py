from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.database import User
from app.core.config import settings
from datetime import datetime, timedelta
import random
import os
from typing import List

class ReminderService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def get_random_gif(self) -> str:
        """Get random meme gif from media directory"""
        gif_files = [f"meme_{i}.gif" for i in range(1, 9)]  # meme_1.gif to meme_8.gif
        return os.path.join(settings.MEDIA_DIR, random.choice(gif_files))
    
    def get_random_reminder_text(self) -> str:
        """Get random fun reminder text"""
        texts = [
            "🐸 Hey there! Your favorite frog misses you! 💚",
            "🎰 The roulette wheel is getting lonely without you! 😢",
            "🎁 Amazing gifts are waiting for you to claim them! ✨",
            "💎 Your luck meter is fully charged! Time to spin! ⚡",
            "🌟 The stars aligned perfectly for your return! 🔮",
            "🎪 The carnival of gifts is calling your name! 🎭",
            "🍀 Lady Luck has been asking about you! 🎲",
            "🎊 Party time! Come back and let's celebrate! 🥳"
        ]
        return random.choice(texts)
    
    def get_random_button_text(self) -> str:
        """Get random fun button text"""
        buttons = [
            "🎰 Let's Spin Again!",
            "💚 Miss You Too, Pepe!",
            "🎁 Show Me The Gifts!",
            "✨ I'm Back For Magic!",
            "🍀 Ready For Luck!",
            "🎪 Take Me To Fun!",
            "💎 Claim My Fortune!",
            "🎊 Let's Party!"
        ]
        return random.choice(buttons)
    
    async def get_inactive_users(self) -> List[User]:
        """Get users who haven't been active for 3+ days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.REMINDER_DAYS)
            
            result = await self.session.execute(
                select(User).where(
                    and_(
                        User.last_activity < cutoff_date,
                        User.is_blocked == False,
                        (User.reminder_sent_at == None) | 
                        (User.reminder_sent_at < cutoff_date)
                    )
                )
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error getting inactive users: {e}")
            return []
    
    async def mark_reminder_sent(self, user_id: int):
        """Mark that reminder was sent to user"""
        try:
            user = await self.session.get(User, user_id)
            if user:
                user.reminder_sent_at = datetime.utcnow()
                await self.session.commit()
        except Exception as e:
            print(f"Error marking reminder sent: {e}")
            await self.session.rollback()
