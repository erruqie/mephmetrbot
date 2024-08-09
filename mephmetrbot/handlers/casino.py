import random
import asyncio
from aiogram import Router
from aiogram.types import Message
from datetime import datetime, timedelta
from mephmetrbot.handlers.models import Users
from mephmetrbot.config import bot, LOGS_CHAT_ID
from aiogram.filters.command import Command, CommandObject

router = Router()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user

@router.message(Command('casino'))
async def casino_command(message: Message, command: CommandObject):
    if message.chat.id != message.from_user.id:
        await message.reply('📛️️ Эта команда работает только в ЛС с ботом!')
        return
    args = command.args
    user_id = message.from_user.id
    user = await get_user(user_id)
    bot_user = await get_user(1)
    bot_balance = bot_user.drug_count

    now = datetime.now()
    today = now.date()

    if not args:
        await message.reply("🛑 Укажи ставку и коэффициент автостопа ракетки! Пример:\n<code>/casino 10 2</code>", parse_mode='HTML')
        return

    parts = args.split()

    if len(parts) < 2:
        await message.reply("🛑 Укажи ставку и коэффициент автостопа ракетки! Пример:\n<b>/casino 10 2</b>", parse_mode='HTML')
        return

    try:
        bet = int(parts[0])
        target_multiplier = float(parts[1])
    except ValueError:
        await message.reply("🛑 <b>Ставка должна быть целым числом, а коэффициент числом!</b>", parse_mode='HTML')
        return
    if target_multiplier < 1.1:
        await message.reply("🛑 Минимальный коэффициент автостопа: <code>1.1x</code>", parse_mode='HTML')
        return
    if bet < 10:
        await message.reply("🛑 Ставка должна быть больше <code>10</code> гр.", parse_mode='HTML')
        return

    if not user:
        await message.reply('❌ Профиль не найден')
        return

    if user.last_game_day != today:
        user.game_count = 0
        user.last_game_day = today

    if (user.vip == 0 and user.game_count >= 20) and (user.is_admin == 0 and user.is_tester == 0):
        await message.reply("🛑 <b>Ты достиг дневного лимита игр в казино. Приобрети</b> <code>VIP-статус</code> <b>для снятия ограничений.</b>",parse_mode='HTML')
        return

    drug_count = user.drug_count

    if bet > drug_count:
        await message.reply("🛑 <b>Твоя ставка больше твоего баланса!</b>", parse_mode='HTML')
        return
    if bot_balance <= bet:
        await message.reply("🛑 <b>У бота недостаточно средств для проведения игры. Попробуй позже.</b>", parse_mode='HTML')
        return

    last_casino = user.last_casino
    if last_casino:
        last_casino = last_casino.replace(tzinfo=None)

    if last_casino and (now - last_casino).total_seconds() < 20:
        await message.reply('⏳ Ты только что <b>крутил казик</b>, солевая обезьяна, <b>подожди 10 секунд по братски.</b>', parse_mode='HTML')
        return

    if bet > drug_count:
        await message.reply("🛑 <b>Твоя ставка больше твоего баланса!</b>", parse_mode='HTML')
        return
    if bot_balance <= bet:
        await message.reply("🛑 <b>У бота недостаточно средств для проведения игры. Попробуй позже.</b>", parse_mode='HTML')
        return

    user.drug_count -= bet
    user.game_count += 1
    await user.save()

    dice_message = await message.reply("<b>🚀 Начинаем игру... Ракетка взлетает!</b>", parse_mode='HTML')
    await asyncio.sleep(2.5)
    random_number = random.uniform(0, 1)
    if random_number < 0.11:
        random_multiplier = 0
    elif random_number < 0.55:
        random_multiplier = round(random.uniform(1, 1.9), 2)
    elif random_number > 0.55 and random_number < 0.65:
        random_multiplier = round(random.uniform(4, 6), 2)
    else:
        random_multiplier = round(random.uniform(2, 5), 2)

    current_multiplier = 0
    result_message = ''

    if current_multiplier == random_multiplier:
        await dice_message.edit_text(f"🚀 <b>Коэффициент</b>: <code>{current_multiplier}x</code>", parse_mode='HTML')
        new_balance = round(user.drug_count, 1)
        if user.is_admin == False or None and user.is_tester == False or None:
            new_bot_balance = round(bot_balance + bet, 1)
            bot_user.drug_count = new_bot_balance
            await bot_user.save()
        if user.vip != 1:
            result_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз! Твой новый баланс: <code>{new_balance}</code> гр.\nОставшееся количество спинов: <code>{20 - int(user.game_count)}</code>'
        else:
            result_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз! Твой новый баланс: <code>{new_balance}</code> гр.'
        await bot.send_message(LOGS_CHAT_ID, f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\ntarget_multiplier: <code>{target_multiplier}</code>\nactual_multiplier: <code>{random_multiplier}</code>\ndrug_count: <code>{new_balance}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
        user.last_casino = now
        await user.save()
        await dice_message.edit_text(result_message, parse_mode='HTML')
        return

    while current_multiplier < random_multiplier:
        current_multiplier = round(current_multiplier + 0.5, 2)
        if current_multiplier > random_multiplier:
            current_multiplier = random_multiplier
        await dice_message.edit_text(f"🚀 <b>Коэффициент</b>: <code>{current_multiplier}x</code>", parse_mode='HTML')
        await asyncio.sleep(1.5)
    result_message = f"🚀 Итоговый коэффициент: <code>{random_multiplier}x</code>. "

    if random_multiplier >= target_multiplier:
        win_amount = round(bet * target_multiplier, 1)
        if win_amount > bot_balance:
            await message.reply("🛑 <b>Бот не может выплатить выигрыш. Попробуй позже.</b>", parse_mode='HTML')
        else:
            new_balance = round(user.drug_count + win_amount, 1)
            if user.is_admin != True or user.is_tester != True:
                new_bot_balance = round(bot_balance - win_amount, 1)
                bot_user.drug_count = new_bot_balance
                await bot_user.save()
            if user.vip != 1:
                result_message += f'🎉 Поздравляем, вы выиграли <code>{win_amount}</code> гр. Ваш новый баланс: <code>{new_balance}</code> гр.\nОставшееся количество спинов: <code>{20 - int(user.game_count)}</code>'
            else:
                result_message += f'🎉 Поздравляем, вы выиграли <code>{win_amount}</code> гр. Ваш новый баланс: <code>{new_balance}</code> гр.'
            user.drug_count = new_balance
            await bot.send_message(LOGS_CHAT_ID, f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.2</code>\ndrug_count: <code>{new_balance}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
    else:
        new_balance = round(user.drug_count, 1)
        if user.is_admin == False or None and user.is_tester == False or None:
            new_bot_balance = round(bot_balance + bet, 1)
            bot_user.drug_count = new_bot_balance
            await bot_user.save()
        if user.vip != 1:
            result_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз! Твой новый баланс: <code>{new_balance}</code> гр.\nОставшееся количество спинов: <code>{20 - int(user.game_count)}</code>'
        else:
            result_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз! Твой новый баланс: <code>{new_balance}</code> гр.'
        await bot.send_message(LOGS_CHAT_ID, f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\ntarget_multiplier: <code>{target_multiplier}</code>\nactual_multiplier: <code>{random_multiplier}</code>\ndrug_count: <code>{new_balance}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')

    user.last_casino = now
    await user.save()
    await dice_message.edit_text(result_message, parse_mode='HTML')


