from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user import UserService
from app.core.config import settings

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession):
    user_service = UserService(session)
    user = await user_service.get_or_create_user(message.from_user)
    
    await user_service.update_last_activity(user.telegram_id)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎰 Play Roulette",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/roulette")
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 My Gifts",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/profile")
                ),
                InlineKeyboardButton(
                    text="ℹ️ How to Play",
                    callback_data="how_to_play"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Buy Stars",
                    url="https://t.me/PremiumBot"
                )
            ]
        ]
    )
    
    welcome_text = (
        f"🎰 **Welcome to Gift Roulette, {message.from_user.first_name}!**\n\n"
        f"🌟 Spin the wheel for just **{settings.SPIN_COST} ⭐ Stars** and win amazing gifts worth up to **{settings.MAX_GIFT_COST} ⭐ Stars**!\n\n"
        f"🎁 **Available Prizes:**\n"
        f"• 🎨 Premium Sticker Packs\n"
        f"• 😎 Exclusive Emojis\n"
        f"• 🚀 Channel Boosts\n"
        f"• 👑 Premium Subscriptions\n"
        f"• 🏆 Special Badges\n"
        f"• 💎 And much more!\n\n"
        f"🍀 **Good luck and have fun!**"
    )
    
    await message.answer_photo(
        photo="https://images.unsplash.com/photo-1596838132731-3301c3fd4317?w=800&h=600&fit=crop",
        caption=welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "how_to_play")
async def how_to_play_callback(callback: CallbackQuery):
    how_to_text = (
        "🎯 **How to Play Gift Roulette**\n\n"
        f"1️⃣ Click **'🎰 Play Roulette'** to open the game\n"
        f"2️⃣ Pay **{settings.SPIN_COST} ⭐ Stars** to spin the wheel\n"
        f"3️⃣ Watch the wheel spin and see what you win!\n"
        f"4️⃣ Receive your gift instantly in Telegram\n"
        f"5️⃣ Check **'🎁 My Gifts'** to see your collection\n\n"
        f"💡 **Tips:**\n"
        f"• Higher value gifts are rarer\n"
        f"• All gifts are worth more than the spin cost\n"
        f"• You can win multiple times!\n\n"
        f"🎊 **Start spinning and good luck!**"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎰 Start Playing",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/roulette")
                )
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")
            ]
        ]
    )
    
    await callback.message.edit_caption(
        caption=how_to_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎰 Play Roulette",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/roulette")
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 My Gifts",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/profile")
                ),
                InlineKeyboardButton(
                    text="ℹ️ How to Play",
                    callback_data="how_to_play"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Buy Stars",
                    url="https://t.me/PremiumBot"
                )
            ]
        ]
    )
    
    welcome_text = (
        f"🎰 **Welcome to Gift Roulette!**\n\n"
        f"🌟 Spin the wheel for just **{settings.SPIN_COST} ⭐ Stars** and win amazing gifts worth up to **{settings.MAX_GIFT_COST} ⭐ Stars**!\n\n"
        f"🎁 **Available Prizes:**\n"
        f"• 🎨 Premium Sticker Packs\n"
        f"• 😎 Exclusive Emojis\n"
        f"• 🚀 Channel Boosts\n"
        f"• 👑 Premium Subscriptions\n"
        f"• 🏆 Special Badges\n"
        f"• 💎 And much more!\n\n"
        f"🍀 **Good luck and have fun!**"
    )
    
    await callback.message.edit_caption(
        caption=welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
