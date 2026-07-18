from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from bot.database.queries import create_transaction, add_balance, get_balance
from bot.keyboards.main_menu import main_menu
from bot.config import CARD_NUMBER, CARD_OWNER, MIN_PAYMENT, ADMIN_ID

WAITING_AMOUNT, WAITING_CHECK = range(2)


async def show_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Balans sahifasi"""
    tg_id = update.effective_user.id
    balance = await get_balance(tg_id)
    
    text = (
        f"💳 Balans to'ldirish\n\n"
        f"💰 Joriy balansingiz: {balance:,} so'm\n\n"
        "⚠️ XIZMAT NARXLARI:\n"
        "💌 Tanishish: 15,000 so'm\n\n"
        f"🏦 KARTA: <code>{CARD_NUMBER}</code>\n"
        f"👤 EGASI: {CARD_OWNER}\n\n"
        f"Minimal to'ldirish: {MIN_PAYMENT:,} so'm\n\n"
        "Quyidagi tugmalardan birini tanlang:"
    )
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Summa kiritish", callback_data="pay_amount")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="pay_back")]
    ])
    
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=kb)
    return WAITING_AMOUNT


async def show_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summa kiritish"""
    kb = ReplyKeyboardMarkup([
        [KeyboardButton("50000"), KeyboardButton("100000"), KeyboardButton("200000")],
        [KeyboardButton("500000"), KeyboardButton("1000000")],
        [KeyboardButton("🔙 Orqaga")]
    ], resize_keyboard=True)
    
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "💵 Qancha to'ldirmoqchisiz?\n\n"
        "Tayyor summa tanlang yoki yozing:",
        reply_markup=kb
    )
    return WAITING_AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summa qabul qilish"""
    text = update.message.text
    
    if text == "🔙 Orqaga":
        await show_payment(update, context)
        return ConversationHandler.END
    
    try:
        amount = int(text.replace(' ', '').replace(',', ''))
        if amount < MIN_PAYMENT:
            await update.message.reply_text(
                f"❌ Minimal summa: {MIN_PAYMENT:,} so'm"
            )
            return WAITING_AMOUNT
        
        context.user_data['payment_amount'] = amount
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Chek yuborish", callback_data="pay_send_check")],
            [InlineKeyboardButton("🔙 Bekor qilish", callback_data="pay_back")]
        ])
        
        await update.message.reply_text(
            f"✅ Summa: {amount:,} so'm\n\n"
            f"🏦 {CARD_NUMBER} karta raqamiga o'tkazing.\n"
            f"👤 Egasi: {CARD_OWNER}\n\n"
            "To'lov qilgandan so'ng chekni yuboring:",
            reply_markup=kb
        )
        return WAITING_CHECK
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting!")
        return WAITING_AMOUNT


async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Payment callbacklar"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "pay_back":
        await query.message.reply_text("Asosiy menyu:", reply_markup=main_menu())
        return ConversationHandler.END
    
    if data == "pay_amount":
        return await show_amount_input(update, context)
    
    if data == "pay_send_check":
        await query.message.reply_text(
            "📸 Chekni rasm ko'rinishida yuboring:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Orqaga")]], resize_keyboard=True))
        return WAITING_CHECK


async def receive_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check qabul qilish"""
    text = update.message.text if update.message.text else ""
    
    if text == "🔙 Orqaga":
        await show_payment(update, context)
        return ConversationHandler.END
    
    if not update.message.photo:
        await update.message.reply_text("❌ Iltimos, chekni rasm ko'rinishida yuboring!")
        return WAITING_CHECK
    
    tg_id = update.effective_user.id
    file_id = update.message.photo[-1].file_id
    amount = context.user_data.get('payment_amount', 0)
    
    tx = await create_transaction(tg_id, amount, file_id)
    
    await update.message.reply_text(
        f"✅ Chek qabul qilindi!\n\n"
        f"💵 Summa: {amount:,} so'm\n"
        f"🆔 Tranzaksiya: #{tx['id']}\n\n"
        "Admin tekshirib, balansingizni 5-15 daqiqada to'ldiradi.",
        reply_markup=main_menu()
    )
    
    if ADMIN_ID:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_confirm_{tx['id']}_{tg_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_reject_{tx['id']}_{tg_id}")
        ]])
        
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=(
                f"💰 Yangi to'lov!\n\n"
                f"👤 Foydalanuvchi ID: {tg_id}\n"
                f"💵 Summa: {amount:,} so'm\n"
                f"🆔 Tranzaksiya: #{tx['id']}"
            ),
            reply_markup=kb
        )
    
    context.user_data['payment_amount'] = None
    return ConversationHandler.END


def get_payment_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("💳 Balans"), show_payment)
        ],
        states={
            WAITING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount),
                CallbackQueryHandler(handle_payment_callback)
            ],
            WAITING_CHECK: [
                MessageHandler(filters.PHOTO, receive_check),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_check),
                CallbackQueryHandler(handle_payment_callback)
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex("🔙 Orqaga"), show_payment),
            CallbackQueryHandler(handle_payment_callback, pattern="^pay_")
        ]
    )
