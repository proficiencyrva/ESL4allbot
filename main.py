import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import db
from handlers import router
from notifications import schedule_notifications
from flask import Flask
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Flask app
web_app = Flask(__name__)

@web_app.route("/healthy", methods=["GET"])
def healthy():
    return "<b>Bot is alive🎉🥳</b>", 200

def run_flask():
    web_app.run(host="0.0.0.0", port=5000)

async def main():
    """Main function to run the bot and start Flask server"""
    try:
        # Start Flask in background thread
        Thread(target=run_flask).start()

        # Initialize database
        await db.create_pool()
        await db.init_db()

        # Register handlers
        dp.include_router(router)

        # Start notification scheduler
        asyncio.create_task(schedule_notifications(bot))

        # Start polling
        await dp.start_polling(bot)

    except Exception as e:
        logging.error(f"Error starting bot: {e}")
    finally:
        await db.close_pool()

if __name__ == "__main__":
    asyncio.run(main())
