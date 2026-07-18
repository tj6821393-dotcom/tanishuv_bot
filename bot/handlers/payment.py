from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from bot.database.queries import create_transaction, add_balance, get_balance
from bot.keyboards.payment_kb import payment_menu
from bot.keyboards.admin_kb import payment_actions
from bot.config import CARD_NUMBER, CARD_OWNER, MIN_PAYMENT, ADMIN_ID

WAITING_AMOUNT, WAITING_CHECK = range(2)

async def show_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    balance = await get_balance(tg_id)
    await update.message.reply_text(
        f"💳 Balans to'ldirish\n\n"
        f"💰 Joriy balansingiz: {balance:,} so'm\n\n"
        "⚠️ DIQQAT - Narxlar:\n"
        "💌 Tanishish: 15,000 som\n"

        f"🏦 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: {CARD_OWNER}\n\n"
        f"Minimal to'ldirish: {MIN_PAYMENT:,} som\n\n"
        "To'lovdan keyin chekni shu yerga yuboring:",
        parse_mode='HTML',
        reply_markup=payment_menu()
    )
    return WAITING_AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.replace(' ', '').replace(',', ''))
        if amount < MIN_PAYMENT:
            await update.message.reply_text(
                f"❌ Minimal summa: {MIN_PAYMENT:,} so'm\nKattaroq summa kiriting:"
            )
            return WAITING_AMOUNT
        context.user_data['payment_amount'] = amount
        await update.message.reply_text(
            f"✅ Summa: {amount:,} so'm\n\n"
            "Endi to'lov chekini (screenshot) yuboring:"
        )
        return WAITING_CHECK
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting (masalan: 10000):")
        return WAITING_AMOUNT

async def receive_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Iltimos, chekni rasm ko'rinishida yuboring!")
        return WAITING_CHECK
    tg_id = update.effective_user.id
    file_id = update.message.photo[-1].file_id
    amount = context.user_data.get('payment_amount', 0)
    tx = await create_transaction(tg_id, amount, file_id)
    await update.message.reply_text(
        "✅ Chek qabul qilindi!\n"
        "Admin tekshirib, balansingizni to'ldiradi.\n"
        "Odatda 5-15 daqiqa ichida."
    )
    if ADMIN_ID:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=(
                f"💰 Yangi to'lov so'rovi!\n\n"
                f"👤 Foydalanuvchi: {tg_id}\n"
                f"💵 Summa: {amount:,} so'm\n"
                f"🆔 Tranzaksiya: #{tx['id']}"
            ),
            reply_markup=payment_actions(tx['id'], tg_id)
        )
    return ConversationHandler.END

def get_payment_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("💳 Balans to'ldirish"), show_payment)
        ],
        states={
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)],
            WAITING_CHECK: [MessageHandler(filters.PHOTO, receive_check)]
        },
        fallbacks=[]
    )
