import random
import sqlite3
import sys
from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command, CommandObject
import os
from config import bot

router = Router()
conn = sqlite3.connect('handlers/mephmetrbot.db')
cursor = conn.cursor()

@router.message(Command('clancreate'))
async def create_clan(message: Message, command: CommandObject):
    args = command.args
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if args:
            args = command.args.split(' ', maxsplit=1)[0]
            clan_name = args
            cursor.execute('SELECT * FROM clans WHERE clan_name = ?', (clan_name,))
            clanexist = cursor.fetchone()
            if clanexist:
                await message.reply('🛑 Клан с таким названием уже существует')
            else:
                clan_id = random.randint(100000, 999999)
                user_id = message.from_user.id
                cursor.execute('SELECT clan_member, drug_count FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()
                drug_count = user[1]
                if user[0] is not None:
                    await message.reply(f"🛑 Вы уже состоите в клане.", parse_mode='markdown')
                else:
                    if drug_count >= 100:
                        cursor.execute('INSERT INTO clans (clan_id, clan_name, clan_owner_id, clan_balance) VALUES (?, ?, ?, ?)', (clan_id, clan_name, user_id, 0))
                        cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (clan_id, user_id))
                        cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count - 100, user_id))
                        conn.commit()
                        await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#NEWCLAN</b> clanid: <code>{clan_id}</code> clanname: <code>{clan_name}</code> clanownerid: <code>{user_id}</code>",parse_mode='HTML')

                        await message.reply(f"✅ Клан *{clan_name}* успешно создан.\nВаш идентификатор клана: `{clan_id}`\nС вашего баланса списано `100` гр.",parse_mode='markdown')
                    else:
                        await message.reply(f"🛑 Недостаточно средств.\nСтоимость создания клана: `100` гр.", parse_mode='markdown')
        else:
            await message.reply(f"🛑 Укажи название клана\nПример:\n`/clancreate КрУтЫе_ПеРцЫ`\nСтоимость создания клана: `100` гр.", parse_mode='markdown')

@router.message(Command('deposit'))
async def deposit(message: Message, command: CommandObject):
    args = command.args.split(' ', maxsplit=1)[0]
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if args:
            try:
                cost = int(args)
            except ValueError:
                await message.reply(f'❌ Введи целое число')
                return
            user_id = message.from_user.id
            cursor.execute('SELECT drug_count, clan_member FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            user_balance = int(user[0])
            clan_id = user[1]
            if clan_id == 0:
                await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
            elif clan_id > 0:
                cursor.execute('SELECT * FROM clans WHERE clan_id = ?', (clan_id,))
                clan = cursor.fetchone()
                clan_balance = clan[3]
                clan_name = clan[1]
                clan_owner_id = clan[2]
                if cost < 0:
                    await message.reply(f'❌ Значение не может быть отрицательным')
                    return
                elif cost == 0:
                    await message.reply(f'❌ Значение не может быть равным нулю')
                    return
                elif cost > user_balance:
                    await message.reply(f"🛑 Недостаточно средств. Ваш баланс: `{user_balance}` гр.", parse_mode='markdown')
                elif cost <= user_balance and cost != 0:
                    cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (user_balance - cost, user_id,))
                    conn.commit()
                    newbalance = clan_balance+cost
                    cursor.execute('UPDATE clans SET clan_balance = ? WHERE clan_owner_id = ?', (newbalance, clan_owner_id,))
                    conn.commit()
                    await message.reply(f"✅ Вы успешно пополнили баланс клана `{clan_name}` на `{cost}` гр.", parse_mode='markdown')
                    await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#DEPOSIT</b> <br>clanname: <code>{clan_name}</code> <br>amount: <code>{cost}</code> <br>userid: <code>{user_id}</code> <br>firstname: {message.from_user.first_name} <br><a href='tg://user?id={user_id}'>mention</a>",parse_mode='HTML')
        else:
            await message.reply(f"🛑 Вы не указали сумму. Пример:\n`/deposit 100`", parse_mode='markdown')

@router.message(Command('withdraw'))
async def withdraw(message: Message, command: CommandObject):
    args = command.args.split(' ', maxsplit=1)[0]
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if args:
            try:
                cost = int(args)
            except ValueError:
                await message.reply(f'❌ Введи целое число')
            user_id = message.from_user.id
            cursor.execute('SELECT drug_count, clan_member FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            user_balance = int(user[0])
            clan_id = user[1]
            if clan_id == 0:
                await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
            elif clan_id > 0:
                cursor.execute('SELECT * FROM clans WHERE clan_id = ?', (clan_id,))
                clan = cursor.fetchone()
                clan_balance = clan[3]
                clan_name = clan[1]
                clan_owner_id = clan[2]
                if user_id != clan_owner_id:
                    await message.reply(f"🛑 Снимать деньги со счёта клана может только его владелец.", parse_mode='markdown')
                else:
                    if cost < 0:
                        await message.reply(f'❌ Значение не может быть отрицательным')
                        return
                    elif cost == 0:
                        await message.reply(f'❌ Значение не может быть равным нулю')
                        return
                    elif cost > clan_balance:
                        await message.reply(f"🛑 Недостаточно средств. Баланс клана: `{clan_balance}` гр.", parse_mode='markdown')
                    elif cost <= clan_balance and cost != 0:
                        cursor.execute('UPDATE clans SET clan_balance = ? WHERE clan_owner_id = ?', (clan_balance - cost, user_id,))
                        cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (user_balance + cost, user_id,))
                        conn.commit()
                        await message.reply(f"✅ Вы успешно сняли `{cost}` гр. мефа с баланса клана `{clan_name}`", parse_mode='markdown')
                        await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#WITHDRAW</b><br>amount: <code>{cost}</code><br>clanname: <code>{clan_name}</code><br>userid: <code>{user_id}</code><br><a href='tg://user?id={user_id}'>mention</a>",parse_mode='HTML')
        else:
            await message.reply(f"🛑 Вы не указали сумму. Пример:\n`/withdraw 100`", parse_mode='markdown')


@router.message(Command('clantop'))
async def clan_top(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        cursor.execute('SELECT clan_name, clan_balance FROM clans ORDER BY clan_balance DESC LIMIT 10')
        top_clans = cursor.fetchall()
        if top_clans:
            response = "🔝ТОП 10 МЕФЕДРОНОВЫХ КАРТЕЛЕЙ В МИРЕ🔝:\n"
            counter = 1
            for clan in top_clans:
                clan_name = clan[0]
                clan_balance = clan[1]
                response += f"{counter}) *{clan_name}*  `{clan_balance} гр. мефа`\n"
                counter += 1
            await message.reply(response, parse_mode='markdown')
        else:
            await message.reply('🛑 Ещё ни один клан не пополнил свой баланс.')

@router.message(Command('clanbalance'))
async def clanbalance(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
             await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0:
            clan_balance = clan[0]
            clan_name = clan[1]
            await message.reply(f'✅ Баланс клана *{clan_name}* - `{clan_balance}` гр.', parse_mode='markdown')

@router.message(Command('clanwar'))
async def clanwar(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 *Вы не состоите в клане*", parse_mode='markdown')
        elif clan_id > 0:
            cursor.execute('SELECT clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
            clan = cursor.fetchone()
            clan_name = clan[0]
            clan_owner_id = clan[1]
            if user_id != clan_owner_id:
                await message.reply(f"🛑 *Вы не являетесь владельцем клана*", parse_mode='markdown')
                return
            if len(message.text.split()) < 2:
                await message.reply(f"🛑 *Вы не указали идентификатор клана для начала войны*", parse_mode='markdown')
                return
            target_clan_id = message.text.split()[1]
            cursor.execute('SELECT clan_name FROM clans WHERE clan_id = ?', (target_clan_id,))
            target_clan = cursor.fetchone()
            if not target_clan:
                await message.reply(f"🛑 *Не удалось найти клан с указанным идентификатором*", parse_mode='markdown')
                return
            target_clan_name = target_clan[0]
            await message.reply(f"*Клан {clan_name} начал войну с {target_clan_name}!*", parse_mode='markdown')
            
            cursor.execute('SELECT chat_id FROM chats')
            chats = cursor.fetchall()
            for chat_id in chats:
                try:
                    await bot.send_message(chat_id[0], f"*Клан {clan_name} начал войну с {target_clan_name}!*", parse_mode='markdown')
                except Exception as e:
                    print(f"Ошибка отправки сообщения в {chat_id}: {e}")

@router.message(Command('clanowner'))
async def clan_owner(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 *Вы не состоите в клане*", parse_mode='markdown')
        elif clan_id > 0:
            cursor.execute('SELECT clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
            current_owner_id = cursor.fetchone()[0]
            if user_id != current_owner_id:
                await message.reply(f"🛑 *Вы не являетесь владельцем клана*", parse_mode='markdown')
                return

            if message.reply_to_message:
                new_owner_id = message.reply_to_message.from_user.id
            elif len(message.text.split()) >= 2:
                new_owner_id = int(message.text.split()[1])
            else:
                await message.reply(f"🛑 *Вы не указали нового владельца клана*", parse_mode='markdown')
                return
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (new_owner_id,))
            new_owner = cursor.fetchone()
            if not new_owner:
                await message.reply(f"🛑 *Не удалось найти пользователя с указанным идентификатором*", parse_mode='markdown')
                return
            cursor.execute('UPDATE clans SET clan_owner_id = ? WHERE clan_id = ?', (new_owner_id, clan_id))
            conn.commit()
            await message.reply(f"✅ *Вы передали владельца клана!*", parse_mode='markdown')


@router.message(Command('claninfo'))
async def claninfo(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
             await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0:
            clan_balance = clan[0]
            clan_name = clan[1]
            clan_owner_id = clan[2]
            clan_owner = await bot.get_chat(clan_owner_id)
            await message.reply(f"👥 Клан: `{clan_name}`\n👑 Владелец клана: [{clan_owner.first_name}](tg://user?id={clan_owner_id})\n🌿 Баланс клана `{clan_balance}` гр.", parse_mode='markdown')   

@router.message(Command('clanmembers'))
async def clanmembers(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0

    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        clan_id = user[7] if user else 0
        cursor.execute('SELECT * FROM users WHERE clan_member = ?', (clan_id,))
        clan_members = cursor.fetchall()
        cursor.execute('SELECT clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
        clan = cursor.fetchone()
        if clan:
            clan_name = clan[0]
            clan_owner_id = clan[1]
            if clan_id > 0:
                if clan_members:
                    response = f"👥 Список участников клана *{clan_name}*:\n"
                    counter = 1
                    clan_owner = None
                    for member in clan_members:
                        if member[0] == clan_owner_id:
                            clan_owner = member
                            break
                    if clan_owner:
                        user_info = await bot.get_chat(clan_owner[0])
                        response += f"{counter}) *{user_info.full_name}* 👑\n"
                        counter += 1
                    for member in clan_members:
                        if member[0] != clan_owner_id:
                            user_info = await bot.get_chat(member[0])
                            response += f"{counter}) {user_info.full_name}\n"
                            counter += 1
                    await message.reply(response, parse_mode='markdown')
        else:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')

@router.message(Command('claninvite'))
async def claninvite(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan:
            clan_name = clan[1]
            clan_owner_id = clan[2]
            if user_id == clan_owner_id:
                reply_msg = message.reply_to_message
                if reply_msg and reply_msg.from_user.id == 7266772626:
                    await message.reply(f'❌ Вы не можете пригласить бота в клан')
                    return
                elif reply_msg:
                    user_id = reply_msg.from_user.id
                    cursor.execute('SELECT clan_member, clan_invite FROM users WHERE id = ?', (user_id,))
                    user = cursor.fetchone()
                    clan_member = user[0]
                    clan_invite = user[1]
                    try:
                        cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned, clan_member, clan_invite) VALUES (?, 0, 0, 0, 0, 0)', (user_id,))
                        conn.commit()
                        cursor.execute('SELECT clan_member, clan_invite FROM users WHERE id = ?', (user_id,))
                        user = cursor.fetchone()
                        clan_member = user[0]
                        clan_invite = user[1]
                    except:
                        pass
     
                    if clan_member == 0 and clan_invite == 0:
                        if user:
                            cursor.execute('UPDATE users SET clan_invite = ? WHERE id = ?', (clan_id, user_id))
                        else:
                            cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned, clan_member, clan_invite) VALUES (?, 0, 0, 0, 0, ?)', (user_id, clan_id))
                        conn.commit()
                        await message.reply(f'✅ Пользователь {reply_msg.from_user.first_name} *приглашён в клан {clan_name}* пользователем {message.from_user.first_name}\nДля того чтобы принять приглашение, *введите команду* `/clanaccept`\nДля того чтобы отказаться от приглашения, *введите команду* `/clandecline`', parse_mode='markdown')
                    
                         
                    elif clan_member is None and clan_invite is None:
                        if user:
                            cursor.execute('UPDATE users SET clan_invite = ? WHERE id = ?', (clan_id, user_id))
                        else:
                            cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned, clan_member, clan_invite) VALUES (?, 0, 0, 0, 0, ?)', (user_id, clan_id))
                        conn.commit()
                        await message.reply(f'✅ Пользователь {reply_msg.from_user.first_name} *приглашён в клан {clan_name}* пользователем {message.from_user.first_name}\nДля того чтобы принять приглашение, *введите команду* `/clanaccept`\nДля того чтобы отказаться от приглашения, *введите команду* `/clandecline`', parse_mode='markdown')
                    
                    
                    elif clan_invite > 0:
                        await message.reply(f"🛑 Этот пользователь уже имеет активное приглашение", parse_mode='markdown')
                    elif clan_member > 0:
                        await message.reply(f"🛑 Этот пользователь уже в клане", parse_mode='markdown')
            elif user_id != clan_owner_id:
                await message.reply(f"🛑 Приглашать в клан может только создатель", parse_mode='markdown')
        else:
            await message.reply(f"🛑 {sys.exc_info()[0]}")

@router.message(Command('clankick'))
async def clankick(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    clan_name = clan[1]
    clan_owner_id = int(clan[2])
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0 and user_id == clan_owner_id:
            reply_msg = message.reply_to_message
            if reply_msg:
                user_id = reply_msg.from_user.id
                username = reply_msg.from_user.username
                usernameinviter = message.from_user.username.replace('_', '\n')
                cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (0, user_id))
                conn.commit()
                await message.reply(f'✅ Пользователь @{username} *исключен из клана {clan_name}* пользователем @{usernameinviter}', parse_mode='markdown')
        elif clan_id > 0 and user_id != clan_owner_id:
            await message.reply(f"🛑 Исключать из клана может только создатель", parse_mode='markdown')

@router.message(Command('clanleave'))
async def clanleave(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    clan_name = clan[1]
    clan_owner_id = int(clan[2])
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0 and user_id != clan_owner_id:
            cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (0, user_id))
            conn.commit()
            await message.reply(f'✅ *Вы покинули* клан *{clan_name}*', parse_mode='markdown')
        elif clan_id > 0 and user_id == clan_owner_id:
            await message.reply(f"🛑 Создатель клана не может его покинуть", parse_mode='markdown')

@router.message(Command('clandisband'))
async def clandisband(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_owner_id, clan_name FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()

    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        try:
            clan_owner_id = clan[0]
            clan_name = clan[1]
        except:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        if clan_id > 0 and user_id == clan_owner_id:
            cursor.execute('DELETE FROM clans WHERE clan_id = ?', (clan_id,))
            cursor.execute('UPDATE users SET clan_member = 0 WHERE clan_member = ?', (clan_id,))
            cursor.execute('UPDATE users SET clan_invite = 0 WHERE clan_invite = ?', (clan_id,))
            conn.commit()
            await message.reply(f'✅ Вы распустили клан `{clan_name}`', parse_mode='markdown')
        elif clan_id > 0 and user_id != clan_owner_id:
            await message.reply(f"🛑 Вы не владелец клана!", parse_mode='markdown')

@router.message(Command('clanaccept'))
async def clanaccept(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_invite = user[8] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_invite:
            if clan_invite != 0:
                cursor.execute('SELECT clan_name FROM clans WHERE clan_id = ?', (clan_invite,))
                clan = cursor.fetchone()
                clan_name = clan[0]
                cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (clan_invite, user_id))
                cursor.execute('UPDATE users SET clan_invite = 0 WHERE id = ?', (user_id,))
                conn.commit()
                await message.reply(f'✅ *Вы приняли* приглашение в клан *{clan_name}*', parse_mode='markdown')
        else:
            await message.reply('🛑 Вы ещё не получали приглашений в клан')
        
@router.message(Command('clandecline'))
async def clandecline(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_invite = user[8] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_invite:
            if clan_invite != 0:
                cursor.execute('SELECT clan_name FROM clans WHERE clan_id = ?', (clan_invite,))
                clan = cursor.fetchone()
                clan_name = clan[0]
                cursor.execute('UPDATE users SET clan_invite = 0 WHERE id = ?', (user_id,))
                conn.commit()
                await message.reply(f'❌ *Вы отклонили* приглашение в клан *{clan_name}*', parse_mode='markdown')
        else:
            await message.reply('🛑 Вы ещё не получали приглашений в клан')
        
@router.message(Command('clancreate'))
async def create_clan(message: Message, command: CommandObject):
    args = command.args
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if args:
            args = command.args.split(' ', maxsplit=1)[0]
            clan_name = args
            cursor.execute('SELECT * FROM clans WHERE clan_name = ?', (clan_name,))
            clanexist = cursor.fetchone()
            if clanexist:
                await message.reply('🛑 Клан с таким названием уже существует')
            else:
                clan_id = random.randint(100000, 999999)
                user_id = message.from_user.id
                cursor.execute('SELECT clan_member, drug_count FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()
                drug_count = user[1]
                if user[0] is not None:
                    await message.reply(f"🛑 Вы уже состоите в клане.", parse_mode='markdown')
                else:
                    if drug_count >= 100:
                        cursor.execute('INSERT INTO clans (clan_id, clan_name, clan_owner_id, clan_balance) VALUES (?, ?, ?, ?)', (clan_id, clan_name, user_id, 0))
                        cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (clan_id, user_id))
                        cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (drug_count - 100, user_id))
                        conn.commit()
                        await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#NEWCLAN</b><br>clanid: <code>{clan_id}</code><br>clanname: <code>{clan_name}</code><br>clanownerid: <code>{user_id}</code>",parse_mode='HTML')
                        await message.reply(f"✅ Клан *{clan_name}* успешно создан.\nВаш идентификатор клана: `{clan_id}`\nС вашего баланса списано `100` гр.",parse_mode='markdown')
                    else:
                        await message.reply(f"🛑 Недостаточно средств.\nСтоимость создания клана: `100` гр.", parse_mode='markdown')
        else:
            await message.reply(f"🛑 Укажи название клана\nПример:\n`/clancreate КрУтЫе_ПеРцЫ`\nСтоимость создания клана: `100` гр.", parse_mode='markdown')

@router.message(Command('deposit'))
async def deposit(message: Message, command: CommandObject):
    args = command.args.split(' ', maxsplit=1)[0]
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if args:
            try:
                cost = int(args)
            except ValueError:
                await message.reply(f'❌ Введи целое число')
                return
            user_id = message.from_user.id
            cursor.execute('SELECT drug_count, clan_member FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            user_balance = int(user[0])
            clan_id = user[1]
            if clan_id == 0:
                await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
            elif clan_id > 0:
                cursor.execute('SELECT * FROM clans WHERE clan_id = ?', (clan_id,))
                clan = cursor.fetchone()
                clan_balance = clan[3]
                clan_name = clan[1]
                clan_owner_id = clan[2]
                if cost < 0:
                    await message.reply(f'❌ Значение не может быть отрицательным')
                    return
                elif cost == 0:
                    await message.reply(f'❌ Значение не может быть равным нулю')
                    return
                elif cost > user_balance:
                    await message.reply(f"🛑 Недостаточно средств. Ваш баланс: `{user_balance}` гр.", parse_mode='markdown')
                elif cost <= user_balance and cost != 0:
                    cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (user_balance - cost, user_id,))
                    conn.commit()
                    newbalance = clan_balance+cost
                    cursor.execute('UPDATE clans SET clan_balance = ? WHERE clan_owner_id = ?', (newbalance, clan_owner_id,))
                    conn.commit()
                    await message.reply(f"✅ Вы успешно пополнили баланс клана `{clan_name}` на `{cost}` гр.", parse_mode='markdown')
                    await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#DEPOSIT</b><br>clanname: <code>{clan_name}</code><br>amount: <code>{cost}</code><br>userid: <code>{user_id}</code><br>firstname: {message.from_user.first_name}<br><a href='tg://user?id={user_id}'>mention</a>",parse_mode='HTML')
        else:
            await message.reply(f"🛑 Вы не указали сумму. Пример:\n`/deposit 100`", parse_mode='markdown')

@router.message(Command('withdraw'))
async def withdraw(message: Message, command: CommandObject):
    args = command.args.split(' ', maxsplit=1)[0]
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if args:
            try:
                cost = int(args)
            except ValueError:
                await message.reply(f'❌ Введи целое число')
            user_id = message.from_user.id
            cursor.execute('SELECT drug_count, clan_member FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            user_balance = int(user[0])
            clan_id = user[1]
            if clan_id == 0:
                await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
            elif clan_id > 0:
                cursor.execute('SELECT * FROM clans WHERE clan_id = ?', (clan_id,))
                clan = cursor.fetchone()
                clan_balance = clan[3]
                clan_name = clan[1]
                clan_owner_id = clan[2]
                if user_id != clan_owner_id:
                    await message.reply(f"🛑 Снимать деньги со счёта клана может только его владелец.", parse_mode='markdown')
                else:
                    if cost < 0:
                        await message.reply(f'❌ Значение не может быть отрицательным')
                        return
                    elif cost == 0:
                        await message.reply(f'❌ Значение не может быть равным нулю')
                        return
                    elif cost > clan_balance:
                        await message.reply(f"🛑 Недостаточно средств. Баланс клана: `{clan_balance}` гр.", parse_mode='markdown')
                    elif cost <= clan_balance and cost != 0:
                        cursor.execute('UPDATE clans SET clan_balance = ? WHERE clan_owner_id = ?', (clan_balance - cost, user_id,))
                        cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (user_balance + cost, user_id,))
                        conn.commit()
                        await message.reply(f"✅ Вы успешно сняли `{cost}` гр. мефа с баланса клана `{clan_name}`", parse_mode='markdown')
                        await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#WITHDRAW</b><br>amount: <code>{cost}</code><br>clanname: <code>{clan_name}</code><br>userid: <code>{user_id}</code><br><a href='tg://user?id={user_id}'>mention</a>",parse_mode='HTML')
        else:
            await message.reply(f"🛑 Вы не указали сумму. Пример:\n`/withdraw 100`", parse_mode='markdown')


@router.message(Command('clantop'))
async def clan_top(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        cursor.execute('SELECT clan_name, clan_balance FROM clans ORDER BY clan_balance DESC LIMIT 10')
        top_clans = cursor.fetchall()
        if top_clans:
            response = "🔝ТОП 10 МЕФЕДРОНОВЫХ КАРТЕЛЕЙ В МИРЕ🔝:\n"
            counter = 1
            for clan in top_clans:
                clan_name = clan[0]
                clan_balance = clan[1]
                response += f"{counter}) *{clan_name}*  `{clan_balance} гр. мефа`\n"
                counter += 1
            await message.reply(response, parse_mode='markdown')
        else:
            await message.reply('🛑 Ещё ни один клан не пополнил свой баланс.')

@router.message(Command('clanbalance'))
async def clanbalance(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
             await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0:
            clan_balance = clan[0]
            clan_name = clan[1]
            await message.reply(f'✅ Баланс клана *{clan_name}* - `{clan_balance}` гр.', parse_mode='markdown')

@router.message(Command('clanwar'))
async def clanwar(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 *Вы не состоите в клане*", parse_mode='markdown')
        elif clan_id > 0:
            cursor.execute('SELECT clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
            clan = cursor.fetchone()
            clan_name = clan[0]
            clan_owner_id = clan[1]
            if user_id != clan_owner_id:
                await message.reply(f"🛑 *Вы не являетесь владельцем клана*", parse_mode='markdown')
                return
            if len(message.text.split()) < 2:
                await message.reply(f"🛑 *Вы не указали идентификатор клана для начала войны*", parse_mode='markdown')
                return
            target_clan_id = message.text.split()[1]
            cursor.execute('SELECT clan_name FROM clans WHERE clan_id = ?', (target_clan_id,))
            target_clan = cursor.fetchone()
            if not target_clan:
                await message.reply(f"🛑 *Не удалось найти клан с указанным идентификатором*", parse_mode='markdown')
                return
            target_clan_name = target_clan[0]
            await message.reply(f"*Клан {clan_name} начал войну с {target_clan_name}!*", parse_mode='markdown')
            
            cursor.execute('SELECT chat_id FROM chats')
            chats = cursor.fetchall()
            for chat_id in chats:
                try:
                    await bot.send_message(chat_id[0], f"*Клан {clan_name} начал войну с {target_clan_name}!*", parse_mode='markdown')
                except Exception as e:
                    print(f"Ошибка отправки сообщения в {chat_id}: {e}")

@router.message(Command('clanowner'))
async def clan_owner(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 *Вы не состоите в клане*", parse_mode='markdown')
        elif clan_id > 0:
            cursor.execute('SELECT clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
            current_owner_id = cursor.fetchone()[0]
            if user_id != current_owner_id:
                await message.reply(f"🛑 *Вы не являетесь владельцем клана*", parse_mode='markdown')
                return

            if message.reply_to_message:
                new_owner_id = message.reply_to_message.from_user.id
            elif len(message.text.split()) >= 2:
                new_owner_id = int(message.text.split()[1])
            else:
                await message.reply(f"🛑 *Вы не указали нового владельца клана*", parse_mode='markdown')
                return
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (new_owner_id,))
            new_owner = cursor.fetchone()
            if not new_owner:
                await message.reply(f"🛑 *Не удалось найти пользователя с указанным идентификатором*", parse_mode='markdown')
                return
            cursor.execute('UPDATE clans SET clan_owner_id = ? WHERE clan_id = ?', (new_owner_id, clan_id))
            conn.commit()
            await message.reply(f"✅ *Вы передали владельца клана!*", parse_mode='markdown')


@router.message(Command('claninfo'))
async def claninfo(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
             await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0:
            clan_balance = clan[0]
            clan_name = clan[1]
            clan_owner_id = clan[2]
            clan_owner = await bot.get_chat(clan_owner_id)
            await message.reply(f"👥 Клан: `{clan_name}`\n👑 Владелец клана: [{clan_owner.first_name}](tg://user?id={clan_owner_id})\n🌿 Баланс клана `{clan_balance}` гр.", parse_mode='markdown')   

@router.message(Command('clanmembers'))
async def clanmembers(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0

    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        clan_id = user[7] if user else 0
        cursor.execute('SELECT * FROM users WHERE clan_member = ?', (clan_id,))
        clan_members = cursor.fetchall()
        cursor.execute('SELECT clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
        clan = cursor.fetchone()
        if clan:
            clan_name = clan[0]
            clan_owner_id = clan[1]
            if clan_id > 0:
                if clan_members:
                    response = f"👥 Список участников клана *{clan_name}*:\n"
                    counter = 1
                    clan_owner = None
                    for member in clan_members:
                        if member[0] == clan_owner_id:
                            clan_owner = member
                            break
                    if clan_owner:
                        user_info = await bot.get_chat(clan_owner[0])
                        response += f"{counter}) *{user_info.full_name}* 👑\n"
                        counter += 1
                    for member in clan_members:
                        if member[0] != clan_owner_id:
                            user_info = await bot.get_chat(member[0])
                            response += f"{counter}) {user_info.full_name}\n"
                            counter += 1
                    await message.reply(response, parse_mode='markdown')
        else:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')

@router.message(Command('claninvite'))
async def claninvite(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan:
            clan_name = clan[1]
            clan_owner_id = clan[2]
            if user_id == clan_owner_id:
                reply_msg = message.reply_to_message
                if reply_msg and reply_msg.from_user.id == 7266772626:
                    await message.reply(f'❌ Вы не можете пригласить бота в клан')
                    return
                elif reply_msg:
                    user_id = reply_msg.from_user.id
                    cursor.execute('SELECT clan_member, clan_invite FROM users WHERE id = ?', (user_id,))
                    user = cursor.fetchone()
                    clan_member = user[0]
                    clan_invite = user[1]
                    try:
                        cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned, clan_member, clan_invite) VALUES (?, 0, 0, 0, 0, 0)', (user_id,))
                        conn.commit()
                        cursor.execute('SELECT clan_member, clan_invite FROM users WHERE id = ?', (user_id,))
                        user = cursor.fetchone()
                        clan_member = user[0]
                        clan_invite = user[1]
                    except:
                        pass
     
                    if clan_member == 0 and clan_invite == 0:
                        if user:
                            cursor.execute('UPDATE users SET clan_invite = ? WHERE id = ?', (clan_id, user_id))
                        else:
                            cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned, clan_member, clan_invite) VALUES (?, 0, 0, 0, 0, ?)', (user_id, clan_id))
                        conn.commit()
                        await message.reply(f'✅ Пользователь {reply_msg.from_user.first_name} *приглашён в клан {clan_name}* пользователем {message.from_user.first_name}\nДля того чтобы принять приглашение, *введите команду* `/clanaccept`\nДля того чтобы отказаться от приглашения, *введите команду* `/clandecline`', parse_mode='markdown')
                    
                         
                    elif clan_member is None and clan_invite is None:
                        if user:
                            cursor.execute('UPDATE users SET clan_invite = ? WHERE id = ?', (clan_id, user_id))
                        else:
                            cursor.execute('INSERT INTO users (id, drug_count, is_admin, is_banned, clan_member, clan_invite) VALUES (?, 0, 0, 0, 0, ?)', (user_id, clan_id))
                        conn.commit()
                        await message.reply(f'✅ Пользователь {reply_msg.from_user.first_name} *приглашён в клан {clan_name}* пользователем {message.from_user.first_name}\nДля того чтобы принять приглашение, *введите команду* `/clanaccept`\nДля того чтобы отказаться от приглашения, *введите команду* `/clandecline`', parse_mode='markdown')
                    
                    
                    elif clan_invite > 0:
                        await message.reply(f"🛑 Этот пользователь уже имеет активное приглашение", parse_mode='markdown')
                    elif clan_member > 0:
                        await message.reply(f"🛑 Этот пользователь уже в клане", parse_mode='markdown')
            elif user_id != clan_owner_id:
                await message.reply(f"🛑 Приглашать в клан может только создатель", parse_mode='markdown')
        else:
            await message.reply(f"🛑 {sys.exc_info()[0]}")

@router.message(Command('clankick'))
async def clankick(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    clan_name = clan[1]
    clan_owner_id = int(clan[2])
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0 and user_id == clan_owner_id:
            reply_msg = message.reply_to_message
            if reply_msg:
                user_id = reply_msg.from_user.id
                username = reply_msg.from_user.username
                usernameinviter = message.from_user.username.replace('_', '\n')
                cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (0, user_id))
                conn.commit()
                await message.reply(f'✅ Пользователь @{username} *исключен из клана {clan_name}* пользователем @{usernameinviter}', parse_mode='markdown')
        elif clan_id > 0 and user_id != clan_owner_id:
            await message.reply(f"🛑 Исключать из клана может только создатель", parse_mode='markdown')

@router.message(Command('clanleave'))
async def clanleave(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_balance, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()
    clan_name = clan[1]
    clan_owner_id = int(clan[2])
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_id == 0:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        elif clan_id > 0 and user_id != clan_owner_id:
            cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (0, user_id))
            conn.commit()
            await message.reply(f'✅ *Вы покинули* клан *{clan_name}*', parse_mode='markdown')
        elif clan_id > 0 and user_id == clan_owner_id:
            await message.reply(f"🛑 Создатель клана не может его покинуть", parse_mode='markdown')

@router.message(Command('clandisband'))
async def clandisband(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_id = user[7] if user else 0
    cursor.execute('SELECT clan_owner_id, clan_name FROM clans WHERE clan_id = ?', (clan_id,))
    clan = cursor.fetchone()

    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        try:
            clan_owner_id = clan[0]
            clan_name = clan[1]
        except:
            await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
        if clan_id > 0 and user_id == clan_owner_id:
            cursor.execute('DELETE FROM clans WHERE clan_id = ?', (clan_id,))
            cursor.execute('UPDATE users SET clan_member = 0 WHERE clan_member = ?', (clan_id,))
            cursor.execute('UPDATE users SET clan_invite = 0 WHERE clan_invite = ?', (clan_id,))
            conn.commit()
            await message.reply(f'✅ Вы распустили клан `{clan_name}`', parse_mode='markdown')
        elif clan_id > 0 and user_id != clan_owner_id:
            await message.reply(f"🛑 Вы не владелец клана!", parse_mode='markdown')

@router.message(Command('clanaccept'))
async def clanaccept(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_invite = user[8] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_invite:
            if clan_invite != 0:
                cursor.execute('SELECT clan_name FROM clans WHERE clan_id = ?', (clan_invite,))
                clan = cursor.fetchone()
                clan_name = clan[0]
                cursor.execute('UPDATE users SET clan_member = ? WHERE id = ?', (clan_invite, user_id))
                cursor.execute('UPDATE users SET clan_invite = 0 WHERE id = ?', (user_id,))
                conn.commit()
                await message.reply(f'✅ *Вы приняли* приглашение в клан *{clan_name}*', parse_mode='markdown')
        else:
            await message.reply('🛑 Вы ещё не получали приглашений в клан')
        
@router.message(Command('clandecline'))
async def clandecline(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_banned = user[4] if user else 0
    clan_invite = user[8] if user else 0
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
    elif is_banned == 0:
        if clan_invite:
            if clan_invite != 0:
                cursor.execute('SELECT clan_name FROM clans WHERE clan_id = ?', (clan_invite,))
                clan = cursor.fetchone()
                clan_name = clan[0]
                cursor.execute('UPDATE users SET clan_invite = 0 WHERE id = ?', (user_id,))
                conn.commit()
                await message.reply(f'❌ *Вы отклонили* приглашение в клан *{clan_name}*', parse_mode='markdown')
        else:
            await message.reply('🛑 Вы ещё не получали приглашений в клан')
        
