import os
from mephmetrbot.config import bot, ADMINS, RESTART_COMMAND, LOGS_CHAT_ID
from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters.command import Command, CommandObject
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER
from mephmetrbot.handlers.models import Users, Chats
from tortoise.exceptions import DoesNotExist

router = Router()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user

async def get_all_users() -> list:
    return await Users.all().values_list('id', flat=True)

async def get_all_chats() -> list:
    return await Chats.all().values_list('chat_id', flat=True)

@router.message(Command('getadmin'))
async def getadmin_command(message: Message):
    if str(message.from_user.id) in ADMINS:
        target_user = await Users.get(id=message.from_user.id)
        target_user.is_admin = 1
        await target_user.save()
        await message.reply('✅')
    else:
        return


@router.message(Command('restartbot'))
async def restartbot_command(message: Message):
    user = await get_user(message.from_user.id)
    if user.is_admin:
        os.system(RESTART_COMMAND)
    else:
        await message.reply('🚨 У вас нет прав для выполнения этой команды.')

@router.message(Command('banuser'))
async def banuser_command(message: Message, command: CommandObject):
    if command.args:
        args = command.args.split(' ', maxsplit=1)[0]
    else:
        args = None

    if message.reply_to_message:
        ban_user_id = message.reply_to_message.from_user.id
    elif args:
        try:
            ban_user_id = int(args)
        except ValueError:
            await message.reply("🚨 Неверный формат ID пользователя.")
            return
    else:
        await message.reply("🚨 Не указан ID пользователя для бана.")
        return

    user = await get_user(message.from_user.id)
    if user.is_admin:
        ban_user = await get_user(ban_user_id)
        if ban_user:
            if ban_user.is_banned == 1:
                await message.reply(f"🔍 Пользователь с ID: `{ban_user_id}` уже заблокирован.", parse_mode='markdown')
                return
            ban_user.is_banned = 1
            await ban_user.save()
            await message.reply(f"🛑 Пользователь с ID: `{ban_user_id}` заблокирован.", parse_mode='markdown')
            await bot.send_message(LOGS_CHAT_ID, f"#BAN\n\nid: {ban_user_id}")
        else:
            await message.reply("🚨 Пользователь не найден.")
    else:
        await message.reply('🚨 У вас нет прав для выполнения этой команды.')

@router.message(Command('unbanuser'))
async def unbanuser_command(message: Message, command: CommandObject):
    if command.args:
        args = command.args.split(' ', maxsplit=1)[0]
    else:
        args = None

    if message.reply_to_message:
        ban_user_id = message.reply_to_message.from_user.id
    elif args:
        try:
            ban_user_id = int(args)
        except ValueError:
            await message.reply("🚨 Неверный формат ID пользователя.")
            return
    else:
        await message.reply("🚨 Не указан ID пользователя для разблокировки.")
        return

    user = await get_user(message.from_user.id)
    if user.is_admin:
        ban_user = await get_user(ban_user_id)
        if ban_user:
            if ban_user.is_banned == 0:
                await message.reply(f"🔍 Пользователь с ID: `{ban_user_id}` не в бане.", parse_mode='markdown')
                return

            ban_user.is_banned = 0
            await ban_user.save()
            updated_ban_user = await get_user(ban_user_id)
            if updated_ban_user.is_banned == 0:
                await message.reply(f"✅ Пользователь с ID: `{ban_user_id}` разблокирован.", parse_mode='markdown')
                await bot.send_message(LOGS_CHAT_ID, f"#UNBAN\n\nid: {ban_user_id}")
        else:
            await message.reply("🚨 Пользователь не найден")
    else:
        await message.reply('🚨 У вас нет прав для выполнения этой команды.')


@router.message(Command('setdrugs'))
async def setdrugs_command(message: Message, command: CommandObject):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user and user.is_admin:
        target_id = None
        drug_count = None
        args = command.args.split(' ', maxsplit=1)

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            if args:
                drug_count = args[0]
        elif len(args) == 2:
            target_id, drug_count = args[0], args[1]

        if drug_count and drug_count.isdigit():
            drug_count = int(drug_count)

            # Определите ID бота
            bot_id = 1
            # Проверьте, если target_id это ID бота в Telegram
            if str(target_id) == '7005935644':
                target_id = bot_id

            try:
                target_user = await Users.get(id=target_id)
                target_user.drug_count = drug_count
                await target_user.save()
                await message.reply('✅')
                await bot.send_message(
                    LOGS_CHAT_ID,
                    f"<b>#SETDRUGS</b>\n\nuser_id_receiver: <code>{target_id}</code>\nuser_id_sender: <code>{user_id}</code>\ndrug_count: <code>{drug_count}</code>\n\n<a href='tg://user?id={user_id}'>mention sender</a>\n<a href='tg://user?id={target_id}'>mention receiver</a>",
                    parse_mode='HTML'
                )
            except DoesNotExist:
                await message.reply(f'❌ Пользователь с ID {target_id} не найден.')
        else:
            await message.reply(
                '❌ Неверный формат команды. Используйте /setdrugs [число] или используйте в ответ на сообщение.')
    else:
        await message.reply('🚨 У вас нет прав для выполнения этой команды.')

@router.message(Command('usercount'))
async def usercount(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    user_count = await Users.all().count()
    if user.is_admin == 1:
        await message.reply(f'Количество пользователей в боте: {user_count}')
    else:
        await message.reply('🚨 У вас нет прав для выполнения этой команды.')

@router.message(Command('broadcast'))
async def cmd_broadcast_start(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if user and user.is_admin:
        reply = message.reply_to_message

        if reply:
            media_type = reply.content_type
            chats = await get_all_chats()
            users = await get_all_users()

            caption = reply.caption or ""
            await message.answer('Начинаю рассылку.')

            for chat_id in chats:
                try:
                    if media_type == 'photo':
                        await message.bot.send_photo(chat_id, reply.photo[-1].file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'video':
                        await message.bot.send_video(chat_id, reply.video.file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'animation':
                        await message.bot.send_animation(chat_id, reply.animation.file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'audio':
                        await message.bot.send_audio(chat_id, reply.audio.file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'text':
                        await message.bot.send_message(chat_id, reply.text, parse_mode='Markdown')
                    else:
                        await message.answer('Не поддерживаемый тип медиа для рассылки.')
                except Exception as e:
                    await message.bot.send_message(LOGS_CHAT_ID, f"#SENDERROR\n\nchatid: {chat_id}\nerror: {str(e)}")

            for user_id in users:
                try:
                    if media_type == 'photo':
                        await message.bot.send_photo(user_id, reply.photo[-1].file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'video':
                        await message.bot.send_video(user_id, reply.video.file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'animation':
                        await message.bot.send_animation(user_id, reply.animation.file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'audio':
                        await message.bot.send_audio(user_id, reply.audio.file_id, caption=caption, parse_mode='Markdown')
                    elif media_type == 'text':
                        await message.bot.send_message(user_id, reply.text, parse_mode='Markdown')
                    else:
                        await message.answer('Не поддерживаемый тип медиа для рассылки.')
                except Exception as e:
                    await message.bot.send_message(LOGS_CHAT_ID, f"#SENDERROR\n\nuser_id: {user_id}\nerror: {str(e)}")
        else:
            await message.answer('Пожалуйста, ответьте на сообщение с медиафайлом для рассылки.')
    else:
        await message.reply('🚨 У вас нет прав для выполнения этой команды.')



@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> MEMBER
    )
)
async def add_chat(event: ChatMemberUpdated):
    if event.new_chat_member.user.is_bot:
        chat_id = event.chat.id
        await Chats.get_or_create(chat_id=chat_id, defaults={'is_ads_enable': True})
        await bot.send_message(LOGS_CHAT_ID, f"<b>#NEW_CHAT</b>\n\nchat_id: <code>{chat_id}</code>", parse_mode='HTML')
