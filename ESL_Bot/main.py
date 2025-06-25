import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import db
from handlers import router
from notifications import schedule_notifications

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    """Main function to run the bot"""
    try:
        # Initialize database
        await db.create_pool()
        await db.init_db()

        # Register handlers
        dp.include_router(router)

        # Start notification scheduler in background
        asyncio.create_task(schedule_notifications(bot))

        # Start polling
        await dp.start_polling(bot)

    except Exception as e:
        logging.error(f"Error starting bot: {e}")
    finally:
        await db.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
