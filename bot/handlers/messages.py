from telegram import Update
from telegram.ext import ContextTypes
from bot.database.queries import get_user, get_messages, send_message_db, get_balance, deduct_balance
from bot.database.admin_queries import get_user_by_unique_id

PRICE_TANISHISH = 15000


async def show_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ID bilan qidiruv - xabarlar o'rniga"""
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    await update.message.reply_text(
        "🔍 ID bilan qidiruv\n\n"
        "Yozmoqchi bo'lgan odamning ID sini yuboring:\n"
        "(Masalan: TAN-00547)"
    )
    context.user_data['messages_action'] = 'waiting_id'


async def handle_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    action = context.user_data.get('messages_action')

    if action == 'waiting_id':
        unique_id = update.message.text.replace('#', '').strip()
        target = await get_user_by_unique_id(unique_id)
        if not target:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi!")
            return
        context.user_data['message_to'] = target['telegram_id']
        context.user_data['target_user'] = target
        context.user_data['messages_action'] = 'waiting_text'
        
        # Tanishish narxi
        balance = await get_balance(tg_id)
        await update.message.reply_text(
            f"👤 {target['full_name']}, {target['age']} yosh\n"
            f"🆔 #{target['unique_id']}\n\n"
            f"💰 Tanishish narxi: {PRICE_TANISHISH:,} so'm\n"
            f"💳 Sizning balansingiz: {balance:,} so'm\n\n"
            "Xabaringizni yozing:"
        )

    elif action == 'waiting_text':
        to_user = context.user_data.get('message_to')
        if not to_user:
            return
        sender = await get_user(tg_id)
        target = context.user_data.get('target_user')
        
        # Balansni tekshirish
        balance = await get_balance(tg_id)
        if balance < PRICE_TANISHISH:
            await update.message.reply_text(
                f"❌ Balans yetarli emas!\n"
                f"💳 Kerakli summa: {PRICE_TANISHISH:,} so'm\n"
                f"💰 Sizning balansingiz: {balance:,} so'm\n\n"
                "Balansni to'ldiring: 💳 Balans to'ldirish"
            )
            context.user_data['messages_action'] = None
            context.user_data['message_to'] = None
            context.user_data['target_user'] = None
            return
        
        # Pul yechish
        await deduct_balance(tg_id, PRICE_TANISHISH)
        
        # Xabar yuborish
        await send_message_db(tg_id, to_user, update.message.text)
        
        # Guruh yaratish
        try:
            # Sender va recipient username/phone
            sender_contact = f"@{sender.get('username', 'unknown')}" if sender.get('username') else sender.get('phone_number', '')
            target_contact = f"@{target.get('username', 'unknown')}" if target.get('username') else target.get('phone_number', '')
            
            # Guruh yaratish
            group = await context.bot.create_group_chat(
                chat_title=f"💬 Tanishuv: {sender['full_name']} & {target['full_name']}",
                description=f"Tanishish uchun yaratilgan guruh\n\n"
                           f"👤 {sender['full_name']}: {sender_contact}\n"
                           f"👤 {target['full_name']}: {target_contact}"
            )
            
            # Guruhga yigitni qo'shish
            await context.bot.add_chat_member(group.chat_id, tg_id)
            # Guruhga qizni qo'shish
            await context.bot.add_chat_member(group.chat_id, to_user)
            
            # Guruhga xabar yuborish
            await context.bot.send_message(
                chat_id=group.chat_id,
                text=f"🎉 Guruh yaratildi!\n\n"
                     f"👤 {sender['full_name']}: {sender_contact}\n"
                     f"👤 {target['full_name']}: {target_contact}\n\n"
                     f"💬 Bu yerda tanishishingiz mumkin!"
            )
            
            await update.message.reply_text(
                f"✅ Tanishish tasdiqlandi!\n\n"
                f"💰 {PRICE_TANISHISH:,} so'm yechildi\n"
                f"💬 Guruh yaratildi!\n\n"
                f"📎 Kontaktlar:\n"
                f"👤 {sender['full_name']}: {sender_contact}\n"
                f"👤 {target['full_name']}: {target_contact}"
            )
            
            # Qizga xabar
            await context.bot.send_message(
                chat_id=to_user,
                text=f"💌 #{sender['unique_id']} ({sender['full_name']}) siz bilan tanishdi!\n\n"
                     f"💬 Guruh yaratildi: {group.title}\n\n"
                     f"📎 {sender['full_name']}: {sender_contact}"
            )
            
        except Exception as e:
            # Guruh yaratishda xato bo'lsa, oddiy xabar yuborish
            await update.message.reply_text(
                f"✅ Xabar yuborildi!\n"
                f"💰 {PRICE_TANISHISH:,} so'm yechildi"
            )
            await context.bot.send_message(
                chat_id=to_user,
                text=f"💌 #{sender['unique_id']} ({sender['full_name']}) dan xabar:\n\n"
                     f"{update.message.text}\n\n"
                     f"📎 Kontakt: {sender_contact}"
            )
        
        context.user_data['messages_action'] = None
        context.user_data['message_to'] = None
        context.user_data['target_user'] = None