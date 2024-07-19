from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command, CommandObject
import sqlite3
from datetime import datetime
import asyncio
from config import bot
import os

router = Router()
conn = sqlite3.connect('handlers/mephmetrbot.db')
cursor = conn.cursor()

@router.message(Command('casino'))
async def casino(message: Message, command: CommandObject):
    args = command.args
    user_id = message.from_user.id
    bot_id = '7266772626'
    bot_id2 = '7005935644'

    cursor.execute('SELECT drug_count FROM users WHERE id = 7266772626')
    cursor.execute('SELECT drug_count FROM users WHERE id = 7005935644')
    bot_balance = cursor.fetchone()[0]
    
    if not args:
        await message.reply("🛑 Укажи ставку и условие! Пример:\n`/casino 100 чет`", parse_mode='markdown')
        return
    parts = args.split()
    try:
        bet = int(parts[0])
    except ValueError:
        await message.reply("🛑 Ставка должна быть целым числом!", parse_mode='markdown')
        return
    if bet < 10:
        await message.reply("🛑 Ставка должна быть больше `10` гр.", parse_mode='markdown')
        return
    
    condition = parts[1]
    valid_conditions = ['чет', 'нечет', 'меньше', 'больше', 'четное', 'нечетное'] + [str(i) for i in range(1, 7)]
    if condition not in valid_conditions:
        await message.reply("🛑 Неправильное условие! *Условия: `чет`, `нечет`, `меньше`, `больше`, `нечетное`, `четное` или число от `1` до `6`.*", parse_mode='markdown')
        return
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if user is None:
        await message.reply('🛑 Профиль не найден', parse_mode='markdown')
        return
    drug_count = user[1]
    last_used = user[5]
    is_banned = user[4]
    if is_banned == 1:
        await message.reply('🛑 Вы заблокированы в боте!')
        return
    if bet > drug_count:
        await message.reply("🛑 Твоя ставка больше твоего баланса!", parse_mode='markdown')
        return
    if bot_balance <= bet:
        await message.reply("🛑 У бота недостаточно средств для проведения игры. Попробуй позже.", parse_mode='markdown')
        return
    if last_used is not None and (datetime.now() - datetime.fromisoformat(last_used)).total_seconds() < 10:
        await message.reply('⏳ Ты только что *крутил казик*, солевая обезьяна, *подожди 10 секунд по братски.*', parse_mode='markdown')
        return
    
    
    dice_message = await message.answer_dice(emoji='🎲')
    await asyncio.sleep(3)
    dice_result = dice_message.dice.value
    outcome_message = f"🎲 Выпало: `{dice_result}`. "

    if condition == 'чет' or condition == 'четное':
        if dice_result % 2 == 0:
            win_amount = round(bet * 1.5, 1)
            if win_amount > bot_balance:
                await message.reply("🛑 Бот не может выплатить выигрыш. Попробуй позже.", parse_mode='markdown')
            else:
                new_balance = round(drug_count + win_amount, 1)
                new_bot_balance = round(bot_balance - win_amount, 1)
                outcome_message += f'🎉 Поздравляем, вы выиграли `{win_amount}` гр. Ваш новый баланс: `{new_balance}` гр.'
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
            await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
    elif condition == 'нечет' or condition == 'нечетное':
        if dice_result % 2 != 0:
            win_amount = round(bet * 1.5, 1)
            if win_amount > bot_balance:
                await message.reply("🛑 Бот не может выплатить выигрыш. Попробуй позже.", parse_mode='markdown')
            else:
                new_balance = round(drug_count + win_amount, 1)
                new_bot_balance = round(bot_balance - win_amount, 1)
                outcome_message += f'🎉 Поздравляем, вы выиграли `{win_amount}` гр. Ваш новый баланс: `{new_balance}` гр.'
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
            await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
    elif condition == 'меньше':
        if dice_result <= 3:
            win_amount = round(bet * 1.5, 1)
            if win_amount > bot_balance:
                await message.reply("🛑 Бот не может выплатить выигрыш. Попробуй позже.", parse_mode='markdown')
            else:
                new_bot_balance = round(bot_balance - win_amount, 1)
                new_balance = round(drug_count + win_amount, 1)
                outcome_message += f'🎉 Поздравляем, вы выиграли `{win_amount}` гр. Ваш новый баланс: `{new_balance}` гр.'
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
            await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
    elif condition == 'больше':
        if dice_result > 3:
            win_amount = round(bet * 1.5, 1)
            if win_amount > bot_balance:
                await message.reply("🛑 Бот не может выплатить выигрыш. Попробуй позже.", parse_mode='markdown')
            else:
                new_balance = round(drug_count + win_amount, 1)
                new_bot_balance = round(bot_balance - win_amount, 1)
                outcome_message += f'🎉 Поздравляем, вы выиграли `{win_amount}` гр. Ваш новый баланс: `{new_balance}` гр.'
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
            await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')

    elif condition.isdigit() and int(condition) in range(1, 7):
        number = int(condition)
        if dice_result == number:
            win_amount = round(bet * 3, 1)
            if win_amount > bot_balance:
                await message.reply("🛑 Бот не может выплатить выигрыш. Попробуй позже.", parse_mode='markdown')
            else:
                new_balance = round(drug_count + win_amount, 1)
                new_bot_balance = round(bot_balance - win_amount, 1)
                outcome_message += f'🎉 Поздравляем, вы выиграли `{win_amount}` гр. Ваш новый баланс: `{new_balance}` гр.'
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
                cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>3</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id))
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_bot_balance, bot_id2))
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. *Твой новый баланс: `{new_balance}` гр.*'
            cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (new_balance, user_id))
            await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>3</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
    else:
        await message.reply("🛑 Неправильное условие! *Условия: `чет`, `нечет`, `меньше`, `больше`, или число от `1` до `6`.*", parse_mode='markdown')
        return
    cursor.execute('UPDATE users SET last_casino = ? WHERE id = ?', (datetime.now().isoformat(), user_id))
    conn.commit()
    await message.reply(outcome_message, parse_mode='markdown')