from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user import UserService
from app.core.config import settings
import os

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
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/docs")
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 API Documentation",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/docs")
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
        f"🍀 **Good luck and have fun!**\n\n"
        f"📱 **User Info:**\n"
        f"• ID: `{user.telegram_id}`\n"
        f"• Username: @{user.username or 'N/A'}\n"
        f"• Premium: {'✅' if user.is_premium else '❌'}\n\n"
        f"💡 **Tip**: If you don't visit for 3 days, I'll send you a fun surprise! 🐸"
    )
    
    # Use the local image file
    image_path = "static/pepe-heart.png"
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # Fallback to text message if image not found
        await message.answer(
            text=welcome_text,
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
        f"5️⃣ Check **'📊 API Documentation'** to see technical details\n\n"
        f"💡 **Tips:**\n"
        f"• Higher value gifts are rarer\n"
        f"• All gifts are worth more than the spin cost\n"
        f"• You can win multiple times!\n"
        f"• Stay active to avoid missing fun reminders! 🐸\n\n"
        f"🎊 **Start spinning and good luck!**"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎰 Start Playing",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/docs")
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
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/docs")
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 API Documentation",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/docs")
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
        f"🍀 **Good luck and have fun!**\n\n"
        f"💡 **Tip**: If you don't visit for 3 days, I'll send you a fun surprise! 🐸"
    )
    
    await callback.message.edit_caption(
        caption=welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
