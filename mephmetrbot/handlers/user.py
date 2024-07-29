from aiogram import Router, F
import random
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.filters.command import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from mephmetrbot.handlers.models import Users, Clans
from mephmetrbot.config import bot, LOGS_CHAT_ID
from datetime import datetime, timedelta
import asyncio
from aiogram.exceptions import TelegramBadRequest

router = Router()

async def update_user_balance_and_drug_count(user_id: int, new_balance: int, new_drug_count: int):
    user = await Users.get(id=user_id)
    user.balance = new_balance
    user.drug_count = new_drug_count
    await user.save()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user

async def update_user_drug_count(user_id: int, new_count: int):
    user = await Users.get(id=user_id)
    user.drug_count = new_count
    await user.save()

@router.message(Command('profile'))
async def profile_command(message: Message):
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else message.from_user.id
    user = await get_user(user_id)

    if not user:
        await message.reply('❌ Профиль не найден')
        return

    clan_name = None
    if user.clan_member:
        clan = await Clans.get_or_none(id=user.clan_member)
        clan_name = clan.clan_name if clan else None

    username = message.from_user.username if user_id == message.from_user.id else message.reply_to_message.from_user.username
    full_name = message.from_user.full_name if user_id == message.from_user.id else message.reply_to_message.from_user.full_name

    profile_info = (
        f"👤 *Имя:* _{full_name}_\n"
        f"👥 *Username пользователя:* @{username}\n"
        f"🆔 *ID пользователя:* `{user_id}`\n"
        f"🌿 *Снюхано:* _{user.drug_count}_ грамм.\n"
        f"💸 *Баланс крипты:* _{user.balance}_ *$MEF*"
    )
    if user.is_admin:
        profile_info = f"👑 *Администратор*\n{profile_info}"
    if clan_name:
        profile_info = f"{profile_info}\n👥 *Клан:* *{clan_name}*"

    await message.reply(profile_info, parse_mode='markdown')


@router.message(Command('botprofile'))
async def botprofile(message: Message, command: CommandObject):
    bot_user = await get_user(1)
    await message.reply(f"🤖 *Это Бот*\n🌿 *Баланс бота:* _{bot_user.drug_count}_ грамм.", parse_mode='markdown')

@router.message(Command('shop'))
async def shop(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌿 10 грамм - 💸 5000 $MEF", callback_data="buy_10"),
        InlineKeyboardButton(text="🌿 20 грамм - 💸 9000 $MEF", callback_data="buy_20"),
        InlineKeyboardButton(text="🌿 50 грамм - 💸 20000 $MEF", callback_data="buy_50")
    )

    await message.answer(f"*🧙‍♂️ Здарова, ты попал на черный рынок, здесь ты можешь купить весь мой ассортимент.*", reply_markup=builder.as_markup(), parse_mode='markdown')


@router.callback_query(F.data.startswith('buy_'))
async def handle_purchase_callback(callback_query: CallbackQuery):
    action = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    match action:
        case 10:
            await handle_purchase(callback_query, user_id, 10, 5000)
        case 20:
            await handle_purchase(callback_query, user_id, 20, 9000)
        case 50:
            await handle_purchase(callback_query, user_id, 50, 20000)
        case _:
            return

async def handle_purchase(callback_query: CallbackQuery, user_id: int, amount: int, cost: int):
    user = await get_user(user_id)

    if user.balance >= cost:
        new_balance = user.balance - cost
        new_drug_count = user.drug_count + amount
        await update_user_balance_and_drug_count(user_id, new_balance, new_drug_count)
        await bot.answer_callback_query(callback_query.id, text=f"😈 Спасибо за покупку кентишка. Ты купил {amount} грамм за {cost} $MEF.", show_alert=True)
    else:
        await bot.answer_callback_query(callback_query.id, text="❌ Недостаточно крипты для покупки.", show_alert=True)

@router.message(Command('give'))
async def give_command(message: Message, command: CommandObject):
    user_id = message.from_user.id
    user = await get_user(user_id)
    try:
        args = command.args.split(' ', maxsplit=1)
    except:
        await message.reply('❌ Не указаны аргументы, укажи сколько грамм хочешь передать челику')
        return

    try:
        value = int(args[0])
    except ValueError:
        await message.reply('❌ Введи целое число')
        return

    recipient_id = message.reply_to_message.from_user.id if message.reply_to_message else None
    if recipient_id == 7266772626:
        await message.reply('❌ Вы не можете передать средства боту')
        return

    recipient = await get_user(recipient_id)
    if not recipient:
        await message.reply('❌ Пользователь не найден')
        return

    if value <= 0:
        await message.reply('❌ Значение должно быть положительным и больше нуля')
        return

    if user.drug_count < value:
        await message.reply('❌ Недостаточно граммов мефа для передачи')
        return

    commission = round(value * 0.10)
    net_value = value - commission
    bot_user = await get_user(7266772626)
    if not bot_user:
        bot_user = await Users.create(id=7266772626, drug_count=0)

    recipient.drug_count += net_value
    user.drug_count -= value
    bot_user.drug_count += commission

    await recipient.save()
    await user.save()
    await bot_user.save()

    await bot.send_message(
        LOGS_CHAT_ID,
        f"<b>#GIVE</b>\n\nfirst_name: <code>{message.from_user.first_name}</code>\n"
        f"user_id: <code>{recipient_id}</code>\nvalue: <code>{net_value}</code>\n"
        f"Commission: <code>{commission}</code>\n\n<a href='tg://user?id={recipient_id}'>mention</a>",
        parse_mode='HTML'
    )

    recipient_full_name = message.reply_to_message.from_user.full_name if message.reply_to_message else ""

    await message.reply(
        f"✅ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) _подарил(-а) {value} гр. мефа_ "
        f"[{recipient_full_name}](tg://user?id={recipient_id})!\nКомиссия: `{commission}` гр. мефа\n"
        f"Получено `{net_value}` гр. мефа.",
        parse_mode='markdown'
    )

@router.message(Command('work'))
async def work_command(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user.balance is None:
        user.balance = 0

    last_work = user.last_work
    now = datetime.now()

    if last_work:
        last_work = last_work.replace(tzinfo=None)

    if last_work and (now - last_work).total_seconds() < 21600:
        remaining_time = timedelta(hours=1) - (now - last_work)
        await message.reply(f'⏳ Ты недавно ходил прятать *закладку*, подожди {remaining_time.seconds // 60} минут.', parse_mode='markdown')
        return

    if random.randint(1, 100) > 50:
        count = random.randint(500, 1300)
        user.balance += count
        user.last_work = now
        await user.save()
        await message.reply(f"🌿 {message.from_user.first_name}, ты пошёл в лес и *спрятал закладку*, тебя никто не спалил, ты заработал `{count} $MEF.`", parse_mode='markdown')
    else:
        user.last_work = now
        await user.save()
        await message.reply(f"❌ *{message.from_user.first_name}*, тебя *спалил мент* и *дал тебе по ебалу*\n⏳ Следующая попытка доступна через *12 часов.*", parse_mode='markdown')



@router.message(Command('find'))
async def find_command(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    drug_count, last_find = user.drug_count, user.last_find
    now = datetime.now()

    if last_find:
        last_find = last_find.replace(tzinfo=None)

    if last_find and (now - last_find).total_seconds() < 21600:
        remaining_time = timedelta(hours=1) - (now - last_find)
        await message.reply(f'⏳ Ты недавно *ходил за кладом, подожди {remaining_time.seconds // 60} минут.*', parse_mode='markdown')
        return

    if random.randint(1, 100) > 50:
        count = random.randint(2, 10)
        user.drug_count += count
        user.last_find = now
        user.last_use_time = datetime.fromtimestamp(0)
        await user.save()
        await message.reply(f"👍 {message.from_user.first_name}, ты пошёл в лес и *нашел клад*, там лежало `{count} гр.` мефчика!\n🌿 Твое время команды /drug обновлено", parse_mode='markdown')
    else:
        if drug_count > 1:
            count = random.randint(1, round(drug_count))
        else:
            count = 0
        user.drug_count -= count
        user.last_find = now
        await user.save()
        if count != 0:
            await message.reply(f"❌ *{message.from_user.first_name}*, тебя *спалил мент* и *дал тебе по ебалу*\n🌿 Тебе нужно откупиться, мент предложил взятку в размере `{count} гр.`\n⏳ Следующая попытка доступна через *12 часов.*", parse_mode='markdown')
        else:
            await message.reply(f"❌ *{message.from_user.first_name}*, тебя *спалил мент* и *дал тебе по ебалу*\n⏳ Следующая попытка доступна через *12 часов.*", parse_mode='markdown')

@router.message(Command('top'))
async def top_command(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    top_users = await Users.all().order_by('-drug_count').limit(10)

    if top_users:
        response = "🔝ТОП 10 ЛЮТЫХ МЕФЕДРОНЩИКОВ В МИРЕ🔝:\n\n"
        valid_user_ids = {user.id for user in top_users if user.id != 1 and user.drug_count > 0}

        async def fetch_user_info(user_id):
            try:
                return (user_id, await bot.get_chat(user_id))
            except TelegramBadRequest:
                return (user_id, None)

        user_infos = await asyncio.gather(
            *[fetch_user_info(valid_user_id) for valid_user_id in valid_user_ids]
        )

        user_info_dict = {info_id: info for info_id, info in user_infos if info}

        counter = 1
        for user in top_users:
            if user.id == 1:
                continue
            drug_count = user.drug_count
            user_info = user_info_dict.get(user.id, None)
            if user_info:
                response += f"{counter}) *{user_info.full_name}*: `{drug_count} гр. мефа`\n"
                counter += 1

        if counter == 1:
            await message.reply('Никто еще не принимал меф.')
        else:
            await message.reply(response, parse_mode='markdown')
    else:
        await message.reply('Никто еще не принимал меф.')

@router.message(Command('take'))
async def take_command(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    reply_msg = message.reply_to_message
    if reply_msg:
        if reply_msg.from_user.id == 7266772626:
            await message.reply(f'❌ Вы не можете забрать меф у бота')
            return
        if reply_msg.from_user.id != message.from_user.id:
            victim = await get_user(reply_msg.from_user.id)
            if not victim or user.drug_count <= 1 or victim.drug_count <= 1:
                await message.reply('❌ У вас или у жертвы недостаточно мефа.')
                return
            last_time_data = await state.get_data()
            last_time = last_time_data.get('time') if last_time_data else None

            if last_time and (datetime.now() - datetime.fromisoformat(last_time)).total_seconds() < 86400:
                await message.reply("❌ Нельзя пиздить меф так часто! Ты сможешь спиздить меф через 1 день.")
                return

            variables = ['noticed', 'hit', 'pass']
            randomed = random.choice(variables)
            if randomed == 'noticed':
                user.drug_count -= 1
                await message.reply('❌ *Жертва тебя заметила*, и ты решил убежать. Спиздить меф не получилось. Пока ты бежал, *ты потерял* `1 гр.`', parse_mode='markdown')
            elif randomed == 'hit':
                user.drug_count -= 1
                await message.reply('❌ *Жертва тебя заметила*, и пизданула тебя бутылкой по башке. Спиздить меф не получилось. *Жертва достала из твоего кармана* `1 гр.`', parse_mode='markdown')
            elif randomed == 'pass':
                victim.drug_count -= 1
                user.drug_count += 1
                await victim.save()
                victim_user_id = reply_msg.from_user.id
                victim_username = f'tg://user?id={victim_user_id}'
                await message.reply(f"✅ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) спиздил(-а) один грамм мефа у [{reply_msg.from_user.first_name}]({victim_username})!", parse_mode='markdown')
            await state.update_data(time=datetime.now().isoformat())
            await user.save()
    else:
        await message.reply('❌ Ответьте на сообщение, чтобы забрать меф.')

@router.message(Command('drug'))
async def drug_command(message: Message):
    user = await get_user(message.from_user.id)

    drug_count, last_use_time = user.drug_count, user.last_use_time
    now = datetime.now()

    if last_use_time:
        last_use_time = last_use_time.replace(tzinfo=None)

    if last_use_time and (now - last_use_time).total_seconds() < 3600:
        remaining_time = timedelta(hours=1) - (now - last_use_time)
        await message.reply(f"❌ *{message.from_user.first_name}*, _ты уже нюхал(-а)!_\n\n🌿 Всего снюхано `{drug_count} грамм` мефедрона\n\n⏳ Следующий занюх доступен через `{remaining_time.seconds // 60} минут.`", parse_mode='markdown')
        return

    if random.randint(0, 100) < 20:
        await message.reply(f"🧂 *{message.from_user.first_name}*, _ты просыпал(-а) весь мефчик!_\n\n🌿 Всего снюхано `{drug_count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')
        user.last_use_time = now
        return

    count = random.randint(1, 10)
    user.drug_count += count
    user.last_use_time = now
    await user.save()
    await message.reply(f"👍 *{message.from_user.first_name}*, _ты занюхнул(-а) {count} грамм мефчика!_\n\n🌿 Всего снюхано `{user.drug_count}` грамм мефедрона\n\n⏳ Следующий занюх доступен через `1 час.`", parse_mode='markdown')


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
async def start_command(message: Message, command: CommandObject):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='📢 Канал', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💰 Донат', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💬 Чат', url='https://t.me/mefmetrchat')
    )
    await message.reply("👋 *Здарова шныр*, этот бот сделан для того, чтобы *считать* сколько *грамм мефедрончика* ты снюхал\n\n🛑 Внимание, это всего лишь игровой бот, здесь не продают меф. Не стоит писать об этом мне, ваши попытки приобрести наркотические вещества - будут переданы правохранительным органам.\n\n🧑‍💻 Бот разработан *powerplantsmoke.t.me* и *tbankhater.t.me*", reply_markup=builder.as_markup(), parse_mode='markdown')


@router.message(Command('about'))
async def about_command(message: Message):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='📢 Канал', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💰 Донат', url='https://t.me/mefmetrch'),
        InlineKeyboardButton(text='💬 Чат', url='https://t.me/mefmetrchat')
    )
    await message.reply("🧑‍💻 Бот разработан powerplantsmoke.t.me и tbankhater.t.me", reply_markup=builder.as_markup())
