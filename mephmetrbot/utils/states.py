from aiogram.fsm.state import StatesGroup, State

class BroadcastForm(StatesGroup):
    text = State()
    photo = State()
    confirm = State()