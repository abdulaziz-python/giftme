from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.database import Gift, WonGift
from app.core.config import settings
import random
from typing import List, Optional

class GiftService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_available_gifts(self) -> List[Gift]:
        result = await self.session.execute(
            select(Gift).where(
                Gift.is_active == True,
                Gift.star_count <= settings.MAX_GIFT_COST
            ).order_by(Gift.star_count.desc())
        )
        return result.scalars().all()
    
    async def get_random_gift(self) -> Optional[Gift]:
        gifts = await self.get_available_gifts()
        if not gifts:
            return None
        
        weighted_gifts = []
        for gift in gifts:
            weight = max(1, int(gift.win_probability * 100))
            weighted_gifts.extend([gift] * weight)
        
        return random.choice(weighted_gifts) if weighted_gifts else None
    
    async def record_won_gift(self, user_id: int, gift_id: int, transaction_id: int = None) -> WonGift:
        won_gift = WonGift(
            user_id=user_id,
            gift_id=gift_id,
            transaction_id=transaction_id
        )
        self.session.add(won_gift)
        
        await self.session.execute(
            update(Gift)
            .where(Gift.id == gift_id)
            .values(total_won=Gift.total_won + 1)
        )
        
        await self.session.commit()
        await self.session.refresh(won_gift)
        return won_gift
    
    async def get_user_won_gifts(self, user_id: int) -> List[WonGift]:
        result = await self.session.execute(
            select(WonGift)
            .join(Gift)
            .where(WonGift.user_id == user_id)
            .order_by(WonGift.won_at.desc())
        )
        return result.scalars().all()
    
    async def seed_gifts(self):
        existing_gifts = await self.session.execute(select(Gift))
        if existing_gifts.scalars().first():
            return
        
        premium_gifts = [
            Gift(
                gift_id="premium_sticker_pack_1",
                name="🎨 Premium Sticker Pack",
                description="Exclusive animated stickers",
                star_count=75,
                rarity="common",
                win_probability=0.25
            ),
            Gift(
                gift_id="exclusive_emoji_1",
                name="😎 Exclusive Emoji Pack",
                description="Rare emoji collection",
                star_count=100,
                rarity="uncommon",
                win_probability=0.20
            ),
            Gift(
                gift_id="channel_boost_1",
                name="🚀 Channel Boost",
                description="Boost your favorite channel",
                star_count=125,
                rarity="uncommon",
                win_probability=0.15
            ),
            Gift(
                gift_id="premium_month_1",
                name="👑 Premium Month",
                description="One month of Telegram Premium",
                star_count=150,
                rarity="rare",
                win_probability=0.10
            ),
            Gift(
                gift_id="special_badge_1",
                name="🏆 Special Badge",
                description="Exclusive profile badge",
                star_count=175,
                rarity="rare",
                win_probability=0.08
            ),
            Gift(
                gift_id="mega_prize_1",
                name="💎 Mega Prize",
                description="Ultimate reward package",
                star_count=200,
                rarity="legendary",
                win_probability=0.05
            )
        ]
        
        for gift in premium_gifts:
            self.session.add(gift)
        
        await self.session.commit()
