import os
import random
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from dotenv import load_dotenv, find_dotenv
import sqlite3

logging.basicConfig(level=logging.INFO)
load_dotenv(find_dotenv())

bot = Bot(token=os.environ.get('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect('data.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, drug_count INTEGER, last_use_time TEXT, is_admin INTEGER, is_banned INTEGER)')
conn.commit()


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply('Напиши /drug и снюхай меф')

@dp.message_handler(Command('profile'))
async def profile_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        drug_count = user[1]
        await message.reply(f"👤 *Имя:* _{message.from_user.first_name}_\n👥 *Ваш username:* _@{message.from_user.username}_\n🎖 *Вы приняли мефчик* _{drug_count}_ раз(а).", parse_mode='markdown')
    else:
        await message.reply('❌ Вы еще не нюхали мефчик')

@dp.message_handler(Command('drug'))
async def drug_command(message: types.Message, state: FSMContext):
    format = '%Y-%m-%d %H:%M:%S.%f'
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    drug_count = user[1] if user else 0
    last_use_time = user[2] if user else 0
    is_admin = user[3] if user else 0
    is_banned = user[4] if user else 0
    use_time = datetime.strptime(last_use_time, format) if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    else:
        if last_use_time and (datetime.now() - use_time) < timedelta(hours=1):
            remaining_time = timedelta(hours=1) - (datetime.now() - use_time)
            #debug
            #await message.answer(f"remaining_time: {remaining_time}\nlast_use_time: {use_time}")
            await message.reply(f"❌ *{message.from_user.first_name}*, _ты уже нюхал(-а)!_\n\n🌿 Всего занюхано `{drug_count} грамм` мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
        
        elif random.randint(0,100) < 20:
            await message.reply(f"🧂 *{message.from_user.first_name}*, _ты просыпал(-а) весь мефчик!_\n\n🌿 Всего занюхано `{drug_count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
            await state.set_data({'time': datetime.now()})
        
        else:
            count = random.randint(1, 10)
            await message.reply(f"👍 *{message.from_user.first_name}*, _ты занюхнул(-а) {count} грамм мефчика!_\n\n🌿 Всего занюхано `{drug_count+count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
            if user:
                cursor.execute('UPDATE users SET drug_count = drug_count + ? WHERE id = ?', (count, user_id))
            else:
                cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned) VALUES (?, ?, 0, 0)', (user_id, count))
            cursor.execute('UPDATE users SET last_use_time = ? WHERE id = ?', (datetime.now(), user_id))
            conn.commit()
        
  
@dp.message_handler(commands=['top'])
async def top_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    else:
        cursor.execute('SELECT id, drug_count FROM users ORDER BY drug_count DESC LIMIT 10')
        top_users = cursor.fetchall()
        if top_users:
            response = "🔝ТОП 10 ЛЮТЫХ МЕФЕНДРОНЩИКОВ В МИРЕ🔝:\n"
            counter = 1
            for user in top_users:
                user_id = user[0]
                drug_count = user[1]
                user_info = await bot.get_chat(user_id)
                response += f"{counter}) *{user_info.full_name}*: `{drug_count} грамм мефедрона`\n"
                counter += 1
            await message.reply(response, parse_mode='markdown')
        else:
            await message.reply('Никто еще не принимал меф.')


@dp.message_handler(commands=['take'])
async def take_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    else:
        reply_msg = message.reply_to_message
        if reply_msg and reply_msg.from_user.id != message.from_user.id:
            user_id = reply_msg.from_user.id
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            your_user_id = message.from_user.id
            cursor.execute('SELECT * FROM users WHERE id = ?', (your_user_id,))
            your_user = cursor.fetchone()

            if user and your_user:
                drug_count = user[1]
                last_time = await state.get_data()
                if last_time and (datetime.now() - last_time['time']) < timedelta(days=1):
                    remaining_time = timedelta(days=1) - (datetime.now() - last_time['time'])
                    await message.reply(f"❌ Нельзя пиздить меф так часто! Ты сможешь спиздить меф через 1 день.")
                else:
                    cursor.execute('UPDATE users SET drug_count = drug_count - 1 WHERE id = ?', (user_id,))
                    conn.commit()
                    cursor.execute('UPDATE users SET drug_count = drug_count + 1 WHERE id = ?', (your_user_id,))
                    conn.commit()
                    await message.reply(f"✅ *{message.from_user.first_name}* _спиздил(-а) один грам мефа у_ *@{reply_msg.from_user.username}*!", parse_mode='markdown')
                    await state.set_data({'time': datetime.now()})
            else:
                await message.reply('❌ Этот пользователь еще не нюхал меф')
        else:
            await message.reply('❌ Ответьте на сообщение пользователя, у которого хотите спиздить мефедрон.')

@dp.message_handler(commands=['banuser'])
async def banuser_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    await message.reply(user)
    is_admin = user[3]
    if is_admin == 1:
        reply_msg = message.reply_to_message
        if reply_msg and reply_msg.from_user.id != message.from_user.id:
            bann_user_id = reply_msg.from_user.id
            cursor.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (bann_user_id,))
            conn.commit()
        await message.reply(f"🛑 Пользователь с ID: `{bann_user_id}` заблокирован", parse_mode='markdown')
    else:
        await message.reply('🚨 MONKEY ALARM')

@dp.message_handler(commands=['unbanuser'])
async def unbanuser_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_admin = user[3]
    if is_admin == 1:
        reply_msg = message.reply_to_message
        if reply_msg and reply_msg.from_user.id != message.from_user.id:
            bann_user_id = reply_msg.from_user.id
            cursor.execute('UPDATE users SET is_banned = 0 WHERE id = ?', (bann_user_id,))
            conn.commit()
        await message.reply(f"🛑 Пользователь с ID: `{bann_user_id}` разблокирован", parse_mode='markdown')
    else:
        await message.reply('🚨 MONKEY ALARM')

@dp.message_handler(commands=['getadminka'])
async def getadminka_command(message: types.Message):
    cursor.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (5510709343,))
    cursor.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (1888296065,))
    conn.commit()
    await message.reply('✅')

@dp.message_handler(commands=['setdrugs'])
async def setdrugs_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_admin = user[3]
    if is_admin == 1:
        args = message.get_args().split(maxsplit=1)
        cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (args[1],args[0]))
        conn.commit()
        await message.reply('✅')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)