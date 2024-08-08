from mephmetrbot.config import bot
from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters.command import Command


router = Router()


@router.message(Command('airdrop'))
async def airdrop_command(message: Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Open Webview", web_app=WebAppInfo(url="https://google.com/"))
            ]
        ]
    )
    await message.answer(
        "Привет! Нажми на кнопку ниже, чтобы забрать Airdrop",
        reply_markup=markup
    )