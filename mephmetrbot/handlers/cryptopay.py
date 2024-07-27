from pyCryptoPayAPI import pyCryptoPayAPI, pyCryptoPayException
from mephmetrbot.handlers.models import Users, Invoices
from mephmetrbot.config import bot, ADMINS, RESTART_COMMAND, LOGS_CHAT_ID, CRYPTO_PAY_TOKEN
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command, CommandObject
import asyncio


client = pyCryptoPayAPI(api_token=CRYPTO_PAY_TOKEN, print_errors=True)
router = Router()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user

@router.message(Command('buymef'))
async def buymef(message: Message):
    try:
        invoice = client.create_invoice(
            "TON",
            0.2,
            description="100 единиц игровой валюты",
            paid_btn_name="callback",
            paid_btn_url="https://help.crypt.bot/crypto-pay-api",
            allow_comments=True,
            allow_anonymous=True,
            expires_in='300'
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Оплатить", url=f"{invoice['pay_url']}")
            ]
        ])
        await message.reply(f'💰 Вы можете купить 100 гр. за 0.2 TON\n\n', parse_mode='markdown', disable_webpage_preview=True, reply_markup=keyboard)

        await Invoices.create(invoice_id=invoice['invoice_id'], user_id=message.from_user.id, amount_ton=0.2, amount_meph=100, status='active')

        for _ in range(60):
            await asyncio.sleep(5)
            try:
                response = client.get_invoices(
                    "TON",
                    status="paid",
                    offset=0,
                    count=1,
                    return_items=True,
                    invoice_ids=[invoice['invoice_id']]
                )
                if response:
                    invoice_record = response[0]
                    await handle_paid_invoice(message.from_user.id, invoice_record)
                    break
            except Exception as e:
                await message.bot.send_message(LOGS_CHAT_ID, f"#SENDERROR\n\nuser_id: {user_id}\nerror: {str(e)}")

    except Exception as e:
        await message.bot.send_message(LOGS_CHAT_ID, f"#SENDERROR\n\nuser_id: {user_id}\nerror: {str(e)}")
ф
async def handle_paid_invoice(user_id, invoice):
    try:
        user = await get_user(user_id)
        new_balance = round(user.drug_count + 100, 1)
        user.drug_count = new_balance
        await user.save()
        await Invoices.filter(invoice_id=invoice['invoice_id']).delete()
        await bot.send_message(user_id, f"✅ Ты крут бро ты получил 100 грам грамм мефа, спасибо за поддержку!")
    except Exception as e:
        await message.bot.send_message(LOGS_CHAT_ID, f"#SENDERROR\n\nuser_id: {user_id}\nerror: {str(e)}")





# GOVNOCODE