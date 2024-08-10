from mephmetrbot.config import bot
from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, WebAppInfo
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.message(Command('airdrop'))
async def airdrop_command(message: Message):
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text='Привязать кошелёк', web_app=WebAppInfo(url="https://airdrop-7de18.web.app/"))
        )
        await message.reply(
            "Привет! Нажми на кнопку ниже, чтобы забрать Airdrop",
            reply_markup=builder.as_markup()
        )
    except:
        await message.reply('📛️️ Эта команда работает только в ЛС с ботом!')
        return