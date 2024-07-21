from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command, CommandObject
from handlers.models import Users
from tortoise.models import Model
from tortoise import fields
from datetime import datetime, timedelta
import asyncio
from config import bot
import os

router = Router()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user

@router.message(Command('casino'))
async def casino(message: Message, command: CommandObject):
    args = command.args
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else message.from_user.id
    user = await get_user(user_id)

    bot_user = await get_user(1)
    bot_balance = bot_user.drug_count

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

    if not user:
        await message.reply('❌ Профиль не найден')
        return

    drug_count = user.drug_count
    last_casino = user.last_casino

    # Проверка кулдауна
    if last_casino is not None:
        # Преобразование `last_casino` в offset-naive datetime, если необходимо
        if last_casino.tzinfo is not None:
            last_casino = last_casino.replace(tzinfo=None)

        # Текущая дата и время (offset-naive)
        now = datetime.now()

        # Проверка кулдауна
        if (now - last_casino) < timedelta(seconds=10):
            await message.reply('⏳ Ты только что *крутил казик*, солевая обезьяна, *подожди 10 секунд по братски.*', parse_mode='markdown')
            return

    # Обновляем время последнего действия после успешной проверки
    user.last_casino = datetime.now()  # Текущая дата и время (offset-naive)
    await user.save()
    if bet > drug_count:
        await message.reply("🛑 Твоя ставка больше твоего баланса!", parse_mode='markdown')
        return
    if bot_balance <= bet:
        await message.reply("🛑 У бота недостаточно средств для проведения игры. Попробуй позже.", parse_mode='markdown')
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
                user.drug_count = new_balance
                bot_user.drug_count = new_bot_balance
                await user.save()
                await bot_user.save()
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            drug_count = new_balance
            bot_balance = new_bot_balance
            await user.save()
            await bot_user.save()

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
                user.drug_count = new_balance
                bot_user.drug_count = new_bot_balance
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            user.drug_count = new_balance
            bot_user.drug_count = new_bot_balance
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
                user.drug_count = new_balance
                bot_user.drug_count = new_bot_balance
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            user.drug_count = new_balance
            bot_user.drug_count = new_bot_balance
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
                user.drug_count = new_balance
                bot_user.drug_count = new_bot_balance
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.5</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. Твой новый баланс: `{new_balance}` гр.'
            user.drug_count = new_balance
            bot_user.drug_count = new_bot_balance
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
                user.drug_count = new_balance
                bot_user.drug_count = new_bot_balance
                await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>3</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        else:
            win_amount = 0
            new_balance = round(drug_count - bet, 1)
            new_bot_balance = round(bot_balance + bet, 1)
            user.drug_count = new_balance
            bot_user.drug_count = new_bot_balance
            outcome_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз!. *Твой новый баланс: `{new_balance}` гр.*'
            await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>3</code>\ndrug_count: <code>{drug_count-bet}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
    else:
        await message.reply("🛑 Неправильное условие! *Условия: `чет`, `нечет`, `меньше`, `больше`, или число от `1` до `6`.*", parse_mode='markdown')
        return
        await user.save()
        await bot_user.save()
    user.last_casino = datetime.now()
    await message.reply(outcome_message, parse_mode='markdown')
