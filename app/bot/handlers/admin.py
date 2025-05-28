from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.services.statistics import StatisticsService
from app.services.broadcast import BroadcastService
from app.services.admin_session import AdminSessionService
from app.services.admin import AdminService
from app.services.user import UserService
from typing import Dict
import json

router = Router()

class BroadcastStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_image = State()
    waiting_for_text = State()
    waiting_for_keyboard = State()
    confirmation = State()

class AdminStates(StatesGroup):
    waiting_for_admin_username = State()

async def is_admin(user_id: int, username: str, session: AsyncSession) -> bool:
    admin_service = AdminService(session)
    return await admin_service.is_admin(user_id, username)

def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistics", callback_data="admin_stats"),
                InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="🎁 Manage Gifts", callback_data="admin_gifts"),
                InlineKeyboardButton(text="👥 User Management", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton(text="💰 Revenue Report", callback_data="admin_revenue"),
                InlineKeyboardButton(text="📈 Analytics", callback_data="admin_analytics")
            ],
            [
                InlineKeyboardButton(text="👑 Admin Management", callback_data="admin_management")
            ]
        ]
    )

def stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 User Stats", callback_data="stats_users"),
                InlineKeyboardButton(text="💰 Revenue Stats", callback_data="stats_revenue")
            ],
            [
                InlineKeyboardButton(text="🎁 Gift Stats", callback_data="stats_gifts"),
                InlineKeyboardButton(text="📊 Charts", callback_data="stats_charts")
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_stats"),
                InlineKeyboardButton(text="⬅️ Back", callback_data="admin_main")
            ]
        ]
    )

def broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 New Broadcast", callback_data="broadcast_new"),
                InlineKeyboardButton(text="📋 My Broadcasts", callback_data="broadcast_list")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="admin_main")
            ]
        ]
    )

def admin_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Add Admin", callback_data="add_admin"),
                InlineKeyboardButton(text="📋 List Admins", callback_data="list_admins")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="admin_main")
            ]
        ]
    )

@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    if not await is_admin(message.from_user.id, message.from_user.username, session):
        await message.answer("❌ Access denied. You are not authorized to use admin commands.")
        return
    
    await message.answer(
        "🔧 **Admin Panel**\n\n"
        "Welcome to the administration panel. Choose an option below:",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_main")
async def admin_main_callback(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔧 **Admin Panel**\n\n"
        "Welcome to the administration panel. Choose an option below:",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    stats_service = StatisticsService(session)
    user_stats = await stats_service.get_user_stats()
    revenue_stats = await stats_service.get_revenue_stats()
    gift_stats = await stats_service.get_gift_stats()
    
    text = (
        "📊 **Statistics Overview**\n\n"
        f"👥 **Users:**\n"
        f"• Total: {user_stats['total_users']:,}\n"
        f"• Today: +{user_stats['new_users_today']:,}\n"
        f"• This week: +{user_stats['new_users_week']:,}\n"
        f"• This month: +{user_stats['new_users_month']:,}\n"
        f"• Active today: {user_stats['active_users_today']:,}\n"
        f"• Premium: {user_stats['premium_users']:,}\n\n"
        f"💰 **Revenue:**\n"
        f"• Total: {revenue_stats['total_revenue']:,} ⭐\n"
        f"• Today: {revenue_stats['revenue_today']:,} ⭐\n"
        f"• This week: {revenue_stats['revenue_week']:,} ⭐\n"
        f"• This month: {revenue_stats['revenue_month']:,} ⭐\n"
        f"• Transactions: {revenue_stats['total_transactions']:,}\n\n"
        f"🎁 **Gifts:**\n"
        f"• Total won: {gift_stats['total_gifts_won']:,}\n"
        f"• Today: {gift_stats['gifts_today']:,}\n"
        f"• Total value: {gift_stats['total_gift_value']:,} ⭐"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=stats_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "stats_charts")
async def stats_charts_callback(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await callback.answer("📊 Generating charts...", show_alert=True)
    
    stats_service = StatisticsService(session)
    
    try:
        user_chart = await stats_service.generate_user_growth_chart()
        revenue_chart = await stats_service.generate_revenue_chart()
        
        if user_chart:
            with open(user_chart, 'rb') as photo:
                await callback.message.answer_photo(
                    photo=photo,
                    caption="📈 **User Growth Chart (Last 30 Days)**"
                )
        
        if revenue_chart:
            with open(revenue_chart, 'rb') as photo:
                await callback.message.answer_photo(
                    photo=photo,
                    caption="💰 **Revenue Chart (Last 30 Days)**"
                )
    except Exception as e:
        await callback.message.answer(f"❌ Error generating charts: {str(e)}")

@router.callback_query(F.data == "admin_management")
async def admin_management_callback(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👑 **Admin Management**\n\n"
        "Manage bot administrators and their permissions.",
        reply_markup=admin_management_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "add_admin")
async def add_admin_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_for_admin_username)
    await callback.message.edit_text(
        "➕ **Add New Admin**\n\n"
        "Please send the username of the user you want to make an admin.\n"
        "Format: @username or just username",
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_for_admin_username)
async def add_admin_username_handler(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, message.from_user.username, session):
        return
    
    username = message.text.strip().replace('@', '')
    
    try:
        user_service = UserService(session)
        admin_service = AdminService(session)
        
        # Try to find user by username
        user = await user_service.get_user_by_username(username)
        
        if not user:
            await message.answer(
                f"❌ User @{username} not found in the database.\n"
                f"The user must start the bot first before being added as admin."
            )
            await state.clear()
            return
        
        # Check if already admin
        if await admin_service.is_admin(user.telegram_id, username):
            await message.answer(f"❌ @{username} is already an admin.")
            await state.clear()
            return
        
        # Create telegram user object for admin service
        from aiogram.types import User as TelegramUser
        telegram_user = TelegramUser(
            id=user.telegram_id,
            is_bot=False,
            first_name=user.first_name or "Admin",
            username=username
        )
        
        # Add admin
        await admin_service.add_admin(telegram_user, message.from_user.id)
        
        await message.answer(
            f"✅ Successfully added @{username} as admin!\n\n"
            f"**User Details:**\n"
            f"• Name: {user.first_name or 'N/A'} {user.last_name or ''}\n"
            f"• Username: @{username}\n"
            f"• User ID: {user.telegram_id}\n"
            f"• Added by: @{message.from_user.username}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(f"❌ Error adding admin: {str(e)}")
    
    await state.clear()

@router.callback_query(F.data == "list_admins")
async def list_admins_callback(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    admin_service = AdminService(session)
    admins = await admin_service.get_all_admins()
    
    if not admins:
        text = "📋 **Admin List**\n\nNo admins found in database."
    else:
        text = "📋 **Admin List**\n\n"
        for i, admin in enumerate(admins, 1):
            text += (
                f"{i}. **{admin.first_name or 'N/A'}** {admin.last_name or ''}\n"
                f"   • Username: @{admin.username or 'N/A'}\n"
                f"   • ID: `{admin.telegram_id}`\n"
                f"   • Added: {admin.created_at.strftime('%Y-%m-%d')}\n\n"
            )
    
    # Add initial admins from config
    text += "\n🔧 **Initial Admins (from config):**\n"
    for username in settings.ADMIN_USERNAMES:
        text += f"• @{username}\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="admin_management")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 **Broadcast Management**\n\n"
        "Create and manage broadcast messages to all users.",
        reply_markup=broadcast_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "broadcast_new")
async def broadcast_new_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await state.set_state(BroadcastStates.waiting_for_title)
    await callback.message.edit_text(
        "📝 **Create New Broadcast**\n\n"
        "Step 1/5: Enter a title for this broadcast:",
        parse_mode="Markdown"
    )

@router.message(BroadcastStates.waiting_for_title)
async def broadcast_title_handler(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, message.from_user.username, session):
        return
    
    await state.update_data(title=message.text)
    await state.set_state(BroadcastStates.waiting_for_image)
    
    admin_session_service = AdminSessionService(session)
    await admin_session_service.create_session(
        admin_id=message.from_user.id,
        session_type="broadcast_creation",
        session_data={"title": message.text}
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Skip Image", callback_data="broadcast_skip_image")]
        ]
    )
    
    await message.answer(
        "🖼️ **Step 2/5: Image/GIF (Optional)**\n\n"
        "Send an image or GIF for your broadcast, or skip this step:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "broadcast_skip_image")
async def broadcast_skip_image_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await state.set_state(BroadcastStates.waiting_for_text)
    await callback.message.edit_text(
        "📝 **Step 3/5: Message Text**\n\n"
        "Enter the text for your broadcast message.\n"
        "You can use Markdown formatting:\n"
        "• `*bold*` for **bold**\n"
        "• `_italic_` for *italic*\n"
        "• `[link](url)` for links\n"
        "• `` `code` `` for code",
        parse_mode="Markdown"
    )

@router.message(BroadcastStates.waiting_for_image)
async def broadcast_image_handler(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, message.from_user.username, session):
        return
    
    image_url = None
    if message.photo:
        image_url = message.photo[-1].file_id
    elif message.animation:
        image_url = message.animation.file_id
    
    data = await state.get_data()
    data['image_url'] = image_url
    await state.update_data(**data)
    
    admin_session_service = AdminSessionService(session)
    await admin_session_service.update_session_data(
        admin_id=message.from_user.id,
        session_type="broadcast_creation",
        session_data=data
    )
    
    await state.set_state(BroadcastStates.waiting_for_text)
    await message.answer(
        "📝 **Step 3/5: Message Text**\n\n"
        "Enter the text for your broadcast message.\n"
        "You can use Markdown formatting:\n"
        "• `*bold*` for **bold**\n"
        "• `_italic_` for *italic*\n"
        "• `[link](url)` for links\n"
        "• `` `code` `` for code",
        parse_mode="Markdown"
    )

@router.message(BroadcastStates.waiting_for_text)
async def broadcast_text_handler(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, message.from_user.username, session):
        return
    
    data = await state.get_data()
    data['text'] = message.text
    await state.update_data(**data)
    
    admin_session_service = AdminSessionService(session)
    await admin_session_service.update_session_data(
        admin_id=message.from_user.id,
        session_type="broadcast_creation",
        session_data=data
    )
    
    await state.set_state(BroadcastStates.waiting_for_keyboard)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Skip Keyboard", callback_data="broadcast_skip_keyboard")],
            [InlineKeyboardButton(text="ℹ️ Keyboard Format Help", callback_data="broadcast_keyboard_help")]
        ]
    )
    
    await message.answer(
        "⌨️ **Step 4/5: Inline Keyboard (Optional)**\n\n"
        "Send keyboard configuration in JSON format or skip this step.\n\n"
        "Example:\n"
        "\`\`\`json\n"
        "{\n"
        '  "inline_keyboard": [\n'
        '    [{"text": "Button 1", "url": "https://example.com"}],\n'
        '    [{"text": "Button 2", "callback_data": "data"}]\n'
        "  ]\n"
        "}\n"
        "\`\`\`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "broadcast_skip_keyboard")
async def broadcast_skip_keyboard_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    data = await state.get_data()
    await show_broadcast_confirmation(callback.message, data, state, session)

@router.message(BroadcastStates.waiting_for_keyboard)
async def broadcast_keyboard_handler(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, message.from_user.username, session):
        return
    
    try:
        keyboard_data = json.loads(message.text)
        data = await state.get_data()
        data['inline_keyboard'] = keyboard_data
        await state.update_data(**data)
        
        admin_session_service = AdminSessionService(session)
        await admin_session_service.update_session_data(
            admin_id=message.from_user.id,
            session_type="broadcast_creation",
            session_data=data
        )
        
        await show_broadcast_confirmation(message, data, state, session)
        
    except json.JSONDecodeError:
        await message.answer(
            "❌ Invalid JSON format. Please check your keyboard configuration and try again.",
            parse_mode="Markdown"
        )

async def show_broadcast_confirmation(message: Message, data: Dict, state: FSMContext, session: AsyncSession):
    await state.set_state(BroadcastStates.confirmation)
    
    stats_service = StatisticsService(session)
    user_stats = await stats_service.get_user_stats()
    
    preview_text = (
        "✅ **Step 5/5: Confirmation**\n\n"
        f"**Title:** {data.get('title', 'N/A')}\n"
        f"**Has Image:** {'Yes' if data.get('image_url') else 'No'}\n"
        f"**Has Keyboard:** {'Yes' if data.get('inline_keyboard') else 'No'}\n"
        f"**Target Users:** {user_stats['total_users'] - user_stats['blocked_users']:,}\n\n"
        f"**Message Preview:**\n{data.get('text', 'N/A')[:200]}{'...' if len(data.get('text', '')) > 200 else ''}"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Send Broadcast", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="broadcast_cancel")
            ]
        ]
    )
    
    await message.answer(preview_text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    data = await state.get_data()
    
    broadcast_service = BroadcastService(session, callback.bot)
    broadcast = await broadcast_service.create_broadcast(
        title=data.get('title'),
        text=data.get('text'),
        created_by=callback.from_user.id,
        image_url=data.get('image_url'),
        inline_keyboard=data.get('inline_keyboard')
    )
    
    success = await broadcast_service.start_broadcast(broadcast.id)
    
    if success:
        await callback.message.edit_text(
            f"✅ **Broadcast Started!**\n\n"
            f"Broadcast ID: {broadcast.id}\n"
            f"Target Users: {broadcast.target_users:,}\n\n"
            f"The broadcast is now being sent to all users. "
            f"You will receive updates on the progress.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ Failed to start broadcast. Please try again.",
            parse_mode="Markdown"
        )
    
    await state.clear()
    
    admin_session_service = AdminSessionService(session)
    await admin_session_service.delete_session(
        admin_id=callback.from_user.id,
        session_type="broadcast_creation"
    )

@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, callback.from_user.username, session):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await state.clear()
    
    admin_session_service = AdminSessionService(session)
    await admin_session_service.delete_session(
        admin_id=callback.from_user.id,
        session_type="broadcast_creation"
    )
    
    await callback.message.edit_text(
        "❌ Broadcast cancelled.",
        reply_markup=broadcast_keyboard(),
        parse_mode="Markdown"
    )
