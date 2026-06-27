from telegram import Update
from telegram.ext import ContextTypes
from bot.database.queries import (
    get_user, get_all_cards, get_card, get_user_cards,
    add_user_card, use_user_card, deduct_balance, add_notification
)
from bot.keyboards.shop_kb import shop_menu, my_cards_kb
from bot.keyboards.payment_kb import card_response_kb

async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting!")
        return
    await update.message.reply_text(
        f"🛍️ Do'kon\n\n"
        f"💰 Balansingiz: {user['balance']:,} so'm\n\n"
        "Kartochka tanlang:",
        reply_markup=shop_menu()
    )

async def buy_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card_id = int(query.data.split('_')[-1])
    tg_id = update.effective_user.id
    card = await get_card(card_id)
    user = await get_user(tg_id)
    if not card:
        await query.message.reply_text("Kartochka topilmadi!")
        return
    if user['balance'] < card['price']:
        await query.message.reply_text(
            f"❌ Balans yetarli emas!\n\n"
            f"💰 Balansingiz: {user['balance']:,} so'm\n"
            f"💳 Kerakli summa: {card['price']:,} so'm\n\n"
            "Balansni to'ldiring: /payment"
        )
        return
    success = await deduct_balance(tg_id, card['price'])
    if success:
        await add_user_card(tg_id, card_id)
        await query.message.reply_text(
            f"✅ {card['emoji']} {card['name']} kartochkasi sotib olindi!\n\n"
            f"Ishlatish uchun: Qidiruvda foydalanuvchini topib 💌 tugmasini bosing."
        )

async def send_card_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    to_user_id = int(query.data.split('_')[-1])
    tg_id = update.effective_user.id
    user_cards = await get_user_cards(tg_id)
    if not user_cards:
        await query.message.reply_text(
            "❌ Sizda kartochka yo'q!\n\n"
            "Do'kondan sotib oling: /shop"
        )
        return
    context.user_data['send_card_to'] = to_user_id
    await query.message.reply_text(
        "Qaysi kartochkani yubormoqchisiz?",
        reply_markup=my_cards_kb(user_cards)
    )

async def use_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card_id = int(query.data.split('_')[-1])
    tg_id = update.effective_user.id
    to_user_id = context.user_data.get('send_card_to')
    if not to_user_id:
        await query.message.reply_text("Xatolik! Qaytadan urinib ko'ring.")
        return
    card = await get_card(card_id)
    sender = await get_user(tg_id)
    to_user = await get_user(to_user_id)
    if not card or not to_user:
        await query.message.reply_text("Xatolik yuz berdi!")
        return
    await use_user_card(tg_id, card_id)
    await context.bot.send_message(
        chat_id=to_user_id,
        text=f"{card['emoji']} Sizga #{sender['unique_id']} dan kartochka keldi!\n\n"
             f"💬 \"{card['text']}\"\n\n"
             f"Javob berasizmi?",
        reply_markup=card_response_kb(tg_id)
    )
    await add_notification(
        to_user_id,
        f"{card['emoji']} #{sender['unique_id']} sizga kartochka yubordi!"
    )
    await query.message.reply_text(
        f"✅ Kartochka yuborildi!\n"
        f"#{to_user['unique_id']} javob berishi kutilmoqda."
    )

async def handle_card_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from_user_id = int(query.data.split('_')[-1])
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    sender = await get_user(from_user_id)
    await context.bot.send_message(
        chat_id=from_user_id,
        text=f"✅ #{user['unique_id']} kartochkangizni qabul qildi!\n\n"
             f"🆔 Ularning ID: #{user['unique_id']}\n"
             f"Endi yozishingiz mumkin!"
    )
    await query.message.reply_text(
        f"✅ Rozilik bildirdingiz!\n"
        f"🆔 #{sender['unique_id']} endi siz bilan yozisha oladi."
    )

async def handle_card_deny(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ Rad etdingiz.")