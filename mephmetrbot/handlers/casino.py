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
async def casino(message: Message, command: CommandObject):
    args = command.args
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else message.from_user.id
    user = await get_user(user_id)
    bot_user = await get_user(1)
    bot_balance = bot_user.drug_count

    if not args:
        await message.reply("🛑 Укажи ставку и коэффицент автостопа ракетки! Пример:\n`/casino 100 2`", parse_mode='markdown')
        return

    parts = args.split()

    if len(parts) < 2:
        await message.reply("🛑 Укажи ставку и коэффицент автостопа ракетки! Пример:\n`/casino 100 2`", parse_mode='markdown')
        return

    try:
        bet = int(parts[0])
        target_multiplier = float(parts[1])
    except ValueError:
        await message.reply("🛑 Ставка должна быть целым числом, а коэффициент числом!", parse_mode='markdown')
        return

    if bet < 10:
        await message.reply("🛑 Ставка должна быть больше `10` гр.", parse_mode='markdown')
        return

    if not user:
        await message.reply('❌ Профиль не найден')
        return

    drug_count = user.drug_count

    if bet > drug_count:
        await message.reply("🛑 Твоя ставка больше твоего баланса!", parse_mode='markdown')
        return
    if bot_balance <= bet:
        await message.reply("🛑 У бота недостаточно средств для проведения игры. Попробуй позже.", parse_mode='markdown')
        return

    last_casino = user.last_casino

    if last_casino is not None:
        if last_casino.tzinfo is not None:
            last_casino = last_casino.replace(tzinfo=None)
        now = datetime.now()

        if (now - last_casino) < timedelta(seconds=10):
            await message.reply('⏳ Ты только что *крутил казик*, солевая обезьяна, *подожди 10 секунд по братски.*', parse_mode='markdown')
            return

    if bet > drug_count:
        await message.reply("🛑 Твоя ставка больше твоего баланса!", parse_mode='markdown')
        return
    if bot_balance <= bet:
        await message.reply("🛑 У бота недостаточно средств для проведения игры. Попробуй позже.", parse_mode='markdown')
        return

    user.drug_count -= bet
    await user.save()

    await message.answer('🚀')
    dice_message = await message.answer(" *Начинаем игру... Ракетка взлетает!*", parse_mode='markdown')
    await asyncio.sleep(2)
    random_number = random.uniform(0, 1)
    if random_number < 0.7:
        random_multiplier = round(random.uniform(1, 1.9), 2)
    else:
        random_multiplier = round(random.uniform(2, 5), 2)
    animation = min(int(random_multiplier * 10), 30)

    for i in range(1, animation + 1):
        multiplier = round(1 + i * (random_multiplier - 1) / animation, 2)
        await dice_message.edit_text(f"🚀 *Коэффициент*: `{multiplier}`", parse_mode='markdown')
        await asyncio.sleep(3)

    result_message = f"🚀 Итоговый коэффициент: `{random_multiplier}`. "

    if random_multiplier >= target_multiplier:
        win_amount = round(bet * target_multiplier, 1)
        if win_amount > bot_balance:
            await message.reply("🛑 Бот не может выплатить выигрыш. Попробуй позже.", parse_mode='markdown')
        else:
            new_balance = round(user.drug_count + win_amount, 1)
            new_bot_balance = round(bot_balance - win_amount, 1)
            result_message += f'🎉 Поздравляем, вы выиграли `{win_amount}` гр. Ваш новый баланс: `{new_balance}` гр.'
            user.drug_count = new_balance
            bot_user.drug_count = new_bot_balance
            await user.save()
            await bot_user.save()
            await bot.send_message(LOGS_CHAT_ID, f"<b>#CASINO</b> <b>#WIN</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\nmultiplier: <code>1.2</code>\ndrug_count: <code>{new_balance}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')
    else:
        new_balance = round(user.drug_count, 1)
        new_bot_balance = round(bot_balance + bet, 1)
        result_message += f'❌ Твоя ставка не сыграла. Повезёт в следующий раз! Твой новый баланс: `{new_balance}` гр.'
        bot_user.drug_count = new_bot_balance
        await bot_user.save()
        await bot.send_message(LOGS_CHAT_ID, f"<b>#CASINO</b> <b>#LOSE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\nuser_id: <code>{user_id}</code>\nbet: <code>{bet}</code>\ntarget_multiplier: <code>{target_multiplier}</code>\nactual_multiplier: <code>{random_multiplier}</code>\ndrug_count: <code>{new_balance}</code>\n\n<a href='tg://user?id={user_id}'>mention</a>", parse_mode='HTML')

    await dice_message.delete()
    await message.reply(result_message, parse_mode='markdown')
