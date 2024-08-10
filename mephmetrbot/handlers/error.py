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
        f"❗ <b>#ERROR</b>\n\n"
        f"👤 <b>First Name:</b> <a href='tg://user?id={user_id}'>{first_name}</a>\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"💬 <b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"📝 <b>Text:</b> <code>{text}</code>\n\n"
        f"⚠️ <b>Exception:</b> <code>{exception}</code>\n\n",
        parse_mode='HTML'
    )
    await message.reply('💀 Произошла непредвиденная ошибка, пожалуйста обратитесь к разработчику бота: @vccuser')