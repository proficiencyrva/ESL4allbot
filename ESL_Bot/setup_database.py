"""
Script to set up the database and add initial data
"""

import asyncio
from database import db


async def setup_initial_data():
    """Set up initial FAQ data"""
    await db.create_pool()
    await db.init_db()

    # Add some initial FAQ items
    faq_items = [
        {
            'question_uz': "ESL kursi qancha vaqt davom etadi?",
            'answer_uz': "ESL kursi 3 oy davom etadi, haftada 3 marta dars bo'ladi.",
            'question_ru': "Сколько времени длится курс ESL?",
            'answer_ru': "Курс ESL длится 3 месяца, занятия проводятся 3 раза в неделю.",
            'question_en': "How long does the ESL course last?",
            'answer_en': "The ESL course lasts 3 months, with classes 3 times a week."
        },
        {
            'question_uz': "Kurs narxi qancha?",
            'answer_uz': "Kurs narxi oyiga $10. Referal orqali chegirmalar mavjud.",
            'question_ru': "Сколько стоит курс?",
            'answer_ru': "Курс стоит $10 в месяц. Доступны скидки по реферальной программе.",
            'question_en': "How much does the course cost?",
            'answer_en': "The course costs $10 per month. Discounts are available through the referral program."
        },
        {
            'question_uz': "Referal tizimi qanday ishlaydi?",
            'answer_uz': "Har bir to'lov qilgan referal uchun chegirma olasiz. 10+ referal uchun kurs bepul!",
            'question_ru': "Как работает реферальная система?",
            'answer_ru': "Вы получаете скидку за каждого оплатившего реферала. При 10+ рефералах курс бесплатный!",
            'question_en': "How does the referral system work?",
            'answer_en': "You get a discount for each paying referral. With 10+ referrals, the course is free!"
        }
    ]

    for item in faq_items:
        async with db.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO faq (question_uz, answer_uz, question_ru, answer_ru, question_en, answer_en)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', item['question_uz'], item['answer_uz'], item['question_ru'],
                               item['answer_ru'], item['question_en'], item['answer_en'])

    print("✅ Ma'lumotlar bazasi va boshlang'ich ma'lumotlar muvaffaqiyatli o'rnatildi!")
    await db.close_pool()


if __name__ == "__main__":
    asyncio.run(setup_initial_data())
