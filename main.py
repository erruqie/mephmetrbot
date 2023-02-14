import os
import random
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from dotenv import load_dotenv, find_dotenv


logging.basicConfig(level=logging.INFO)
load_dotenv(find_dotenv())

bot = Bot(token=os.environ.get('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect('data.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, drug_count INTEGER, last_use_time TEXT, is_admin INTEGER, is_banned INTEGER, last_casino TEXT, last_find TEXT)')
conn.commit()


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    channel_button = InlineKeyboardButton('📢 Канал', url='https://t.me/mefmetrch')
    donate_button = InlineKeyboardButton('💰 Донат', url='https://t.me/mefmetrch')
    chat_button = InlineKeyboardButton('💬 Чат', url='https://t.me/mefmetrchat')
    keyboard.row(channel_button, donate_button, chat_button)
    await message.reply("👋 *Здарова шныр*, этот бот сделан для того, чтобы *считать* сколько *грамм мефедрончика* ты можешь снюхать\n🧑‍💻 Бот разработан *@xanaxnotforfree* и *@cl0wnl3ss*", reply_markup=keyboard, parse_mode='markdown')

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.reply('Все команды бота:\n\n`/drug` - *принять мефик*\n`/top` - *топ торчей мира*\n`/take` - *спиздить мефик у ближнего*\n`/give` - *поделиться мефиком*\n`/casino` - *All-in, всё или ничего*\n`/find` - *сходить за кладом*\n`/about` - *узнать подробнее о боте*', parse_mode='markdown')


@dp.message_handler(Command('profile'))
async def profile_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_admin = user[3]

    if user:
        drug_count = user[1]
        is_admin = user[3]
        if is_admin == 1:
            await message.reply(f"👑 *Создатель бота*\n👤 *Имя:* _{message.from_user.first_name}_\n👥 *Ваш username:* _@{message.from_user.username}_\n🌿 *Снюхано* _{drug_count}_ грамм.", parse_mode='markdown')
        else:
            await message.reply(f"👤 *Имя:* _{message.from_user.first_name}_\n👥 *Ваш username:* _@{message.from_user.username}_\n🌿 *Снюхано* _{drug_count}_ грамм.", parse_mode='markdown')
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
            await message.reply(f"❌ *{message.from_user.first_name}*, _ты уже нюхал(-а)!_\n\n🌿 Всего снюхано `{drug_count} грамм` мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
        
        elif random.randint(0,100) < 20:
            await message.reply(f"🧂 *{message.from_user.first_name}*, _ты просыпал(-а) весь мефчик!_\n\n🌿 Всего снюхано `{drug_count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
            await state.set_data({'time': datetime.now()})
        else:
            count = random.randint(1, 10)
            if user:
                cursor.execute('UPDATE users SET drug_count = drug_count + ? WHERE id = ?', (count, user_id))
            else:
                cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned) VALUES (?, ?, 0, 0)', (user_id, count))
            cursor.execute('UPDATE users SET last_use_time = ? WHERE id = ?', (datetime.now(), user_id))
            conn.commit()
            await message.reply(f"👍 *{message.from_user.first_name}*, _ты занюхнул(-а) {count} грамм мефчика!_\n\n🌿 Всего снюхано `{drug_count+count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
  
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
                if drug_count > 1:
                    last_time = await state.get_data()
                    if last_time and (datetime.now() - last_time['time']) < timedelta(days=1):
                        remaining_time = timedelta(days=1) - (datetime.now() - last_time['time'])
                        await message.reply(f"❌ Нельзя пиздить меф так часто! Ты сможешь спиздить меф через 1 день.")
                    else:
                        variables = ['zametil', 'otpor', 'pass']
                        randomed = random.choice(variables)
                        if randomed == 'zametil':
                            cursor.execute('UPDATE users SET drug_count = drug_count - 1 WHERE id = ?', (your_user_id,))
                            conn.commit()
                            await message.reply('❌ *Жертва тебя заметила*, и ты решил убежать. Спиздить меф не получилось. Пока ты бежал, *ты потерял* `1 гр.`', parse_mode='markdown')
                        elif randomed == 'otpor':
                            cursor.execute('UPDATE users SET drug_count = drug_count - 1 WHERE id = ?', (your_user_id,))
                            cursor.execute('UPDATE users SET drug_count = drug_count + 1 WHERE id = ?', (user_id,))
                            conn.commit()
                            await message.reply('❌ *Жертва тебя заметила*, и пизданула тебе бутылкой по башке бля. Спиздить меф не получилось. *Жертва достала из твоего кармана* `1 гр.`', parse_mode='markdown')
                            
                        elif randomed == 'pass':
                            cursor.execute('UPDATE users SET drug_count = drug_count - 1 WHERE id = ?', (user_id,))
                            cursor.execute('UPDATE users SET drug_count = drug_count + 1 WHERE id = ?', (your_user_id,))
                            conn.commit()
                            await message.reply(f"✅ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) _спиздил(-а) один грам мефа у_ *@{reply_msg.from_user.username}*!", parse_mode='markdown')
                        await state.set_data({'time': datetime.now()})
                elif drug_count < 1:
                    await message.reply('❌ У жертвы недостаточно снюханного мефа для того чтобы его спиздить')
            else:
                await message.reply('❌ Этот пользователь еще не нюхал меф')
        else:
            await message.reply('❌ Ответьте на сообщение пользователя, у которого хотите спиздить мефедрон.')

@dp.message_handler(commands=['casino'])
async def casino(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    drug_count = user[1]
    last_used = user[5]
    if drug_count < 20:
        await message.reply(f"🛑 Для игры в казино необходимо имееть больше *20-ти снюханных грамм*", parse_mode='markdown')
    else:
        if last_used is not None and (datetime.now() - datetime.fromisoformat(last_used)).total_seconds() < 3600:
            await message.reply('⏳ Ты только что *крутил казик*, солевая обезьяна, *подожди один час по братски.*', parse_mode='markdown')
            return
        randomed = random.randint(1,100)
        multipliers = [5, 2.5, 2, 1.5, 0]
        weights = [1, 2, 3, 4, 5]
        multiplier = random.choices(multipliers, weights, k=1)[0]
        if multiplier > 0:
            drug_count *= multiplier
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count, user_id,))
            conn.commit()
            await bot.send_message(-1001659076963, f"#CASINO\n\nfirst\_name: `{message.from_user.first_name}`\nuserid: `{user_id}`\nmultiplier: `{multiplier}`\ndrug\_count: `{drug_count}`\n\n[mention](tg://user?id={user_id})", parse_mode='markdown')
            await message.reply(f'🤑 *Ебать тебе повезло!* Твое кол-во снюханных грамм *умножилось* на `{multiplier}` и теперь равно `{drug_count}`.', parse_mode='markdown')
           
        elif multiplier == 0:
            drug_count = 0
            cursor.execute('UPDATE users SET last_casino = ? WHERE id = ?', (datetime.now().isoformat(), user_id,))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count, user_id,))
            conn.commit()
            await bot.send_message(-1001659076963, f"#CASINO\n\nfirst\_name: `{message.from_user.first_name}`\nuserid: `{user_id}`\nmultiplier: `{multiplier}`\ndrug\_count: `{drug_count}`\n\n[mention](tg://user?id={user_id})", parse_mode='markdown')
            await message.reply('😔 *Ты проебал* весь свой мефчик, *нехуй было* крутить казик.', parse_mode='markdown')


@dp.message_handler(commands=['give'])
async def give_command(message: types.Message, state: FSMContext):

    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    else:
        args = message.get_args().split(maxsplit=1)
        if args:
            value = int(args[0])
            reply_msg = message.reply_to_message
            if reply_msg and reply_msg.from_user.id != message.from_user.id:
                user_id = reply_msg.from_user.id
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()
                your_user_id = message.from_user.id
                cursor.execute('SELECT * FROM users WHERE id = ?', (your_user_id,))
                your_user = cursor.fetchone()

                if user and your_user:
                    drug_count = your_user[1]
                    last_time = await state.get_data()
                    if last_time and (datetime.now() - last_time['time']) < timedelta(days=1):
                        remaining_time = timedelta(days=1) - (datetime.now() - last_time['time'])
                        await message.reply(f"❌ Нельзя делиться мефом так часто! Ты сможешь подарить меф через 1 день.")
                    else:
                        if drug_count >= value:
                            cursor.execute('UPDATE users SET drug_count = drug_count + ? WHERE id = ?', (value,user_id))
                            cursor.execute('UPDATE users SET drug_count = drug_count - ? WHERE id = ?', (value,your_user_id))
                            conn.commit()
                            await bot.send_message(-1001659076963, f"#GIVE\n\nfirst\_name: `{message.from_user.first_name}`\nuserid: `{user_id}`\nto: `{reply_msg.from_user.first_name}`\nvalue: `{value}`\nmention: @{reply_msg.from_user.username}", parse_mode='markdown')
                            await message.reply(f"✅ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) _подарил(-а) {value} гр. мефа _ *@{reply_msg.from_user.username}*!", parse_mode='markdown')
                            await state.set_data({'time': datetime.now()})
                        elif drug_count < value:
                            await message.reply(f'❌ Недостаточно граммов мефа для того чтобы их передать')
                else:
                    await message.reply('❌ Этот пользователь еще не нюхал меф')
            else:
                await message.reply('❌ Ответьте на сообщение пользователя, которому хотите дать мефедрона.')
        else:
            await message.reply('❌ Укажи сколько грамм хочешь подарить\nПример:\n`/give 20`', parse_mode='markdown')

@dp.message_handler(commands=['find'])
async def drug_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    drug_count = user[1] if user else 0
    last_time = await state.get_data()
    last_used = user[6]
    if last_used is not None and (datetime.now() - datetime.fromisoformat(last_used)).total_seconds() < 43200:
        await message.reply('⏳ Ты недавно *ходил за кладом*, *подожди 12 часов.*', parse_mode='markdown')
        return
    else:
        if random.randint(1,100) > 50:
            count = random.randint(1, 10)
            if user:
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count + count, user_id))
            else:
                cursor.execute('INSERT INTO users (id, drug_count) VALUES (?, ?)', (user_id, count))
            cursor.execute('UPDATE users SET last_use_time = ? WHERE id = ?', ('2006-02-20 12:45:37.666666', user_id,))
            cursor.execute('UPDATE users SET last_find = ? WHERE id = ?', (datetime.now().isoformat(), user_id,))
            conn.commit()
            await bot.send_message(-1001659076963, f"#FIND #WIN\n\nfirst\_name: `{message.from_user.first_name}`\ncount: `{count}`\ndrug\_count: `{drug_count+count}`\n\n[mention](tg://user?id={user_id})", parse_mode='markdown')
            await message.reply(f"👍 {message.from_user.first_name}, ты пошёл в лес и *нашел клад*, там лежало `{count} гр.` мефчика!\n🌿 Твое время команды /drug обновлено", parse_mode='markdown')
        elif random.randint(1,100) <= 50:
            count = random.randint(1, drug_count)
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count - count, user_id,))
            conn.commit()
            await bot.send_message(-1001659076963, f"#FIND #LOSE\n\nfirst\_name: `{message.from_user.first_name}`\ncount: `{count}`\ndrug\_count: `{drug_count-count}`\n\n[mention](tg://user?id={user_id})", parse_mode='markdown')
            await message.reply(f"❌ *{message.from_user.first_name}*, тебя *спалил мент* и *дал тебе по ебалу*\n🌿 Тебе нужно откупиться, мент предложил взятку в размере `{count} гр.`\n⏳ Следующая попытка доступна через *12 часов.*", parse_mode='markdown')
            


@dp.message_handler(commands=['banuser'])
async def banuser_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
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

@dp.message_handler(commands='about')
async def about_command(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    channel_button = InlineKeyboardButton('📢 Канал', url='https://t.me/mefmetrch')
    donate_button = InlineKeyboardButton('💰 Донат', url='https://t.me/mefmetrch')
    chat_button = InlineKeyboardButton('💬 Чат', url='https://t.me/mefmetrchat')
    keyboard.row(channel_button, donate_button, chat_button)
    await message.reply("🧑‍💻 Бот разработан @xanaxnotforfree и @cl0wnl3ss.", reply_markup=keyboard)

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