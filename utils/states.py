from aiogram.dispatcher.filters.state import State, StatesGroup

class BroadcastForm(StatesGroup):
    text = State()
    photo = State()
    confirm = State()