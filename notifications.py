import asyncio
from datetime import datetime, timedelta
from database import db
from texts import TEXTS


async def send_lesson_notifications(bot):
    """Send lesson notifications to all paid users"""
    users = await db.get_users_for_notification()

    for user in users:
        try:
            message = "🔔 Bugun soat 18:00 da ESL darsi bo'lib o'tadi! Zoom linkni tekshiring!"
            if user['language'] == 'ru':
                message = "🔔 Сегодня в 18:00 урок ESL! Проверьте ссылку Zoom!"
            elif user['language'] == 'en':
                message = "🔔 Today at 18:00 ESL lesson! Check the Zoom link!"

            await bot.send_message(user['telegram_id'], message)
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Failed to send notification to {user['telegram_id']}: {e}")


async def schedule_notifications(bot):
    """Schedule notifications for 6 and 12 hours before lesson"""
    while True:
        now = datetime.now()

        # Check if it's time for 12-hour notification (6:00 AM)
        if now.hour == 6 and now.minute == 0:
            await send_lesson_notifications(bot)

        # Check if it's time for 6-hour notification (12:00 PM)
        if now.hour == 12 and now.minute == 0:
            await send_lesson_notifications(bot)

        # Sleep for 1 minute
        await asyncio.sleep(60)
