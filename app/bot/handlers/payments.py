from aiogram import Router, F
from aiogram.types import PreCheckoutQuery, Message, LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.payment import PaymentService
from app.services.gift import GiftService
from app.core.config import settings

router = Router()

@router.pre_checkout_query()
async def process_pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery,
    session: AsyncSession
):
    payment_service = PaymentService(session)
    
    await payment_service.create_transaction(
        user_id=pre_checkout_query.from_user.id,
        amount=settings.SPIN_COST,
        transaction_id=pre_checkout_query.id
    )
    
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(
    message: Message,
    session: AsyncSession
):
    payment_service = PaymentService(session)
    gift_service = GiftService(session)
    
    payment = message.successful_payment
    
    await payment_service.update_transaction_status(
        transaction_id=payment.telegram_payment_charge_id,
        status="completed"
    )
    
    won_gift = await gift_service.get_random_gift()
    
    if won_gift:
        await gift_service.record_won_gift(
            user_id=message.from_user.id,
            gift_id=won_gift.id
        )
        
        try:
            await message.bot.send_gift(
                user_id=message.from_user.id,
                gift_id=won_gift.gift_id
            )
            
            await message.answer(
                f"🎉 Congratulations! You won: {won_gift.name}!\n"
                f"The gift has been sent to you! 🎁"
            )
        except Exception:
            await message.answer(
                f"🎉 Congratulations! You won: {won_gift.name}!\n"
                f"Unfortunately, we couldn't send the gift automatically. "
                f"Please contact support with your transaction ID: {payment.telegram_payment_charge_id}"
            )
    else:
        await message.answer(
            "😔 Sorry, no gifts are available at the moment. "
            "Your Stars will be refunded shortly."
        )
