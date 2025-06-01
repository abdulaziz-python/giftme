import asyncio
import os
import random
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy import and_
from app.core.config import settings
from app.core.database import async_session_maker
from app.models.database import User
from app.services.reminder import ReminderService

async def send_reminder_task(bot: Bot):
    """Background task to send reminders to inactive users"""
    print("🔔 Starting reminder task...")
    
    while True:
        try:
            # Wait for 24 hours between checks
            await asyncio.sleep(24 * 60 * 60)
            
            print(f"⏰ Running reminder check at {datetime.now()}")
            
            async with async_session_maker() as session:
                reminder_service = ReminderService(session)
                inactive_users = await reminder_service.get_inactive_users()
                
                print(f"📊 Found {len(inactive_users)} inactive users")
                
                for user in inactive_users:
                    try:
                        # Get random content
                        gif_path = reminder_service.get_random_gif()
                        reminder_text = reminder_service.get_random_reminder_text()
                        button_text = reminder_service.get_random_button_text()
                        
                        # Create keyboard with fun button text
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text=button_text,
                                        web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/docs")
                                    )
                                ]
                            ]
                        )
                        
                        # Check if gif exists
                        if os.path.exists(gif_path):
                            # Send gif with message
                            gif = FSInputFile(gif_path)
                            await bot.send_animation(
                                chat_id=user.telegram_id,
                                animation=gif,
                                caption=reminder_text,
                                reply_markup=keyboard
                            )
                        else:
                            # Fallback to text message if gif not found
                            await bot.send_message(
                                chat_id=user.telegram_id,
                                text=f"{reminder_text}\n\n(Note: Couldn't find GIF at {gif_path})",
                                reply_markup=keyboard
                            )
                        
                        # Mark reminder as sent
                        await reminder_service.mark_reminder_sent(user.id)
                        
                        # Sleep briefly to avoid rate limits
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        print(f"❌ Error sending reminder to user {user.telegram_id}: {e}")
                        continue
                
        except Exception as e:
            print(f"❌ Reminder task error: {e}")
            # Wait for 1 hour before retrying after an error
            await asyncio.sleep(60 * 60)
