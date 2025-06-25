"""
Referal discount calculator and monthly checker
"""

import asyncio
from datetime import datetime, timedelta
from database import db
from texts import TEXTS


class DiscountCalculator:
    DISCOUNT_RATES = {
        (1, 2): 10,  # 1-2 referrals = 10% discount
        (3, 9): 30,  # 3-9 referrals = 30% discount
        (10, 99): 50,  # 10-99 referrals = 50% discount
        (100, 999): 100  # 100+ referrals = 100% discount (free)
    }

    BASE_PRICE = 10  # Base price in dollars

    @classmethod
    def calculate_discount(cls, paid_referrals):
        """Calculate discount percentage based on paid referrals"""
        for (min_refs, max_refs), discount in cls.DISCOUNT_RATES.items():
            if min_refs <= paid_referrals <= max_refs:
                return discount
        return 0

    @classmethod
    def calculate_price(cls, paid_referrals):
        """Calculate final price after discount"""
        discount = cls.calculate_discount(paid_referrals)
        discounted_price = cls.BASE_PRICE * (1 - discount / 100)
        return max(0, discounted_price)

    @classmethod
    async def send_monthly_discount_notifications(cls):
        """Send monthly discount notifications to all users"""
        async with db.pool.acquire() as conn:
            users = await conn.fetch('''
                SELECT 
                    u.telegram_id,
                    u.full_name,
                    u.language,
                    COUNT(r.telegram_id) as paid_referrals
                FROM users u
                LEFT JOIN users r ON u.telegram_id = r.referrer_id AND r.payment_status = TRUE
                WHERE u.payment_status = TRUE
                GROUP BY u.telegram_id, u.full_name, u.language
                HAVING COUNT(r.telegram_id) > 0
            ''')

        from main import bot

        for user in users:
            try:
                paid_refs = user['paid_referrals']
                discount = cls.calculate_discount(paid_refs)
                new_price = cls.calculate_price(paid_refs)

                lang = user['language']

                if lang == 'uz':
                    message = f"🎉 Tabriklaymiz! Sizning referalingiz orqali {paid_refs} nafar foydalanuvchi to'lov qildi.\n"
                    message += f"💰 Sizga {discount}% chegirma berildi!\n"
                    message += f"💵 Keyingi oy narxi: ${new_price}"
                elif lang == 'ru':
                    message = f"🎉 Поздравляем! Через вашу реферальную ссылку {paid_refs} пользователей оплатили.\n"
                    message += f"💰 Вам предоставлена скидка {discount}%!\n"
                    message += f"💵 Цена на следующий месяц: ${new_price}"
                else:
                    message = f"🎉 Congratulations! {paid_refs} users paid through your referral link.\n"
                    message += f"💰 You received a {discount}% discount!\n"
                    message += f"💵 Next month's price: ${new_price}"

                await bot.send_message(user['telegram_id'], message)
                await asyncio.sleep(0.1)  # Rate limiting

            except Exception as e:
                print(f"Failed to send discount notification to {user['telegram_id']}: {e}")


# Monthly scheduler for discount notifications
async def monthly_discount_scheduler():
    """Schedule monthly discount notifications"""
    while True:
        now = datetime.now()

        # Check if it's the last day of the month at 10:00 AM
        tomorrow = now + timedelta(days=1)
        if tomorrow.day == 1 and now.hour == 10 and now.minute == 0:
            await DiscountCalculator.send_monthly_discount_notifications()

        # Sleep for 1 minute
        await asyncio.sleep(60)
