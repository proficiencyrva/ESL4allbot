from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from texts import TEXTS


def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])


def contact_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]['share_contact'], request_contact=True)],
            [KeyboardButton(text=TEXTS[lang]['change_language'])]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def skip_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]['skip'])],
            [KeyboardButton(text=TEXTS[lang]['change_language'])]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def regions_keyboard(lang):
    keyboard = []
    regions = TEXTS[lang]['regions']
    for i in range(0, len(regions), 2):
        row = [KeyboardButton(text=regions[i])]
        if i + 1 < len(regions):
            row.append(KeyboardButton(text=regions[i + 1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton(text=TEXTS[lang]['change_language'])])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def main_menu_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]['payment']), KeyboardButton(text=TEXTS[lang]['questions'])],
            [KeyboardButton(text=TEXTS[lang]['referral']), KeyboardButton(text=TEXTS[lang]['settings'])]
        ],
        resize_keyboard=True
    )


def questions_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]['faq']), KeyboardButton(text=TEXTS[lang]['ask_question'])],
            [KeyboardButton(text=TEXTS[lang]['main_menu'])]
        ],
        resize_keyboard=True
    )


def payment_admin_keyboard(payment_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{payment_id}")
        ]
    ])


def settings_keyboard(lang):
   return ReplyKeyboardMarkup(
       keyboard=[
           [KeyboardButton(text=TEXTS[lang]['change_name']), KeyboardButton(text=TEXTS[lang]['change_age'])],
           [KeyboardButton(text=TEXTS[lang]['change_number']), KeyboardButton(text=TEXTS[lang]['change_city'])],
           [KeyboardButton(text=TEXTS[lang]['change_language'])],
           [KeyboardButton(text=TEXTS[lang]['main_menu'])]
       ],
       resize_keyboard=True
   )
