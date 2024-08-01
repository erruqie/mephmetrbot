import os
import sys
import logging

from tortoise import Tortoise
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable, Dict, Awaitable, Any
from aiogram import Bot, Dispatcher, BaseMiddleware
import asyncio
from mephmetrbot.handlers.models import Users
from mephmetrbot.handlers import user, admin, clan, casino, error, cryptopay
from mephmetrbot.config import BOT_TOKEN, DATABASE_URL, LOGS_CHAT_ID
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)


class SubscribeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
    ) -> Any:
        status = await get_subscribe_status(bot, message.from_user.id)
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="Подписаться", url="https://t.me/mefmetrch")
        )
    
        if status == 'left':
            await message.reply('🛑 Для начала подпишись на наш канал',reply_markup=builder.as_markup())
            return
        return await handler(message, data)

class BannedMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
    ) -> Any:
        assert(message.from_user is not None)
        user, _ = await Users.get_or_create(id=message.from_user.id)

        if user.is_banned:
            ban_reason = user.ban_reason if user.ban_reason else "Причина не указана"
            await message.reply(f"🛑 <b>Вы были заблокированы в этом боте.</b>\n📔 *Причина*: <code>{ban_reason}</code>", parse_mode='HTML')
            return

        return await handler(message, data)

async def get_subscribe_status(bot, user_id):
    user, _ = await Users.get_or_create(id=user_id)
    user_channel_status = await bot.get_chat_member(chat_id='-1002177701917', user_id=user_id)
    return user_channel_status.status

async def init_tortoise():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': ['mephmetrbot.handlers.models']}
    )
    await Tortoise.generate_schemas(safe=True)

async def check_invitation_expiry():
    while True:
        now = datetime.now()
        expiry_time = now - timedelta(minutes=5)
        await Users.filter(clan_invite__gt=0, invite_timestamp__lt=expiry_time).update(clan_invite=0, invite_timestamp=None)
        await asyncio.sleep(60)

async def on_startup(bot):
    await init_tortoise()
    await bot.send_message(LOGS_CHAT_ID, f'🤖 <b>Бот был запущен!</b>', parse_mode='HTML')
    asyncio.create_task(check_invitation_expiry())



async def on_shutdown():
    await Tortoise.close_connections()

def main():
    global bot
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.message.middleware(SubscribeMiddleware())
    dp.message.middleware(BannedMiddleware())
    dp.include_router(error.router)
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(clan.router)
    dp.include_router(casino.router)
    dp.include_router(cryptopay.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.run_polling(bot)

if __name__ == '__main__':
    main()
