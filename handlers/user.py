from aiogram import Router
import sqlite3
from datetime import datetime, timedelta
import os
import random
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.command import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import bot


router = Router()
conn = sqlite3.connect('handlers/mephmetrbot.db')
cursor = conn.cursor()

@router.message(Command('profile'))
async def profile_command(message: Message):
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif message.from_user:
        user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
            await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if user:
            drug_count = user[1]
            is_admin = user[3]
            clan_member = user[7]
            if clan_member:
                cursor.execute('SELECT clan_name FROM clans WHERE clan_id = ?', (clan_member,))
                clan = cursor.fetchone()
                clan_name = clan[0] if clan else 0
            if user_id == message.from_user.id:
                username = message.from_user.username if message.from_user.username else None
                full_name = message.from_user.full_name
            else:
                username = message.reply_to_message.from_user.username if message.reply_to_message.from_user.username else None
                full_name = message.reply_to_message.from_user.full_name

            if is_admin == 1:
                if clan_member:
                    await message.reply(f"👑 *Администратор*\n👤 *Имя:* _{full_name}_\n👥 *Клан:* *{clan_name}*\n👥 *Username пользователя:* @{username}\n🆔 *ID пользователя:* `{user_id}`\n🌿 *Снюхано* _{drug_count}_ грамм.", parse_mode='markdown')
                else:
                    await message.reply(f"👑 *Администратор*\n👤 *Имя:* _{full_name}_\n👥 *Username пользователя:* @{username}\n🆔 *ID пользователя:* `{user_id}`\n🌿 *Снюхано* _{drug_count}_ грамм.", parse_mode='markdown')
            else:
                if clan_member:
                    await message.reply(f"👤 *Имя:* _{full_name}_\n👥 *Клан:* *{clan_name}*\n👥 *Username пользователя:* @{username}\n🆔 *ID пользователя:* `{user_id}`\n🌿 *Снюхано* _{drug_count}_ грамм.", parse_mode='markdown')
                else:
                    await message.reply(f"👤 *Имя:* _{full_name}_\n👥 *Username пользователя:* @{username}\n🆔 *ID пользователя: * `{user_id}`\n🌿 *Снюхано* _{drug_count}_ грамм.", parse_mode='markdown')
        else:
            await message.reply('❌ Профиль не найден')


@router.message(Command('give'))
async def give_command(message: Message, state: FSMContext, command: CommandObject):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
        return
    args = command.args.split(' ', maxsplit=1)
    try:
        value = int(args[0])
    except ValueError:
        await message.reply('❌ Введи целое число')
        return
    reply_msg = message.reply_to_message
    if reply_msg:
        recipient_id = reply_msg.from_user.id
        if recipient_id == 7266772626:
            await message.reply('❌ Вы не можете передать средства боту')
            return
        cursor.execute('SELECT * FROM users WHERE id = ?', (recipient_id,))
        recipient = cursor.fetchone()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        sender = cursor.fetchone()
        if recipient and sender:
            sender_drug_count = sender[1]
            if value <= 0:
                await message.reply('❌ Значение должно быть положительным и больше нуля')
            elif sender_drug_count >= value:
                commission = round(value * 0.10)
                net_value = value - commission
                cursor.execute('SELECT drug_count FROM users WHERE id = ?', (7266772626,))
                bot_balance_row = cursor.fetchone()
                bot_balance = bot_balance_row[0] if bot_balance_row else 0
                cursor.execute('UPDATE users SET drug_count = drug_count + ? WHERE id = ?', (net_value, recipient_id))
                cursor.execute('UPDATE users SET drug_count = drug_count - ? WHERE id = ?', (value, user_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (bot_balance + commission, 7266772626))
                conn.commit()
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#GIVE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{recipient_id}</code>\nvalue: <code>{net_value}</code>\nCommission: <code>{commission}</code>\n\n<a href='tg://user?id={recipient_id}'>mention</a>",parse_mode='HTML')
                recipient_username = reply_msg.from_user.username
                if recipient_username:
                    await message.reply(
                        f"✅ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) _подарил(-а) {value} гр. мефа_ [{reply_msg.from_user.first_name}](tg://user?id={recipient_id})!\nКомиссия: `{commission}` гр. мефа\nПолучено `{net_value}` гр. мефа.",
                        parse_mode='markdown'
                    )
                else:
                    await message.reply(
                        f"✅ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) _подарил(-а) {value} гр. мефа_ [{reply_msg.from_user.first_name}](tg://user?id={recipient_id})!\nКомиссия: `{commission}` гр. мефа\nПолучено `{net_value}` гр. мефа.",
                        parse_mode='markdown'
                    )
            else:
                await message.reply('❌ Недостаточно граммов мефа для передачи')
        else:
            await message.reply('❌ Пользователь не найден')
    else:
        await message.reply('❌ Ответьте на сообщение, чтобы передать средства')

@router.message(Command('find'))
async def drug_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    drug_count = user[1] if user else 0
    last_used = user[6] if user else '2021-02-14 16:04:04.465506'
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if last_used is not None and (datetime.now() - datetime.fromisoformat(last_used)).total_seconds() < 43200:
            await message.reply('⏳ Ты недавно *ходил за кладом, подожди 12 часов.*', parse_mode='markdown')
            return
        else:
            if random.randint(1,100) > 50:
                count = random.randint(1, 10)
                if user:
                    cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count + count, user_id))
                else:
                    cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned, clan_member, clan_invite) VALUES (?, ?, ?, ?, ?, ?)', (user_id, count, 0, 0, 0, 0))
                cursor.execute('UPDATE users SET last_use_time = ? WHERE id = ?', ('2006-02-20 12:45:37.666666', user_id,))
                cursor.execute('UPDATE users SET last_find = ? WHERE id = ?', (datetime.now().isoformat(), user_id,))
                conn.commit()
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#FIND #WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\ncount: <code>{count}</code>\ndrug_count: <code>{drug_count + count}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>",parse_mode='HTML')
                await message.reply(f"👍 {message.from_user.first_name}, ты пошёл в лес и *нашел клад*, там лежало `{count} гр.` мефчика!\n🌿 Твое время команды /drug обновлено", parse_mode='markdown')
            elif random.randint(1,100) <= 50:
                count = random.randint(1, round(drug_count))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count - count, user_id,))
                conn.commit()
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#FIND #LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\ncount: <code>{count}</code>\ndrug_count: <code>{drug_count - count}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>",parse_mode='HTML')
                await message.reply(f"❌ *{message.from_user.first_name}*, тебя *спалил мент* и *дал тебе по ебалу*\n🌿 Тебе нужно откупиться, мент предложил взятку в размере `{count} гр.`\n⏳ Следующая попытка доступна через *12 часов.*", parse_mode='markdown')
                
@router.message(Command('top'))
async def top_command(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        cursor.execute('SELECT id, drug_count FROM users ORDER BY drug_count DESC LIMIT 10')
        top_users = cursor.fetchall()
        if top_users:
            response = "🔝ТОП 10 ЛЮТЫХ МЕФЕДРОНЩИКОВ В МИРЕ🔝:\n"
            counter = 1
            for user in top_users:
                user_id = user[0]
                if user_id == 7266772626:
                    continue
                drug_count = user[1]
                user_info = await bot.get_chat(user_id)
                response += f"{counter}) *{user_info.full_name}*: `{drug_count} гр. мефа`\n"
                counter += 1
            await message.reply(response, parse_mode='markdown')
        else:
            await message.reply('Никто еще не принимал меф.')

@router.message(Command('take'))
async def take_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        await message.reply('❌ Ваша информация не найдена в базе данных.')
        return    
    is_banned = user[4]    
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
        return    
    reply_msg = message.reply_to_message    
    if reply_msg:
        if reply_msg.from_user.id == 7266772626:
            await message.reply(f'❌ Вы не можете забрать меф у бота')
            return
        if reply_msg.from_user.id != message.from_user.id:
            victim_id = reply_msg.from_user.id
            your_id = message.from_user.id
            cursor.execute('SELECT * FROM users WHERE id = ?', (victim_id,))
            victim = cursor.fetchone()            
            cursor.execute('SELECT * FROM users WHERE id = ?', (your_id,))
            your_user = cursor.fetchone()            
            if not victim or not your_user:
                await message.reply('❌ Не удалось найти данные пользователя. Попробуйте еще раз.')
                return            
            victim_drug_count = victim[1]
            your_drug_count = your_user[1]
            if victim_drug_count > 1 and your_drug_count > 1:
                last_time_data = await state.get_data()
                last_time = last_time_data.get('time') if last_time_data else None
                
                if last_time and (datetime.now() - last_time) < timedelta(days=1):
                    await message.reply("❌ Нельзя пиздить меф так часто! Ты сможешь спиздить меф через 1 день.")
                    return
                variables = ['noticed', 'hit', 'pass']
                randomed = random.choice(variables)                
                if randomed == 'noticed':
                    cursor.execute('UPDATE users SET drug_count = drug_count - 1 WHERE id = ?', (your_id,))
                    conn.commit()
                    await message.reply('❌ *Жертва тебя заметила*, и ты решил убежать. Спиздить меф не получилось. Пока ты бежал, *ты потерял* `1 гр.`', parse_mode='markdown')                    
                elif randomed == 'hit':
                    cursor.execute('UPDATE users SET drug_count = drug_count - 1 WHERE id = ?', (your_id,))
                    conn.commit()
                    await message.reply('❌ *Жертва тебя заметила*, и пизданула тебя бутылкой по башке бля. Спиздить меф не получилось. *Жертва достала из твоего кармана* `1 гр.`', parse_mode='markdown')  
                elif randomed == 'pass':
                    cursor.execute('UPDATE users SET drug_count = drug_count - 1 WHERE id = ?', (victim_id,))
                    cursor.execute('UPDATE users SET drug_count = drug_count + 1 WHERE id = ?', (your_id,))
                    conn.commit()
                    if reply_msg.from_user.username:
                        username = reply_msg.from_user.username
                    else:
                        username = f'[{reply_msg.from_user.first_name}](tg://user?id={reply_msg.from_user.id})'     
                    await message.reply(f"✅ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) _спиздил(-а) один грам мефа у_ @{username}!", parse_mode='markdown')
                await state.set_data({'time': datetime.now()})
            else:
                await message.reply('❌ У вас или у жертвы недостаточно мефа.')
        else:
            await message.reply('❌ Вы не можете взаимодействовать с этим сообщением.')
    else:
        await message.reply('❌ Ответьте на сообщение, чтобы забрать меф.')
            
@router.message(Command('drug'))
async def drug_command(message: Message, state: FSMContext):
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
    elif is_banned == 0:
        if last_use_time and (datetime.now() - use_time) < timedelta(hours=1):
            remaining_time = timedelta(hours=1) - (datetime.now() - use_time)
            await message.reply(f"❌ *{message.from_user.first_name}*, _ты уже нюхал(-а)!_\n\n🌿 Всего снюхано `{drug_count} грамм` мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
        elif random.randint(0,100) < 20:
            if last_use_time and (datetime.now() - use_time) < timedelta(hours=1):
                remaining_time = timedelta(hours=1) - (datetime.now() - use_time)
                await message.reply(f"🧂 *{message.from_user.first_name}*, _ты просыпал(-а) весь мефчик!_\n\n🌿 Всего снюхано `{drug_count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
                cursor.execute('UPDATE users SET last_use_time = ? WHERE id = ?', (datetime.now(), user_id))
                conn.commit()
        else:
            count = random.randint(1, 10)
            if user:
                cursor.execute('UPDATE users SET drug_count = drug_count + ? WHERE id = ?', (count, user_id))
            else:
                cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned) VALUES (?, ?, 0, 0)', (user_id, count))
            cursor.execute('UPDATE users SET last_use_time = ? WHERE id = ?', (datetime.now(), user_id))
            conn.commit()
            await message.reply(f"👍 *{message.from_user.first_name}*, _ты занюхнул(-а) {count} грамм мефчика!_\n\n🌿 Всего снюхано `{drug_count+count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')

@router.message(Command('help'))
async def help_command(message: Message):
    await message.reply('''Все команды бота:

`/drug` - *принять мефик*
`/top` - *топ торчей мира*
`/take` - *спиздить мефик у ближнего*
`/give` - *поделиться мефиком*
`/casino` - *казино*
`/find` - *сходить за кладом*
`/about` - *узнать подробнее о боте*
`/clancreate` - *создать клан*
`/deposit` - *пополнить баланс клана*
`/withdraw` - *вывести средства с клана*
`/clantop` - *топ 10 кланов по состоянию баланса*
`/clanbalance` - *баланс клана*
`/claninfo` - *о клане*
`/claninvite` - *пригласить в клан*
`/clankick` - *кикнуть из клана*
`/clanaccept` - *принять приглашение в клан*
`/clandecline` - *отказаться от приглашения в клан*
`/clanleave` - *добровольно выйти из клана*
`/clandisband` - *распустить клан*
    ''', parse_mode='markdown')

@router.message(Command('grach'))
async def start_command(message: Message):
    await message.reply("грач хуесос")

@router.message(Command('rules'))
async def start_command(message: Message):
    await message.reply('''Правила пользования mephmetrbot:
*1) Мультиаккаунтинг - бан навсегда и обнуление всех аккаунтов *
*2) Использование любых уязвимостей бота - бан до исправления и возможное обнуление*
*3) Запрещена реклама через топ кланов и топ юзеров - выговор, после бан с обнулением*
*4) Запрещена продажа валюты между игроками - обнуление и бан*

*Бот не имеет никакого отношения к реальности. Все совпадения случайны. 
Создатели не пропагандируют наркотики и против их распространения и употребления. 
Употребление, хранение и продажа является уголовно наказуемой*
*Сообщить о багах вы можете администраторам* (*команда* `/about`)''', parse_mode='markdown')
    
@router.message(Command('start'))
async def start_command(message: Message):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='📢 Канал', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💰 Донат', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💬 Чат', url='https://t.me/mefmetrchat')
    )
    await message.reply("👋 *Здарова шныр*, этот бот сделан для того, чтобы *считать* сколько *грамм мефедрончика* ты снюхал\n🧑‍💻 Бот разработан *powerplantsmoke.t.me* и *hateandroid.t.me*", reply_markup=builder.as_markup(), parse_mode='markdown')


@router.message(Command('about'))
async def about_command(message: Message):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='📢 Канал', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💰 Донат', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💬 Чат', url='https://t.me/mefmetrchat')
    )
    await message.reply("🧑‍💻 Бот разработан powerplantsmoke.t.me и hateandroid.t.me", reply_markup=builder.as_markup())

