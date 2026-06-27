from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from bot.database.queries import create_transaction, add_balance, get_balance
from bot.database.admin_queries import get_stats
from bot.keyboards.payment_kb import payment_menu
from bot.keyboards.admin_kb import payment_actions
from bot.config import CARD_NUMBER, CARD_OWNER, MIN_PAYMENT, ADMIN_ID

WAITING_AMOUNT, WAITING_CHECK = range(2)

async def show_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    balance = await get_balance(tg_id)
    await update.message.reply_text(
        f"💰 Balansingiz: {balance:,} so'm\n\n"
        "Balansni to'ldirish uchun quyidagi karta raqamiga pul o'tkazing:\n\n"
        f"🏦 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: {CARD_OWNER}\n\n"
        f"⚠️ Minimal summa: {MIN_PAYMENT:,} so'm\n\n"
        "To'lovdan keyin chek (screenshot) yuboring:",
        parse_mode='HTML',
        reply_markup=payment_menu()
    )
    return WAITING_CHECK

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
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=f"💰 Yangi to'lov so'rovi!\n\n"
                f"👤 Foydalanuvchi: {tg_id}\n"
                f"🆔 Tranzaksiya: #{tx['id']}",
        reply_markup=payment_actions(tx['id'], tg_id)
    )
    return ConversationHandler.END

def get_payment_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("💳 Balans to'ldirish"), show_payment)
        ],
        states={
            WAITING_CHECK: [MessageHandler(filters.PHOTO, receive_check)]
        },
        fallbacks=[]
    )