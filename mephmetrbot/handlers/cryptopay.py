from aiocryptopay import AioCryptoPay, Networks
from mephmetrbot.handlers.models import Users, Invoices
from mephmetrbot.config import bot, ADMINS, RESTART_COMMAND, LOGS_CHAT_ID, CRYPTO_PAY_TOKEN
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command, CommandObject
import asyncio


router = Router()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user


@router.message(Command('buymef'))
async def buymef(message: Message):
    try:
        crypto = AioCryptoPay(token=CRYPTO_PAY_TOKEN, network=Networks.MAIN_NET)
        invoice = await crypto.create_invoice(
            asset='TON',
            amount=0.2,
            description='100 единиц игровой валюты',
            paid_btn_name='callback',
            paid_btn_url='https://help.crypt.bot/crypto-pay-api',
            allow_comments=True,
            allow_anonymous=True,
            expires_in='300'
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", url=invoice.bot_invoice_url)]
        ])
        await message.reply(
            '💰 Вы можете купить 100 гр. за 0.2 TON\n\n',
            parse_mode='markdown',
            disable_webpage_preview=True,
            reply_markup=keyboard
        )

        await asyncio.sleep(5)
        old_invoice = await crypto.get_invoices(invoice_ids=[invoice.invoice_id])
        status = old_invoice[0].status

        if status == 'paid':
            user = await get_user(message.from_user.id)
            user.drug_count = round(user.drug_count + 100, 1)
            await user.save()
            await bot.send_message(message.chat.id,
                                   "✅ Ты крут бро ты получил 100 грам грамм мефа, спасибо за поддержку!")

        return invoice.bot_invoice_url, invoice.invoice_id

    except Exception as e:
        await message.bot.send_message(LOGS_CHAT_ID, f"#SENDERROR\n\nuser_id: {user_id}\nerror: {str(e)}")