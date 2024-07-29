import random
import sys
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from mephmetrbot.config import bot, LOGS_CHAT_ID
from mephmetrbot.handlers.models import Users, Clans
from tortoise.exceptions import IntegrityError, DoesNotExist

router = Router()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user

async def get_clan(clan_id):
    clan, _ = await Clans.get_or_create(id=clan_id)
    return clan

@router.message(Command('clancreate'))
async def create_clan(message: Message, command: Command):
    args = command.args
    user_id = message.from_user.id
    user = await get_user(user_id)

    if args:
        clan_name = args
        clan_exist = await Clans.filter(clan_name=clan_name).exists()

        if clan_exist:
            await message.reply('🛑 Клан с таким названием уже существует')
        else:
            clan_id = random.randint(100000, 999999)
            drug_count = user.drug_count

            if user.clan_member is not None and user.clan_member > 1:
                await message.reply("🛑 Вы уже состоите в клане.", parse_mode='markdown')
            elif user.clan_member is None or user.clan_member == 0:
                if drug_count >= 100:
                    try:
                        new_clan = await Clans.create(
                            id=clan_id,
                            clan_name=clan_name,
                            clan_owner_id=user_id,
                            clan_balance=0
                        )
                        user.clan_member = new_clan.id
                        user.drug_count -= 100
                        await user.save()

                        await bot.send_message(
                            LOGS_CHAT_ID,
                            f"<b>#NEWCLAN</b>\n\n"
                            f"clanid: <code>{clan_id}</code>\n"
                            f"clanname: <code>{clan_name}</code>\n"
                            f"clanownerid: <code>{user_id}</code>"
                            f"<a href='tg://user?id={user_id}'>clanowner mention</a>",
                            parse_mode='HTML'
                        )
                        await message.reply(
                            f"✅ Клан *{clan_name}* успешно создан.\nВаш идентификатор клана: `{clan_id}`\nС вашего баланса списано `100` гр.",
                            parse_mode='markdown'
                        )
                    except IntegrityError as e:
                        await message.reply(f"🛑 Произошла ошибка при создании клана. Пожалуйста, попробуйте снова.")
                        print(f"IntegrityError: {e}")
                else:
                    await message.reply("🛑 Недостаточно средств.\nСтоимость создания клана: `100` гр.", parse_mode='markdown')
    else:
        await message.reply("🛑 Укажи название клана\nПример:`/clancreate КрУтЫе_ПеРцЫ`\nСтоимость создания клана: `100` гр.", parse_mode='markdown')

@router.message(Command('deposit'))
async def deposit(message: Message, command: Command):
        args = command.args if command.args else None

        if args is None:
            await message.reply("🛑 Вы не указали сумму. Пример:\n`/deposit 100`", parse_mode='markdown')
            return

        args = args.split(' ', maxsplit=1)[0]
        user_id = message.from_user.id
        user = await get_user(user_id)

        try:
            cost = int(args)
        except ValueError:
            await message.reply('❌ Введи целое число')
            return

        user_balance = user.drug_count
        clan_id = user.clan_member

        if clan_id is None or clan_id == 0:
            await message.reply("🛑 Вы не состоите в клане", parse_mode='markdown')
            return

        clan = await Clans.filter(id=clan_id).first()

        if clan is None:
            await message.reply("🛑 Клан не найден", parse_mode='markdown')
            return

        if cost < 0:
            await message.reply('❌ Значение не может быть отрицательным')
            return
        elif cost == 0:
            await message.reply('❌ Значение не может быть равным нулю')
            return

        elif cost > user_balance:
            await message.reply(f"🛑 Недостаточно средств. Ваш баланс: `{user_balance}` гр.", parse_mode='markdown')
            return

        clan.clan_balance += cost
        user.drug_count -= cost
        await clan.save()
        await user.save()

        await message.reply(
            f"✅ Вы успешно пополнили баланс клана `{clan.clan_name}` на `{cost}` гр.",
            parse_mode='markdown'
        )

        await bot.send_message(
            LOGS_CHAT_ID,
            f"<b>#DEPOSIT</b>\nclanname: <code>{clan.clan_name}</code>\namount: <code>{cost}</code>\nuserid: <code>{user_id}</code>\nfirstname: {message.from_user.first_name}\n<a href='tg://user?id={user_id}'>mention</a>",
            parse_mode='HTML'
        )

@router.message(Command('withdraw'))
async def withdraw(message: Message, command: Command):
        args = command.args if command.args else None

        if args is None:
            await message.reply("🛑 Вы не указали сумму. Пример:\n`/withdraw 100`", parse_mode='markdown')
            return


        args = args.split(' ', maxsplit=1)[0]
        user_id = message.from_user.id
        user = await get_user(user_id)

        try:
            cost = int(args)
        except ValueError:
            await message.reply('❌ Введи целое число')
            return

        user_balance = user.drug_count
        clan_id = user.clan_member

        clan = await Clans.filter(id=clan_id).first()
        clan_owner_id = clan.clan_owner_id

        if clan is None:
            await message.reply("🛑 Клан не найден", parse_mode='markdown')
            return

        if user_id != clan_owner_id:
            await message.reply(f"🛑 Приглашать в клан может только создатель", parse_mode='markdown')

        if cost < 0:
            await message.reply('❌ Значение не может быть отрицательным')
            return
        elif cost == 0:
            await message.reply('❌ Значение не может быть равным нулю')
            return
        elif cost > clan.clan_balance:
            await message.reply(f"🛑 Недостаточно средств на балансе клана. Баланс клана: `{clan.clan_balance}` гр.",
                        parse_mode='markdown')
            return

        clan.clan_balance -= cost
        user.drug_count += cost
        await clan.save()
        await user.save()

        await message.reply(
            f"✅ Вы успешно вывели `{cost}` гр. с баланса клана `{clan.clan_name}.`",
            parse_mode='markdown'
        )

        await bot.send_message(
            LOGS_CHAT_ID,
            f"<b>#DEPOSIT</b>\nclanname: <code>{clan.clan_name}</code>\namount: <code>{cost}</code>\nuserid: <code>{user_id}</code>\nfirstname: {message.from_user.first_name}\n<a href='tg://user?id={user_id}'>mention</a>",
            parse_mode='HTML'
        )


@router.message(Command('clantop'))
async def clan_top(message: Message):
    top_clans = await Clans.all().order_by('-clan_balance')[:10].values('clan_name', 'clan_balance')

    if top_clans:
        response = "🔝 ТОП 10 МЕФЕДРОНОВЫХ КАРТЕЛЕЙ В МИРЕ 🔝:\n"
        counter = 1

        for clan in top_clans:
            clan_name = clan['clan_name']
            clan_balance = clan['clan_balance']
            response += f"{counter}) *{clan_name}*: `{clan_balance} гр. мефа`\n"
            counter += 1

        await message.reply(response, parse_mode='markdown')
    else:
        await message.reply('🛑 Ещё ни один клан не пополнил свой баланс.')

@router.message(Command('clanowner'))
async def clan_owner(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    clan_id = user.clan_member
    if clan_id == 0:
        await message.reply(f"🛑 *Вы не состоите в клане*", parse_mode='markdown')
    elif clan_id > 0:
        clan = await Clans.filter(id=clan_id).first()
        current_owner_id = clan.clan_owner_id
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
        new_owner = await Users.filter(id=new_owner_id).first()

        if not new_owner:
            await message.reply(f"🛑 *Не удалось найти пользователя с указанным идентификатором*", parse_mode='markdown')
            return
        await Clans.filter(id=clan_id).update(clan_owner_id=new_owner_id)
        await message.reply(f"✅ *Вы передали владельца клана!*", parse_mode='markdown')

# clan_wars = {}
#
# # @router.message(Command('clanwar'))
# async def clanwar(message: Message):
#     user_id = message.from_user.id
#     cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
#     user = cursor.fetchone()
#
#     if not user:
#         await message.reply('❌ Пользователь не найден')
#         return
#
#     is_banned = user[4]
#     clan_id = user[7]
#
#     if is_banned == 1:
#         await message.reply('🛑 Вы заблокированы в боте!')
#         return
#
#     if clan_id == 0:
#         await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')
#     else:
#         cursor.execute('SELECT clan_id, clan_name, clan_owner_id FROM clans WHERE clan_id = ?', (clan_id,))
#         clan = cursor.fetchone()
#         clan_name, clan_owner_id = clan[1], clan[2]
#
#         if user_id != clan_owner_id:
#             await message.reply(f"🛑 Вы не являетесь владельцем клана", parse_mode='markdown')
#             return
#
#         if len(message.text.split()) < 2:
#             await message.reply(f"🛑 Вы не указали идентификатор клана для начала войны", parse_mode='markdown')
#             return
#
#         target_clan_identifier = ' '.join(message.text.split()[1:])
#         cursor.execute('SELECT clan_id, clan_name FROM clans WHERE clan_name = ? OR clan_id = ?', (target_clan_identifier, target_clan_identifier))
#         target_clan = cursor.fetchone()
#
#         if not target_clan:
#             await message.reply(f"🛑 Не удалось найти клан с указанным идентификатором", parse_mode='markdown')
#             return
#
#         target_clan_id, target_clan_name = target_clan
#
#         cursor.execute('SELECT chat_id FROM chats')
#         chats = cursor.fetchall()
#         for chat_id_row in chats:
#             chat_id = chat_id_row[0]
#             try:
#                 await bot.send_message(chat_id, f"⚔️ Клан *{clan_name}* начал войну с *{target_clan_name}*!", parse_mode='markdown')
#             except Exception as e:
#                 print(f"Ошибка отправки сообщения в {chat_id}: {e}")
#
#         clan_wars[clan_id] = target_clan_id
#         clan_wars[target_clan_id] = clan_id
#
#         start_time = datetime.now()
#
#         while (datetime.now() - start_time).total_seconds() < 3600:
#             await asyncio.sleep(3600 - (datetime.now() - start_time).total_seconds())
#
#         cursor.execute('SELECT SUM(drug_count) FROM users WHERE clan_id = ?', (clan_id,))
#         clan_total = cursor.fetchone()[0]
#
#         cursor.execute('SELECT SUM(drug_count) FROM users WHERE clan_id = ?', (target_clan_id,))
#         target_clan_total = cursor.fetchone()[0]
#
#         if clan_total > target_clan_total:
#             winner_clan_id, loser_clan_id = clan_id, target_clan_id
#             winner_clan_name, loser_clan_name = clan_name, target_clan_name
#         else:
#             winner_clan_id, loser_clan_id = target_clan_id, clan_id
#             winner_clan_name, loser_clan_name = target_clan_name, clan_name
#
#         cursor.execute('UPDATE clans SET clan_balance = clan_balance + (SELECT SUM(drug_count) FROM users WHERE clan_id = ?) WHERE clan_id = ?', (loser_clan_id, winner_clan_id))
#         cursor.execute('UPDATE users SET drug_count = 0 WHERE clan_id = ?', (loser_clan_id,))
#         conn.commit()

        # del clan_wars[clan_id]
        # del clan_wars[target_clan_id]
        #
        # await message.reply(f"⚔️ Клан *{winner_clan_name}* выиграл войну против *{loser_clan_name}*!", parse_mode='markdown')
        # for chat_id_row in chats:
        #     chat_id = chat_id_row[0]
        #     try:
        #         await bot.send_message(chat_id, f"*⚔️ Клан {winner_clan_name} выиграл войну против {loser_clan_name}!*", parse_mode='markdown')
        #     except Exception as e:
        #         print(f"Ошибка отправки сообщения в {chat_id}: {e}")

@router.message(Command('claninfo'))
async def claninfo(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    clan_id = user.clan_member

    if clan_id == 0:
        await message.reply("🛑 Вы не состоите в клане", parse_mode='markdown')
    else:
        clan = await Clans.filter(id=clan_id).first()
        if clan:
            clan_balance = clan.clan_balance
            clan_name = clan.clan_name
            clan_owner_id = clan.clan_owner_id
            clan_owner = await bot.get_chat(clan_owner_id)
            clan_owner_name = clan_owner.first_name

            await message.reply(
                f"👥 Клан: `{clan_name}`\n👑 Владелец клана: [{clan_owner_name}](tg://user?id={clan_owner_name})\n🌿 Баланс клана `{clan_balance}` гр.",
                parse_mode='markdown'
            )
        else:
            await message.reply("🛑 Клан не найден.", parse_mode='markdown')

@router.message(Command('clanmembers'))
async def clanmembers(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    clan_id = user.clan_member
    clan_members = await Users.filter(clan_member=clan_id).values()
    clan = await Clans.filter(id=clan_id).first()
    if clan:
        clan_name = clan.clan_name
        clan_owner_id = clan.clan_owner_id
        if clan_id > 0:
            if clan_members:
                response = f"👥 Список участников клана *{clan_name}*:\n"
                counter = 1
                clan_owner = None
                for member in clan_members:
                    if member['id'] == clan_owner_id:
                        clan_owner = member
                        break
                if clan_owner:
                    user_info = await bot.get_chat(member['id'])
                    response += f"{counter}) *{user_info.full_name}* 👑\n"
                    counter += 1
                for member in clan_members:
                    if member['id'] != clan_owner_id:
                        user_info = await bot.get_chat(member['id'])
                        response += f"{counter}) {user_info.full_name}\n"
                        counter += 1
                await message.reply(response, parse_mode='markdown')
    else:
        await message.reply(f"🛑 Вы не состоите в клане", parse_mode='markdown')

@router.message(Command('claninvite'))
async def claninvite(message: Message):
    user_id = message.from_user.id
    try:
        user = await Users.get(id=user_id)
        is_banned = user.is_banned
        clan_id = user.clan_member
    except DoesNotExist:
        await message.reply("Пользователь не найден!")
        return
    try:
        clan = await Clans.get(id=clan_id)
    except DoesNotExist:
        await message.reply("Клан не найден!")
        return

    if clan:
        clan_name = clan.clan_name
        clan_owner_id = clan.clan_owner_id

        if user_id == clan_owner_id:
            reply_msg = message.reply_to_message
            if reply_msg and reply_msg.from_user.id == 7266772626:
                await message.reply(f'❌ Вы не можете пригласить бота в клан')
                return

            if reply_msg:
                invited_user_id = reply_msg.from_user.id
                try:
                    invited_user = await Users.get(id=invited_user_id)
                    clan_member = invited_user.clan_member
                    clan_invite = invited_user.clan_invite
                except DoesNotExist:
                    await Users.create(id=invited_user_id, drug_count=0, is_admin=0, is_banned=0, clan_member=0, clan_invite=0)
                    clan_member = 0
                    clan_invite = 0

                clan_invite = clan_invite or 0
                clan_member = clan_member or 0

                if clan_member == 0 and clan_invite == 0:
                    await Users.filter(id=invited_user_id).update(clan_invite=clan_id)

                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="Принять", callback_data=f"clan_accept:{clan_id}:{invited_user_id}"),
                            InlineKeyboardButton(text="Отклонить", callback_data=f"clan_decline:{clan_id}:{invited_user_id}")
                        ]
                    ])

                    await message.reply(f'✅ Пользователь `{reply_msg.from_user.first_name}` *приглашён в клан {clan_name}* пользователем `{message.from_user.first_name}`\nДля того чтобы принять или отказаться от приглашения, используйте кнопки ниже.', reply_markup=keyboard, parse_mode='markdown')

                elif clan_invite > 0:
                    await message.reply(f"🛑 Этот пользователь уже имеет активное приглашение", parse_mode='markdown')

                elif clan_member > 0:
                    await message.reply(f"🛑 Этот пользователь уже в клане", parse_mode='markdown')

            elif user_id != clan_owner_id:
                await message.reply(f"🛑 Приглашать в клан может только создатель", parse_mode='markdown')
        else:
            await message.reply(f"🛑 {sys.exc_info()[0]}")
    else:
        await message.reply(f"🛑 {sys.exc_info()[0]}")

@router.message(Command('clankick'))
async def clankick(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    clan_id = user.clan_member

    if clan_id == 0:
        await message.reply("🛑 Вы не состоите в клане", parse_mode='markdown')
        return

    try:
        clan = await Clans.get(id=clan_id)
    except Clans.DoesNotExist:
        await message.reply("🛑 Клан не найден", parse_mode='markdown')
        return

    clan_name = clan.clan_name
    clan_owner_id = int(clan.clan_owner_id)

    if user_id == clan_owner_id:
        reply_msg = message.reply_to_message
        if reply_msg:
            kicked_user_id = reply_msg.from_user.id
            kicked_user = await get_user(kicked_user_id)

            if not kicked_user:
                await message.reply("🛑 Пользователь не найден", parse_mode='markdown')
                return

            if kicked_user.clan_member == clan_id:
                await Users.filter(id=kicked_user_id).update(clan_member=None)
                victim_user_id = reply_msg.from_user.id
                victim_username = f'tg://user?id={victim_user_id}'
                await message.reply(
                    f'✅ Пользователь [{reply_msg.from_user.first_name}]({victim_username})* исключен из клана {clan_name}* пользователем [{message.from_user.first_name}](tg://user?id={message.from_user.id})',
                    parse_mode='markdown'
                )
            else:
                await message.reply("🛑 Этот пользователь не состоит в вашем клане", parse_mode='markdown')
        else:
            await message.reply("🛑 Вы должны ответить на сообщение пользователя, которого хотите исключить", parse_mode='markdown')
    else:
        await message.reply("🛑 Исключать из клана может только создатель", parse_mode='markdown')

@router.message(Command('clanleave'))
async def clanleave(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    clan_id = user.clan_member

    if clan_id == 0:
        await message.reply("🛑 Вы не состоите в клане", parse_mode='markdown')
        return

    try:
        clan = await Clans.get(id=clan_id)
    except Clans.DoesNotExist:
        await message.reply("🛑 Клан не найден", parse_mode='markdown')
        return

    clan_name = clan.clan_name
    clan_owner_id = int(clan.clan_owner_id)

    if user_id == clan_owner_id:
        await message.reply("🛑 Создатель клана не может его покинуть", parse_mode='markdown')
        return

    await Users.filter(id=user_id).update(clan_member=None)

    await message.reply(
        f'✅ *Вы покинули* клан *{clan_name}*',
        parse_mode='markdown'
    )

@router.message(Command('clandisband'))
async def clandisband(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    clan_id = user.clan_member
    try:
        clan = await Clans.get(id=clan_id)
    except:
        await message.reply("🛑 Вы не состоите в клане", parse_mode='markdown')
        return
    try:
        clan_owner_id = clan.clan_owner_id
        clan_name = clan.clan_name
    except AttributeError:
        await message.reply("🛑 Ошибка при получении информации о клане", parse_mode='markdown')
        return

    if clan_id > 0 and user_id == clan_owner_id:

        await Clans.filter(id=clan_id).delete()
        await Users.filter(clan_member=clan_id).update(clan_member=None)
        await Users.filter(clan_member=clan_id).update(clan_invite=None)
        await message.reply(f'✅ Вы распустили клан `{clan_name}`', parse_mode='markdown')
    elif clan_id > 0 and user_id != clan_owner_id:
        await message.reply(f"🛑 Вы не владелец клана!", parse_mode='markdown')

@router.callback_query(F.data.startswith("clan_accept:"))
async def clan_accept(callback_query: CallbackQuery):
    _, clan_id, invited_user_id = callback_query.data.split(":")
    user_id = callback_query.from_user.id

    if int(user_id) == int(invited_user_id):
        try:
            user = await Users.get(id=user_id)
            if user.clan_invite == int(clan_id):
                await Users.filter(id=user_id).update(clan_member=clan_id, clan_invite=0)
                await callback_query.message.edit_text("✅ Вы приняли приглашение в клан!")
            else:
                await callback_query.answer("Это приглашение не для вас!", show_alert=True)
        except DoesNotExist:
            await callback_query.answer("Пользователь не найден!", show_alert=True)

@router.callback_query(F.data.startswith("clan_decline:"))
async def clan_decline(callback_query: CallbackQuery):
    _, clan_id, invited_user_id = callback_query.data.split(":")
    user_id = callback_query.from_user.id

    if int(user_id) == int(invited_user_id):
        try:
            user = await Users.get(id=user_id)
            if user.clan_invite == int(clan_id):
                await Users.filter(id=user_id).update(clan_invite=0)
                await callback_query.message.edit_text("❌ Вы отклонили приглашение в клан!")
            else:
                await callback_query.answer("Это приглашение не для вас!", show_alert=True)
        except DoesNotExist:
            await callback_query.answer("Пользователь не найден!", show_alert=True)
