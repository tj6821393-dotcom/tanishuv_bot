from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database.queries import get_user, get_messages, send_message_db
from bot.database.admin_queries import get_user_by_unique_id
from bot.handlers.search import show_user_profile

async def show_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🆔 ID orqali qidiruv - odamni ID bilan qidirish"""
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    await update.message.reply_text(
        "🆔 ID orqali qidiruv\n\n"
        "Qidirish uchun foydalanuvchi ID sini yuboring:\n"
        "(Masalan: TAN-00547)"
    )
    context.user_data['search_by_id'] = True

async def handle_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    
    # ID orqali qidiruv
    if context.user_data.get('search_by_id'):
        unique_id = update.message.text.replace('#', '').strip().upper()
        target = await get_user_by_unique_id(unique_id)
        
        if not target:
            await update.message.reply_text(
                f"❌ #{unique_id} ID li foydalanuvchi topilmadi!\n\n"
                "ID ni to'g'ri kiritganingizga ishonch hosil qiling."
            )
            return
        
        if target['telegram_id'] == tg_id:
            await update.message.reply_text("❌ O'zingizni qidira olmaysiz!")
            return
        
        context.user_data['search_by_id'] = None
        context.user_data['search_target_id'] = target['telegram_id']
        
        current_user = await get_user(tg_id)
        await show_user_profile(update, context, target, current_user)
        return
    
    # Match bo'lgandan keyin xabar yuborish
    action = context.user_data.get('messages_action')

    if action == 'waiting_id':
        unique_id = update.message.text.replace('#', '').strip().upper()
        target = await get_user_by_unique_id(unique_id)
        if not target:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi!")
            return
        context.user_data['message_to'] = target['telegram_id']
        context.user_data['messages_action'] = 'waiting_text'
        await update.message.reply_text(
            f"👤 {target['full_name']}\n\n"
            "Xabaringizni yozing:"
        )

    elif action == 'waiting_text':
        to_user = context.user_data.get('message_to')
        if not to_user:
            return
        sender = await get_user(tg_id)
        await send_message_db(tg_id, to_user, update.message.text)
        await update.message.reply_text("✅ Xabar yuborildi!")
        await context.bot.send_message(
            chat_id=to_user,
            text=f"💌 #{sender['unique_id']} dan yangi xabar:\n\n"
                 f"{update.message.text}"
        )
        context.user_data['messages_action'] = None
        context.user_data['message_to'] = None