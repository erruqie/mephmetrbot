import os
import sys
import logging

from tortoise import Tortoise
from aiogram.types import Message
from typing import Callable, Dict, Awaitable, Any
from aiogram import Bot, Dispatcher, BaseMiddleware

from mephmetrbot.handlers.models import Users
from mephmetrbot.handlers import user, admin, clan, casino, error
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
            await message.reply("🛑 *Вы были заблокированы в этом боте.*", parse_mode='markdown')
            return

        return await handler(message, data)

async def init_tortoise():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': ['mephmetrbot.handlers.models']}
    )
    await Tortoise.generate_schemas(safe=True)

async def on_startup(bot):
    await init_tortoise()
    await bot.send_message(LOGS_CHAT_ID, f'🤖 Бот был запущен!', parse_mode='markdown')

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

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.run_polling(bot)

if __name__ == '__main__':
    main()
