from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    language = State()
    name = State()
    phone = State()
    age = State()
    region = State()
    change_language = State()
    subscription = State()


class Payment(StatesGroup):
    screenshot = State()


class Question(StatesGroup):
    text = State()


class Settings(StatesGroup):
   change_age = State()
   change_name = State()
   change_phone = State()
   change_region = State()
   change_language = State()
