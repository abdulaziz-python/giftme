from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.database import Gift, WonGift, User
from typing import List, Optional
import random

class GiftService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_available_gifts(self) -> List[Gift]:
        try:
            result = await self.session.execute(
                select(Gift).where(Gift.is_active == True).order_by(Gift.star_count.asc())
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error getting available gifts: {e}")
            return []

    async def get_gift_by_id(self, gift_id: int) -> Optional[Gift]:
        try:
            result = await self.session.execute(
                select(Gift).where(Gift.id == gift_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting gift by id: {e}")
            return None

    async def get_random_gift(self) -> Optional[Gift]:
        try:
            gifts = await self.get_available_gifts()
            if not gifts:
                return None
            
            weights = [gift.win_probability for gift in gifts]
            selected_gift = random.choices(gifts, weights=weights, k=1)[0]
            
            selected_gift.total_won += 1
            await self.session.commit()
            
            return selected_gift
        except Exception as e:
            await self.session.rollback()
            print(f"Error getting random gift: {e}")
            return None

    async def record_won_gift(self, user_id: int, gift_id: int, transaction_id: Optional[int] = None) -> Optional[WonGift]:
        try:
            won_gift = WonGift(
                user_id=user_id,
                gift_id=gift_id,
                transaction_id=transaction_id
            )
            self.session.add(won_gift)
            await self.session.commit()
            await self.session.refresh(won_gift)
            return won_gift
        except Exception as e:
            await self.session.rollback()
            print(f"Error recording won gift: {e}")
            return None

    async def get_user_won_gifts(self, user_id: int) -> List[WonGift]:
        try:
            result = await self.session.execute(
                select(WonGift)
                .join(Gift)
                .where(WonGift.user_id == user_id)
                .order_by(WonGift.won_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error getting user won gifts: {e}")
            return []

    async def seed_gifts(self):
        try:
            existing_gifts = await self.session.execute(select(func.count(Gift.id)))
            if existing_gifts.scalar() > 0:
                return

            default_gifts = [
                {
                    "gift_id": "premium_stickers_1",
                    "name": "🎨 Premium Sticker Pack",
                    "description": "Exclusive animated stickers",
                    "star_count": 75,
                    "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
                    "rarity": "common",
                    "win_probability": 0.3
                },
                {
                    "gift_id": "emoji_pack_1",
                    "name": "😎 Exclusive Emoji Pack",
                    "description": "Rare emoji collection",
                    "star_count": 100,
                    "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
                    "rarity": "uncommon",
                    "win_probability": 0.25
                },
                {
                    "gift_id": "channel_boost_1",
                    "name": "🚀 Channel Boost",
                    "description": "Boost your favorite channel",
                    "star_count": 125,
                    "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
                    "rarity": "rare",
                    "win_probability": 0.2
                },
                {
                    "gift_id": "premium_sub_1",
                    "name": "👑 Premium Subscription",
                    "description": "1 month Telegram Premium",
                    "star_count": 150,
                    "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
                    "rarity": "epic",
                    "win_probability": 0.15
                },
                {
                    "gift_id": "special_badge_1",
                    "name": "🏆 Special Badge",
                    "description": "Exclusive profile badge",
                    "star_count": 200,
                    "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
                    "rarity": "legendary",
                    "win_probability": 0.1
                }
            ]

            for gift_data in default_gifts:
                gift = Gift(**gift_data)
                self.session.add(gift)

            await self.session.commit()
            print("✅ Default gifts seeded successfully")
        except Exception as e:
            await self.session.rollback()
            print(f"Error seeding gifts: {e}")
