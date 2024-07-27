from pyCryptoPayAPI import pyCryptoPayAPI, pyCryptoPayException
from mephmetrbot.handlers.models import Users, Invoices
from mephmetrbot.config import bot, ADMINS, RESTART_COMMAND, LOGS_CHAT_ID, CRYPTO_PAY_TOKEN
from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command, CommandObject


client = pyCryptoPayAPI(api_token=CRYPTO_PAY_TOKEN, print_errors=True)
router = Router()

@router.message(Command('buymeph'))
async def buymeph_command(message: Message):
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
    await message.reply(f'💰 Вы можете купить 100 гр. за 0.2 TON\n\n[Нажмите здесь чтобы оплатить через CryptoBot]({invoice['pay_url']})\n\n[Нажмите здесь чтобы проверить оплату](https://t.me/mephmetrbot?start=checkinvoice-{invoice['invoice_id']})',parse_mode='markdown',disable_webpage_preview=True)
    await Invoices.create(invoice_id=invoice['invoice_id'], user_id=message.from_user.id, amount_ton=0.2, amount_meph=100, status='active')

async def checkinvoice(invoice_id, message: Message):
    invoices = client.get_invoices(
        "TON",
        status="paid",
        offset=0,
        count=10,
        return_items = True,
        invoice_ids = invoice_id
    )
    if invoices:
        try:
            invoice = await Invoices.get(invoice_id=invoice_id)
        except:
            await message.reply(f"❌ Этот счёт не найден")
            return
        await message.reply(f"✅ Ты крут бро ты получил {invoice.amount_meph} грамм мефа, спасибо за поддержку!")
        user = await Users.get(id=message.from_user.id)
        new_balance = round(user.drug_count + invoice.amount_meph, 1)
        user.drug_count = new_balance
        await user.save()
        await Invoices.filter(invoice_id=invoice_id).delete()
    else:
        await message.reply(f"❌ Оплата не найдена")
