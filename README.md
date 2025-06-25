# ESL Telegram Bot

Bu loyiha ESL (English as a Second Language) kurslari uchun Telegram bot hisoblanadi. Bot foydalanuvchilarni ro'yxatdan
o'tkazish, to'lovlarni boshqarish va referal tizimi kabi funksiyalarni amalga oshiradi.

## Xususiyatlari

- **Ko'p tilli qo'llab-quvvatlash**: O'zbek, Rus va Ingliz tillari
- **Foydalanuvchi ro'yxatdan o'tish**: To'liq ism, telefon, yosh va viloyat ma'lumotlari
- **To'lov tizimi**: Screenshot orqali to'lovni tasdiqlash
- **Referal tizimi**: Chegirmalar va bepul kurslar
- **FAQ tizimi**: Avtomatik savol-javoblar
- **Admin panel**: Foydalanuvchilar va to'lovlarni boshqarish
- **Avtomatik bildirishnomalar**: Dars vaqti eslatmalari

## O'rnatish

1. **Loyihani klonlash**:

```bash
git clone <repository-url>
cd esl-telegram-bot
```

2. **Virtual muhit yaratish**:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

3. **Paketlarni o'rnatish**:

```bash
pip install -r requirements.txt
```

4. **PostgreSQL ma'lumotlar bazasini o'rnatish**:

```bash
# PostgreSQL o'rnatish va ma'lumotlar bazasi yaratish
createdb esl_bot
```

5. **Muhit o'zgaruvchilarini sozlash**:
   `.env` faylini yarating va quyidagi ma'lumotlarni kiriting:

```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://username:password@localhost:5432/esl_bot
ADMIN_GROUP_ID=-1001234567890
SECRET_GROUP_LINK=https://t.me/+secret_group_link
```

6. **Ma'lumotlar bazasini sozlash**:

```bash
python setup_database.py
```

7. **Botni ishga tushirish**:

```bash
python main.py
```

## Fayllar tuzilishi

- `main.py` - Botning asosiy fayli
- `config.py` - Konfiguratsiya sozlamalari
- `database.py` - Ma'lumotlar bazasi bilan ishlash
- `handlers.py` - Bot handlarlari
- `keyboards.py` - Klaviatura tugmalari
- `texts.py` - Ko'p tilli matnlar
- `states.py` - FSM holatlari
- `notifications.py` - Avtomatik bildirishnomalar
- `admin_panel.py` - Admin panel CLI
- `discount_calculator.py` - Referal chegirmalari hisoblagichi
- `setup_database.py` - Ma'lumotlar bazasini sozlash skripti

## Admin Panel

Admin panelni ishlatish uchun:

```bash
python admin_panel.py
```

Admin panel imkoniyatlari:

- Foydalanuvchilar ro'yxatini ko'rish
- To'lov statistikasi
- Referal statistikasi
- Ma'lumotlarni CSV formatida eksport qilish
- FAQ elementlarini qo'shish

## Referal Tizimi

Referal asosidagi chegirmalar:

- 1-2 referal: 10% chegirma
- 3-9 referal: 30% chegirma
- 10-99 referal: 50% chegirma
- 100+ referal: 100% chegirma (bepul)

## Xavfsizlik

- Har bir foydalanuvchiga guruh linki faqat bir marta yuboriladi
- To'lovlar admin tomonidan qo'lda tasdiqlanadi
- Referal hisobiga faqat to'lov qilganlar kiradi