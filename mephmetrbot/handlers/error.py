from aiogram import Router, F
from aiogram.types import ErrorEvent, Message
from mephmetrbot.config import bot, LOGS_CHAT_ID

router = Router()

@router.error(F.update.message.as_("message"))
async def error_handler(event: ErrorEvent, message: Message):
    exception = event.exception
    user_id = event.update.message.from_user.id
    first_name = event.update.message.from_user.first_name
    chat_id = event.update.message.chat.id
    text = event.update.message.text
    await bot.send_message(
        LOGS_CHAT_ID,
        f"<b>#ERROR</b>\n\n"
        f"first_name: <a href='tg://user?id={user_id}'>{first_name}</a>\n"
        f"user_id: <code>{user_id}</code>\n"
        f"chat_id: <code>{chat_id}</code>\n"
        f"text: <code>{text}</code>\n\n"
        f"exception: <code>{exception}</code>\n\n",
        parse_mode='HTML'
    )
    await message.reply('💀 Произошла непредвиденная ошибка, пожалуйста обратитесь к разработчику бота: @vccuser')