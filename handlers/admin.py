from aiogram import Router
from aiogram.types import Message
import os
import sys
from config import bot
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters.command import Command, CommandObject
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER
import sqlite3

router = Router()
conn = sqlite3.connect('handlers/mephmetrbot.db')
cursor = conn.cursor()

@router.message(Command('banuser'))
async def banuser_command(message: Message, command: CommandObject):
    if command.args:
        args = command.args.split(' ', maxsplit=1)[0]
    else:
        args = None
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
        elif args:
            bann_user_id = int(args)
            cursor.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (bann_user_id,))
            conn.commit()
        await message.reply(f"🛑 Пользователь с ID: `{bann_user_id}` заблокирован", parse_mode='markdown')
        await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"#BAN\n\nid: {bann_user_id}")
    elif is_admin == 0:
        await message.reply('🚨 MONKEY ALARM')

@router.message(Command('unbanuser'))
async def unbanuser_command(message: Message, command: CommandObject):
    if command.args:
        args = command.args.split(' ', maxsplit=1)[0]
    else:
        args = None
    
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
        elif args:
            bann_user_id = int(args)
            cursor.execute('UPDATE users SET is_banned = 0 WHERE id = ?', (bann_user_id,))
            conn.commit()
        else:
            bann_user_id = None
        
        if bann_user_id is not None:
            await message.reply(f"🛑 Пользователь с ID: `{bann_user_id}` разблокирован", parse_mode='markdown')
            await bot.send_message(os.environ.get('LOGS_CHAT_ID'), f"#UNBAN\n\nid: {bann_user_id}")
    elif is_admin == 0:
        await message.reply('🚨 MONKEY ALARM')


@router.message(Command('setdrugs'))
async def setdrugs_command(message: Message, command: CommandObject):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_admin = user[3]
    if is_admin == 1:
        args = command.args.split(' ', maxsplit=1)
        cursor.execute('UPDATE users SET drug_count = ? WHERE id = ?', (args[1],args[0]))
        conn.commit()
        await message.reply('✅')
    elif is_admin == 0:
        await message.reply('🚨 MONKEY ALARM')

@router.message(Command('usercount'))
async def usercount(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_admin = user[3]
    cursor.execute('SELECT COUNT(id) FROM users')
    user = cursor.fetchone()[0]
    if is_admin == 1:
        await message.reply(f'Количество пользователей в боте: {user}')
    else:
        await message.reply('🚨 MONKEY ALARM')

@router.message(Command('broadcast'))
async def cmd_broadcast_start(message: Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    is_admin = user[3] if user else 0
    if is_admin == 1:
        reply = message.reply_to_message
        if reply:
            media_type = reply.content_type
            result = cursor.execute('SELECT * FROM chats').fetchall()
            if not result:
                await message.answer('Нет доступных чатов для рассылки.')
                return
            if media_type == 'photo':
                caption = reply.caption or ""
                await message.answer('Начинаю рассылку.')
                for row in result:
                    chat_id = row[0]
                    try:
                        await message.bot.send_photo(chat_id, reply.photo[-1].file_id, caption=caption, parse_mode='Markdown')
                    except Exception as e:
                        log_chat_id = os.environ.get('LOGS_CHAT_ID', 'DEFAULT_LOGS_CHAT_ID')
                        await message.bot.send_message(log_chat_id, f"#SENDERROR\n\nchatid: {chat_id}\nerror: {str(e)}")
            elif media_type == 'video':
                caption = reply.caption or ""
                await message.answer('Начинаю рассылку.')
                for row in result:
                    chat_id = row[0]
                    try:
                        await message.bot.send_video(chat_id, reply.video.file_id, caption=caption, parse_mode='Markdown')
                    except Exception as e:
                        log_chat_id = os.environ.get('LOGS_CHAT_ID', 'DEFAULT_LOGS_CHAT_ID')
                        await message.bot.send_message(log_chat_id, f"#SENDERROR\n\nchatid: {chat_id}\nerror: {str(e)}")
            elif media_type == 'animation':
                caption = reply.caption or ""
                await message.answer('Начинаю рассылку.')
                for row in result:
                    chat_id = row[0]
                    try:
                        await message.bot.send_animation(chat_id, reply.animation.file_id, caption=caption, parse_mode='Markdown')
                    except Exception as e:
                        log_chat_id = os.environ.get('LOGS_CHAT_ID', 'DEFAULT_LOGS_CHAT_ID')
                        await message.bot.send_message(log_chat_id, f"#SENDERROR\n\nchatid: {chat_id}\nerror: {str(e)}")
            elif media_type == 'audio':
                caption = reply.caption or ""
                await message.answer('Начинаю рассылку.')
                for row in result:
                    chat_id = row[0]
                    try:
                        await message.bot.send_audio(chat_id, reply.audio.file_id, caption=caption, parse_mode='Markdown')
                    except Exception as e:
                        log_chat_id = os.environ.get('LOGS_CHAT_ID', 'DEFAULT_LOGS_CHAT_ID')
                        await message.bot.send_message(log_chat_id, f"#SENDERROR\n\nchatid: {chat_id}\nerror: {str(e)}")
            elif media_type == 'text':
                await message.answer('Начинаю рассылку.')
                for row in result:
                    chat_id = row[0]
                    try:
                        await message.bot.send_message(chat_id, reply.text, parse_mode='Markdown')
                    except Exception as e:
                        log_chat_id = os.environ.get('LOGS_CHAT_ID', 'DEFAULT_LOGS_CHAT_ID')
                        await message.bot.send_message(log_chat_id, f"#SENDERROR\n\nchatid: {chat_id}\nerror: {str(e)}")
            else:
                await message.answer('Не поддерживаемый тип медиа для рассылки.')
        else:
            await message.answer('Пожалуйста, ответьте на сообщение с медиафайлом для рассылки.')
    else:
        await message.answer('🚨 MONKEY ALARM!')



@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> MEMBER
    )
)
async def add_chat(event: ChatMemberUpdated):
    cursor.execute('INSERT INTO chats (chat_id, is_ads_enable) VALUES (?, ?)', (event.chat.id, 1))
    conn.commit()
    await bot.send_message(os.environ.get('LOGS_CHAT_ID'),f"<b>#NEW_CHAT</b><br>chat_id: <code>{event.chat.id}</code>",parse_mode='HTML')
    
