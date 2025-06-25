import asyncpg
import asyncio
from config import DATABASE_URL


class Database:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

    async def init_db(self):
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20),
                    age INTEGER,
                    region VARCHAR(100),
                    language VARCHAR(10) DEFAULT 'uz',
                    referrer_id BIGINT,
                    referral_count INTEGER DEFAULT 0,
                    payment_status BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Payments table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    screenshot_file_id VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'pending',
                    admin_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            ''')

            # Questions table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    question TEXT NOT NULL,
                    answered BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            ''')

            # FAQ table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS faq (
                    id SERIAL PRIMARY KEY,
                    question_uz TEXT,
                    answer_uz TEXT,
                    question_ru TEXT,
                    answer_ru TEXT,
                    question_en TEXT,
                    answer_en TEXT
                )
            ''')

    async def add_user(self, telegram_id, full_name, phone=None, age=None, region=None, language='uz',
                       referrer_id=None):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (telegram_id, full_name, phone, age, region, language, referrer_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (telegram_id) DO UPDATE SET
                full_name = $2, phone = $3, age = $4, region = $5, language = $6
            ''', telegram_id, full_name, phone, age, region, language, referrer_id)

            # Update referrer count
            if referrer_id:
                await conn.execute('''
                    UPDATE users SET referral_count = referral_count + 1
                    WHERE telegram_id = $1
                ''', referrer_id)

    async def get_user(self, telegram_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM users WHERE telegram_id = $1', telegram_id)

    async def update_user_language(self, telegram_id, language):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET language = $1 WHERE telegram_id = $2', language, telegram_id)

    async def update_user_age(self, telegram_id, age):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET age = $1 WHERE telegram_id = $2', age, telegram_id)

    async def update_user_name(self, telegram_id, full_name):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET full_name = $1 WHERE telegram_id = $2', full_name, telegram_id)

    async def update_user_phone(self, telegram_id, phone):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET phone = $1 WHERE telegram_id = $2', phone, telegram_id)

    async def update_user_region(self, telegram_id, region):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE users SET region = $1 WHERE telegram_id = $2', region, telegram_id)

    async def add_payment(self, user_id, screenshot_file_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchval('''
                INSERT INTO payments (user_id, screenshot_file_id)
                VALUES ($1, $2) RETURNING id
            ''', user_id, screenshot_file_id)

    async def update_payment_status(self, payment_id, status):
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE payments SET status = $1 WHERE id = $2', status, payment_id)
            if status == 'approved':
                # Get user_id and update payment_status
                user_id = await conn.fetchval('SELECT user_id FROM payments WHERE id = $1', payment_id)
                await conn.execute('UPDATE users SET payment_status = TRUE WHERE telegram_id = $1', user_id)

    async def add_question(self, user_id, question):
        async with self.pool.acquire() as conn:
            await conn.execute('INSERT INTO questions (user_id, question) VALUES ($1, $2)', user_id, question)

    async def get_faq(self, language):
        async with self.pool.acquire() as conn:
            if language == 'uz':
                return await conn.fetch(
                    'SELECT question_uz as question, answer_uz as answer FROM faq WHERE question_uz IS NOT NULL')
            elif language == 'ru':
                return await conn.fetch(
                    'SELECT question_ru as question, answer_ru as answer FROM faq WHERE question_ru IS NOT NULL')
            else:
                return await conn.fetch(
                    'SELECT question_en as question, answer_en as answer FROM faq WHERE question_en IS NOT NULL')

    async def get_users_for_notification(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                'SELECT telegram_id, language FROM users WHERE payment_status = TRUE AND is_active = TRUE')

    async def get_referral_stats(self, telegram_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT referral_count, 
                       (SELECT COUNT(*) FROM users WHERE referrer_id = $1 AND payment_status = TRUE) as paid_referrals
                FROM users WHERE telegram_id = $1
            ''', telegram_id)


db = Database()
