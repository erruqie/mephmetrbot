import asyncio
import logging
import sqlite3
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import bot
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from handlers.casino import router as casino_router
from handlers.clan import router as clan_router

logging.basicConfig(level=logging.INFO)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(admin_router)
dp.include_router(user_router)
dp.include_router(casino_router)
dp.include_router(clan_router)


conn = sqlite3.connect('handlers/mephmetrbot.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, drug_count INTEGER, last_use_time TEXT, is_admin INTEGER, is_banned INTEGER, last_casino TEXT, last_find TEXT, clan_member INTEGER, clan_invite INTEGER)')
cursor.execute('CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY, is_ads_enable INTEGER DEFAULT 1)')
cursor.execute('CREATE TABLE IF NOT EXISTS clans (clan_id INTEGER PRIMARY KEY, clan_name TEXT, clan_owner_id INTEGER, clan_balance INTEGER)')
conn.commit()

async def run():
    await dp.start_polling(bot)

def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()