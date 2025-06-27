from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from database import db
from keyboards import *
from texts import TEXTS
from states import Registration, Payment, Question, Settings
import re

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    # Check for referral
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith('ref'):
        try:
            referrer_id = int(args[1][3:])
        except ValueError:
            pass

    await state.update_data(referrer_id=referrer_id)

    user = await db.get_user(message.from_user.id)
    if user:
        lang = user['language']
        await message.answer(TEXTS[lang]['main_menu'], reply_markup=main_menu_keyboard(lang))
    else:
        await message.answer(TEXTS['uz']['choose_language'], reply_markup=language_keyboard())
        await state.set_state(Registration.language)


@router.callback_query(F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    await callback.message.edit_text(TEXTS[lang]['welcome'])
    await callback.message.answer(TEXTS[lang]['enter_name'])
    await state.set_state(Registration.name)


@router.message(Registration.name)
async def name_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['language']

    await state.update_data(name=message.text)
    await message.answer(TEXTS[lang]['enter_phone'], reply_markup=contact_keyboard(lang))
    await state.set_state(Registration.phone)


@router.message(Registration.phone)
async def phone_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['language']

    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    await state.update_data(phone=phone)
    await message.answer(TEXTS[lang]['enter_age'], reply_markup=skip_keyboard(lang))
    await state.set_state(Registration.age)


@router.message(Registration.age)
async def age_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['language']

    age = None
    if message.text != TEXTS[lang]['skip']:
        try:
            age = int(message.text)
        except ValueError:
            await message.answer("Iltimos, raqam kiriting yoki tashlab keting.")
            return

    await state.update_data(age=age)
    await message.answer(TEXTS[lang]['enter_region'], reply_markup=regions_keyboard(lang))
    await state.set_state(Registration.region)


@router.message(Registration.region)
async def region_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['language']

    await state.update_data(region=message.text)

    # Save user to database
    await db.add_user(
        telegram_id=message.from_user.id,
        full_name=data['name'],
        phone=data['phone'],
        age=data.get('age'),
        region=message.text,
        language=lang,
        referrer_id=data.get('referrer_id')
    )

    await message.answer(
        TEXTS[lang]['registration_complete'],
        reply_markup=main_menu_keyboard(lang)
    )
    await state.clear()


@router.message(
    lambda message: message.text in [TEXTS['uz']['change_language'], TEXTS['ru']['change_language'], TEXTS['en']['change_language']],
    Registration.name
)
@router.message(
    lambda message: message.text in [TEXTS['uz']['change_language'], TEXTS['ru']['change_language'], TEXTS['en']['change_language']],
    Registration.phone
)
@router.message(
    lambda message: message.text in [TEXTS['uz']['change_language'], TEXTS['ru']['change_language'], TEXTS['en']['change_language']],
    Registration.age
)
@router.message(
    lambda message: message.text in [TEXTS['uz']['change_language'], TEXTS['ru']['change_language'], TEXTS['en']['change_language']],
    Registration.region
)
async def change_language_registration_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    await state.update_data(previous_state=current_state)
    data = await state.get_data()
    lang = data.get('language', 'uz')
    await message.answer(TEXTS[lang]['choose_language'], reply_markup=language_keyboard())
    await state.set_state(Registration.change_language)


@router.callback_query(Registration.change_language, F.data.startswith("lang_"))
async def process_change_language_registration_handler(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    data = await state.get_data()
    previous_state = data.get("previous_state")

    await callback.message.edit_text(TEXTS[lang]['language_changed'])

    if previous_state == Registration.name.state:
        await callback.message.answer(TEXTS[lang]['enter_name'])
        await state.set_state(Registration.name)
    elif previous_state == Registration.phone.state:
        await callback.message.answer(TEXTS[lang]['enter_phone'], reply_markup=contact_keyboard(lang))
        await state.set_state(Registration.phone)
    elif previous_state == Registration.age.state:
        await callback.message.answer(TEXTS[lang]['enter_age'], reply_markup=skip_keyboard(lang))
        await state.set_state(Registration.age)
    elif previous_state == Registration.region.state:
        await callback.message.answer(TEXTS[lang]['enter_region'], reply_markup=regions_keyboard(lang))
        await state.set_state(Registration.region)


# Main menu handlers
@router.message(F.text.in_([TEXTS['uz']['payment'], TEXTS['ru']['payment'], TEXTS['en']['payment']]))
async def payment_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await message.answer(TEXTS[lang]['payment_instruction'])
    await state.set_state(Payment.screenshot)


@router.message(Payment.screenshot, F.photo)
async def payment_screenshot_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    payment_id = await db.add_payment(message.from_user.id, message.photo[-1].file_id)

    # Send to admin group
    from main import bot
    from config import ADMIN_GROUP_ID

    admin_message = await bot.send_photo(
        ADMIN_GROUP_ID,
        message.photo[-1].file_id,
        caption=f"🆔 {message.from_user.id}\n👤 {user['full_name']}\n📞 {user['phone']}\n📍 {user['region']}",
        reply_markup=payment_admin_keyboard(payment_id)
    )

    # Update payment with admin message ID
    await db.pool.acquire().execute(
        'UPDATE payments SET admin_message_id = $1 WHERE id = $2',
        admin_message.message_id, payment_id
    )

    await message.answer(TEXTS[lang]['payment_sent'], reply_markup=main_menu_keyboard(lang))
    await state.clear()


@router.message(F.text.in_([TEXTS['uz']['questions'], TEXTS['ru']['questions'], TEXTS['en']['questions']]))
async def questions_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await message.answer(TEXTS[lang]['questions'], reply_markup=questions_keyboard(lang))


@router.message(F.text.in_([TEXTS['uz']['faq'], TEXTS['ru']['faq'], TEXTS['en']['faq']]))
async def faq_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    faq_items = await db.get_faq(lang)
    if not faq_items:
        await message.answer(TEXTS[lang]['no_faq'])
        return

    faq_text = ""
    for item in faq_items:
        faq_text += f"❓ {item['question']}\n💬 {item['answer']}\n\n"

    await message.answer(faq_text)


@router.message(F.text.in_([TEXTS['uz']['ask_question'], TEXTS['ru']['ask_question'], TEXTS['en']['ask_question']]))
async def ask_question_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await message.answer(TEXTS[lang]['enter_question'])
    await state.set_state(Question.text)


@router.message(Question.text)
async def question_text_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await db.add_question(message.from_user.id, message.text)

    # Send to admin group
    from main import bot
    from config import ADMIN_GROUP_ID

    await bot.send_message(
        ADMIN_GROUP_ID,
        f"📝 Yangi savol:\n🆔 {message.from_user.id}\n👤 {user['full_name']}\n❓ {message.text}"
    )

    await message.answer(TEXTS[lang]['question_sent'], reply_markup=main_menu_keyboard(lang))
    await state.clear()


@router.message(F.text.in_([TEXTS['uz']['referral'], TEXTS['ru']['referral'], TEXTS['en']['referral']]))
async def referral_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    stats = await db.get_referral_stats(message.from_user.id)
    referral_link = f"https://t.me/esl4allbot?start=ref{message.from_user.id}"

    await message.answer(
        TEXTS[lang]['your_referral_link'].format(
            link=referral_link,
            count=stats['referral_count'],
            paid=stats['paid_referrals']
        )
    )


@router.message(F.text.in_([TEXTS['uz']['main_menu'], TEXTS['ru']['main_menu'], TEXTS['en']['main_menu']]))
async def main_menu_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await message.answer(TEXTS[lang]['main_menu'], reply_markup=main_menu_keyboard(lang))


@router.message(F.text.in_([TEXTS['uz']['settings'], TEXTS['ru']['settings'], TEXTS['en']['settings']]))
async def settings_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await message.answer(TEXTS[lang]['settings'], reply_markup=settings_keyboard(lang))


@router.message(F.text.in_([TEXTS['uz']['change_age'], TEXTS['ru']['change_age'], TEXTS['en']['change_age']]))
async def change_age_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await message.answer(TEXTS[lang]['enter_age'])
    await state.set_state(Settings.change_age)


@router.message(Settings.change_age)
async def process_change_age_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    try:
        age = int(message.text)
        await db.update_user_age(message.from_user.id, age)
        await message.answer(TEXTS[lang]['changes_saved'], reply_markup=main_menu_keyboard(lang))
        await state.clear()
    except ValueError:
        await message.answer("Iltimos, raqam kiriting.")
        return


@router.message(F.text.in_([TEXTS['uz']['change_name'], TEXTS['ru']['change_name'], TEXTS['en']['change_name']]))
async def change_name_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']
    await message.answer(TEXTS[lang]['enter_name'])
    await state.set_state(Settings.change_name)


@router.message(Settings.change_name)
async def process_change_name_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']
    await db.update_user_name(message.from_user.id, message.text)
    await message.answer(TEXTS[lang]['changes_saved'], reply_markup=main_menu_keyboard(lang))
    await state.clear()


@router.message(F.text.in_([TEXTS['uz']['change_number'], TEXTS['ru']['change_number'], TEXTS['en']['change_number']]))
async def change_phone_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']
    await message.answer(TEXTS[lang]['enter_phone'])
    await state.set_state(Settings.change_phone)


@router.message(Settings.change_phone)
async def process_change_phone_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']
    await db.update_user_phone(message.from_user.id, message.text)
    await message.answer(TEXTS[lang]['changes_saved'], reply_markup=main_menu_keyboard(lang))
    await state.clear()


@router.message(F.text.in_([TEXTS['uz']['change_city'], TEXTS['ru']['change_city'], TEXTS['en']['change_city']]))
async def change_region_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']
    await message.answer(TEXTS[lang]['enter_region'], reply_markup=regions_keyboard(lang))
    await state.set_state(Settings.change_region)


@router.message(Settings.change_region)
async def process_change_region_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']
    await db.update_user_region(message.from_user.id, message.text)
    await message.answer(TEXTS[lang]['changes_saved'], reply_markup=main_menu_keyboard(lang))
    await state.clear()


@router.message(F.text.in_([TEXTS['uz']['change_language'], TEXTS['ru']['change_language'], TEXTS['en']['change_language']]))
async def change_language_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language'] if user else 'uz'
    await message.answer(TEXTS[lang]['choose_language'], reply_markup=language_keyboard())
    await state.set_state(Settings.change_language)


@router.callback_query(Settings.change_language, F.data.startswith("lang_"))
async def process_change_language_handler(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await db.update_user_language(callback.from_user.id, lang)
    # Edit the message in place with the new language and updated buttons
    await callback.message.edit_text(
        TEXTS[lang]['settings'],
        reply_markup=settings_keyboard(lang)
    )
    await callback.answer(TEXTS[lang]['language_changed'])
    await state.clear()


# Admin handlers
@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split("_")[1])

    await db.update_payment_status(payment_id, 'approved')

    # Get user info
    async with db.pool.acquire() as conn:
        payment = await conn.fetchrow('SELECT user_id FROM payments WHERE id = $1', payment_id)
        user = await db.get_user(payment['user_id'])

    # Send group link to user
    from main import bot
    from config import SECRET_GROUP_LINK

    await bot.send_message(
        payment['user_id'],
        TEXTS[user['language']]['payment_approved'] + f"\n{SECRET_GROUP_LINK}"
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ To'lov tasdiqlandi!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split("_")[1])

    await db.update_payment_status(payment_id, 'rejected')

    # Get user info
    async with db.pool.acquire() as conn:
        payment = await conn.fetchrow('SELECT user_id FROM payments WHERE id = $1', payment_id)
        user = await db.get_user(payment['user_id'])

    # Notify user
    from main import bot

    await bot.send_message(
        payment['user_id'],
        TEXTS[user['language']]['payment_rejected']
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("❌ To'lov rad etildi!")
