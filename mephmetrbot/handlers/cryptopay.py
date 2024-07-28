from aiocryptopay import AioCryptoPay, Networks
from mephmetrbot.handlers.models import Users, Invoices
from mephmetrbot.config import bot, CRYPTO_PAY_TOKEN, RUB_PER_MEPH
from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.filters.command import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F

crypto = AioCryptoPay(token=CRYPTO_PAY_TOKEN, network=Networks.MAIN_NET)

router = Router()

async def get_user(user_id):
    user, _ = await Users.get_or_create(id=user_id)
    return user


@router.message(Command('buymeph'))
async def buymef(message: Message, command: CommandObject):

    args = command.args
    if args:
        value = command.args.split(' ', maxsplit=1)[0]
    else:
        await message.reply(f'❌ Укажите насколько рублей,  гр. хотите купить\n'
                            f'Пример: <code>/buymeph 100</code>\n\n'
                            f'Курс: <code>1 гр. = {float(RUB_PER_MEPH)} RUB</code>', parse_mode='html')
        return
    invoice_amount = int(int(value) * float(RUB_PER_MEPH))
    invoice = await crypto.create_invoice(
        amount=invoice_amount,
        fiat='RUB',
        currency_type='fiat',
        description=f'{value} единиц игровой валюты',
        allow_comments=True,
        allow_anonymous=True,
        expires_in='300'
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='💰 Оплатить', url=invoice.bot_invoice_url),
        InlineKeyboardButton(text='Проверить оплату', callback_data=f"checkinvoice_{invoice.invoice_id}_{value}")
    )

    await message.reply(
        f'💰 Вы можете купить {value} гр. за {invoice_amount} RUB через CryptoBot\n\n',
        parse_mode='markdown',
        disable_webpage_preview=True,
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("checkinvoice_"))
async def checkinvoice_callback(callback: CallbackQuery):
    data = callback.data.split("_")
    invoice_id = data[1]
    value = data[2]
    try:
        invoice_data = await Invoices.get(invoice_id=invoice_id)
        status = invoice_data.status
        if status == 'paid':
            await callback.answer()
            return
    except:
        invoice = await crypto.get_invoices(invoice_ids=invoice_id)
        status = invoice[0].status
        if status == 'paid':
            user = await get_user(callback.message.from_user.id)
            user.drug_count = round(user.drug_count + int(value), 1)
            await user.save()
            await bot.send_message(callback.message.chat.id,
                                    f"✅ Ты крут бро ты получил {value} грам грамм мефа, спасибо за поддержку!")
            await Invoices.create(invoice_id=invoice_id, status='paid')
            await callback.answer()
        else:
            await callback.answer('❌ Оплата не найдена!')
        return
