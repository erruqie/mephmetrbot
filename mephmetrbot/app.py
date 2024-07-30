import os
import sys
import logging

from tortoise import Tortoise
from aiogram.types import Message
from typing import Callable, Dict, Awaitable, Any
from aiogram import Bot, Dispatcher, BaseMiddleware
import asyncio
from mephmetrbot.handlers.models import Users
from mephmetrbot.handlers import user, admin, clan, casino, error, cryptopay
from mephmetrbot.config import BOT_TOKEN, DATABASE_URL, LOGS_CHAT_ID

logging.basicConfig(level=logging.INFO)

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
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
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
