from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from database import db
from keyboards import *
from texts import TEXTS
from states import Registration, Payment, Question, Settings
import re
from config import ADMIN_GROUP_ID

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


@router.callback_query(Registration.language, F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    print(f'DEBUG: Registration.language callback handler triggered, FSM state: {current_state}')
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    # Send subscription message
    await callback.message.edit_text(TEXTS[lang]['subscription_required'], reply_markup=continue_keyboard(lang))
    await state.set_state(Registration.subscription)


@router.callback_query(Registration.subscription, F.data == 'continue_after_sub')
async def after_subscription_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data['language']
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
    print(f'DEBUG: Registration change_language handler triggered, FSM state: {current_state}')
    await state.update_data(previous_state=current_state)
    data = await state.get_data()
    lang = data.get('language', 'uz')
    await message.answer(TEXTS[lang]['choose_language'], reply_markup=language_keyboard())
    await state.set_state(Registration.change_language)


@router.callback_query(Registration.change_language, F.data.startswith("lang_"))
async def process_change_language_registration_handler(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    print(f'DEBUG: Registration change_language CALLBACK handler triggered, FSM state: {current_state}')
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
    print("DEBUG: payment_screenshot_handler triggered")
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    payment_id = await db.add_payment(message.from_user.id, message.photo[-1].file_id)

    # Send to admin group
    from main import bot

    admin_message = await bot.send_photo(
        ADMIN_GROUP_ID,
        message.photo[-1].file_id,
        caption=f"🆔 {message.from_user.id}\n👤 {user['full_name']}\n📞 {user['phone']}\n📍 {user['region']}",
        reply_markup=payment_admin_keyboard(payment_id)
    )

    # Update payment with admin message ID
    async with db.pool.acquire() as conn:
        await conn.execute(
            'UPDATE payments SET admin_message_id = $1 WHERE id = $2',
            admin_message.message_id, payment_id
        )

    # Debug print for language and available keys
    print(f"DEBUG: Sending payment success message. lang={lang}, available keys={list(TEXTS.keys())}")
    await message.answer(TEXTS[lang]['payment_success'], reply_markup=main_menu_keyboard(lang))
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

    username = message.from_user.username
    full_name = user['full_name']
    if username:
        user_line = f"👤: <a href='https://t.me/{username}'>{full_name}</a>"
    else:
        user_line = f"👤: {full_name}"

    await bot.send_message(
        ADMIN_GROUP_ID,
        f"📝 Yangi savol:\n<code>id:{message.from_user.id}</code>\n{user_line}\n💬 {message.text}",
        parse_mode="HTML"
    )

    await message.answer(TEXTS[lang]['question_sent'], reply_markup=main_menu_keyboard(lang))
    await state.clear()


@router.message(F.text.in_([TEXTS['uz']['referral'], TEXTS['ru']['referral'], TEXTS['en']['referral']]))
async def referral_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    stats = await db.get_referral_stats(message.from_user.id)
    referral_link = f"https://t.me/esl2Bot?start=ref{message.from_user.id}"

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
async def settings_handler(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user['language']

    await state.clear()

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
    current_state = await state.get_state()
    print(f'DEBUG: Settings change_language handler triggered, FSM state: {current_state}')
    user = await db.get_user(message.from_user.id)
    lang = user['language'] if user else 'uz'
    await message.answer(TEXTS[lang]['choose_language'], reply_markup=language_keyboard())
    await state.set_state(Settings.change_language)


@router.callback_query(Settings.change_language, F.data.startswith("lang_"))
async def process_change_language_handler(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    print(f'DEBUG: Settings change_language CALLBACK handler triggered, FSM state: {current_state}')
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


@router.message()
async def admin_reply_to_user_question(message: Message):
    # Only process messages in the admin group that are replies
    print(f"DEBUG: admin_reply_to_user_question called. message.chat.id={message.chat.id}, ADMIN_GROUP_ID={ADMIN_GROUP_ID} (type={type(ADMIN_GROUP_ID)})")
    if message.chat.id != int(ADMIN_GROUP_ID):
        print("DEBUG: Not in admin group, skipping.")
        return
    if not message.reply_to_message:
        print("DEBUG: Not a reply, skipping.")
        return
    # Try to extract user ID from the original message (text or caption)
    import re
    original_text = message.reply_to_message.text or message.reply_to_message.caption or ""
    match = re.search(r"id:(\d+)", original_text)
    if not match:
        print("DEBUG: Could not extract user ID from replied message.")
        return
    user_id = int(match.group(1))
    from main import bot
    # Send the admin's reply to the user (handle text, photo, document)
    if message.text:
        await bot.send_message(user_id, f"{message.text}")
        print(f"DEBUG: Sent text reply to user {user_id}")
    elif message.photo:
        await bot.send_photo(user_id, message.photo[-1].file_id, caption=f"{message.caption or ''}")
        print(f"DEBUG: Sent photo reply to user {user_id}")
    elif message.document:
        await bot.send_document(user_id, message.document.file_id, caption=f"{message.caption or ''}")
        print(f"DEBUG: Sent document reply to user {user_id}")
    else:
        await bot.send_message(user_id, "[Noma'lum fayl turi]")
        print(f"DEBUG: Sent unknown file type reply to user {user_id}")


@router.message(F.photo)
async def debug_any_photo_handler(message: Message, state: FSMContext):
    print("DEBUG: debug_any_photo_handler triggered")
    current_state = await state.get_state()
    print(f"DEBUG: Current FSM state: {current_state}")
    await message.answer("Photo received, but not in payment state.")
