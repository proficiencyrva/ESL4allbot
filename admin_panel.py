import asyncio
import asyncpg
from config import DATABASE_URL


class AdminPanel:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    async def get_all_users(self):
        """Get all users with their statistics"""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT 
                    u.telegram_id,
                    u.full_name,
                    u.phone,
                    u.age,
                    u.region,
                    u.language,
                    u.referral_count,
                    u.payment_status,
                    u.created_at,
                    COUNT(p.id) as payment_attempts
                FROM users u
                LEFT JOIN payments p ON u.telegram_id = p.user_id
                GROUP BY u.telegram_id, u.full_name, u.phone, u.age, u.region, 
                         u.language, u.referral_count, u.payment_status, u.created_at
                ORDER BY u.created_at DESC
            ''')

    async def get_payment_statistics(self):
        """Get payment statistics"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_payments,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_payments,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_payments,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_payments
                FROM payments
            ''')
            return stats

    async def get_referral_statistics(self):
        """Get referral statistics"""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT 
                    u.telegram_id,
                    u.full_name,
                    u.referral_count,
                    COUNT(r.telegram_id) as actual_referrals,
                    COUNT(CASE WHEN r.payment_status = TRUE THEN 1 END) as paid_referrals
                FROM users u
                LEFT JOIN users r ON u.telegram_id = r.referrer_id
                WHERE u.referral_count > 0
                GROUP BY u.telegram_id, u.full_name, u.referral_count
                ORDER BY u.referral_count DESC
            ''')

    async def export_users_csv(self):
        """Export users to CSV format"""
        users = await self.get_all_users()

        csv_content = "telegram_id,full_name,phone,age,region,language,referral_count,payment_status,created_at,payment_attempts\n"

        for user in users:
            csv_content += f"{user['telegram_id']},{user['full_name']},{user['phone']},{user['age']},{user['region']},{user['language']},{user['referral_count']},{user['payment_status']},{user['created_at']},{user['payment_attempts']}\n"

        return csv_content

    async def add_faq_item(self, question_uz, answer_uz, question_ru=None, answer_ru=None, question_en=None,
                           answer_en=None):
        """Add FAQ item"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO faq (question_uz, answer_uz, question_ru, answer_ru, question_en, answer_en)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', question_uz, answer_uz, question_ru, answer_ru, question_en, answer_en)

    async def get_pending_payments(self):
        """Get all pending payments"""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT 
                    p.id,
                    p.user_id,
                    p.screenshot_file_id,
                    p.created_at,
                    u.full_name,
                    u.phone,
                    u.region
                FROM payments p
                JOIN users u ON p.user_id = u.telegram_id
                WHERE p.status = 'pending'
                ORDER BY p.created_at ASC
            ''')

    async def close_pool(self):
        if self.pool:
            await self.pool.close()


# CLI interface for admin panel
async def admin_cli():
    """Command line interface for admin operations"""
    admin = AdminPanel()
    await admin.create_pool()

    while True:
        print("\n=== ESL Bot Admin Panel ===")
        print("1. Ko'rish - Barcha foydalanuvchilar")
        print("2. Ko'rish - To'lov statistikasi")
        print("3. Ko'rish - Referal statistikasi")
        print("4. Eksport - Foydalanuvchilar CSV")
        print("5. Qo'shish - FAQ elementi")
        print("6. Ko'rish - Kutilayotgan to'lovlar")
        print("0. Chiqish")

        choice = input("\nTanlang (0-6): ")

        if choice == "1":
            users = await admin.get_all_users()
            print(f"\n=== Jami foydalanuvchilar: {len(users)} ===")
            for user in users:
                print(
                    f"ID: {user['telegram_id']} | Ism: {user['full_name']} | Tel: {user['phone']} | Viloyat: {user['region']} | To'lov: {'✅' if user['payment_status'] else '❌'} | Referallar: {user['referral_count']}")

        elif choice == "2":
            stats = await admin.get_payment_statistics()
            print(f"\n=== To'lov Statistikasi ===")
            print(f"Jami: {stats['total_payments']}")
            print(f"Tasdiqlangan: {stats['approved_payments']}")
            print(f"Rad etilgan: {stats['rejected_payments']}")
            print(f"Kutilayotgan: {stats['pending_payments']}")

        elif choice == "3":
            refs = await admin.get_referral_statistics()
            print(f"\n=== Referal Statistikasi ===")
            for ref in refs:
                print(
                    f"{ref['full_name']} | Referallar: {ref['actual_referrals']} | To'lov qilganlar: {ref['paid_referrals']}")

        elif choice == "4":
            csv_content = await admin.export_users_csv()
            with open("users_export.csv", "w", encoding="utf-8") as f:
                f.write(csv_content)
            print("✅ users_export.csv fayli yaratildi!")

        elif choice == "5":
            print("\n=== FAQ qo'shish ===")
            q_uz = input("Savol (O'zbek): ")
            a_uz = input("Javob (O'zbek): ")
            q_ru = input("Savol (Rus, ixtiyoriy): ") or None
            a_ru = input("Javob (Rus, ixtiyoriy): ") or None
            q_en = input("Savol (Ingliz, ixtiyoriy): ") or None
            a_en = input("Javob (Ingliz, ixtiyoriy): ") or None

            await admin.add_faq_item(q_uz, a_uz, q_ru, a_ru, q_en, a_en)
            print("✅ FAQ qo'shildi!")

        elif choice == "6":
            payments = await admin.get_pending_payments()
            print(f"\n=== Kutilayotgan to'lovlar: {len(payments)} ===")
            for payment in payments:
                print(f"ID: {payment['id']} | Foydalanuvchi: {payment['full_name']} | Vaqt: {payment['created_at']}")

        elif choice == "0":
            break

        else:
            print("Noto'g'ri tanlov!")

    await admin.close_pool()


if __name__ == "__main__":
    asyncio.run(admin_cli())
