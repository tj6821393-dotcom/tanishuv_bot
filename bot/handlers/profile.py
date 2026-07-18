from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.queries import get_user, update_user, delete_user
from bot.keyboards.profile_kb import profile_actions, profile_edit_fields, confirm_delete
from bot.keyboards.main_menu import main_menu

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Profile view handler - updated for clean deploy
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    photos = user['photos'].split(',') if user['photos'] else []
    balance = f"{user['balance']:,}"
    bio = user.get('bio') if user.get('bio') else "Story yoq"
    
    text = (
        "👤 Sizning profilingiz\n\n"
        f"🆔 #{user['unique_id']}\n"
        f"👤 Ism: {user['full_name']}\n"
        f"🎂 Yosh: {user['age']}\n"
        f"📍 Shahar: {user.get('city') or 'Lokatsiya'}\n"
        f"📱 Telefon: {user.get('phone_number') or 'Korsatilmagan'}\n\n"
        f"📖 Story: {bio}\n\n"
        f"💰 Balans: {balance} so'm"
    )
    if photos:
        await update.message.reply_photo(
            photo=photos[0],
            caption=text,
            reply_markup=profile_actions()
        )
    else:
        await update.message.reply_text(text, reply_markup=profile_actions())

async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "profile_edit":
        await query.message.reply_text(
            "Nimani o'zgartirmoqchisiz?",
            reply_markup=profile_edit_fields()
        )
    
    elif data == "profile_bio":
        await query.message.reply_text(
            "📖 O'zingiz haqingizda yozing:\n\n"
            "Bu story sifatida boshqa foydalanuvchilarga ko'rsatiladi.\n"
            "Masalan: 'Men toshkentlikman, IT sohasida ishlayman'"
        )
        context.user_data['edit_field'] = 'bio'
        return

    elif data == "profile_delete":
        await query.message.reply_text(
            "Profilingiz o'chirilsinmi?\n"
            "Bu amalni qaytarib bo'lmaydi!",
            reply_markup=confirm_delete()
        )

    elif data == "profile_delete_confirm":
        await delete_user(update.effective_user.id)
        await query.message.reply_text(
            "✅ Profil o'chirildi.\n"
            "Qayta ro'yxatdan o'tish uchun /start bosing."
        )

    elif data == "profile_back":
        await query.message.reply_text("Asosiy menyu:", reply_markup=main_menu())

    elif data.startswith("edit_"):
        field = data.split('_')[1]
        
        if field == 'phone':
            kb = ReplyKeyboardMarkup([
                [KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]
            ], resize_keyboard=True, one_time_keyboard=True)
            await query.message.reply_text(
                "📱 Telefon raqamingizni ulashing:",
                reply_markup=kb
            )
            context.user_data['edit_field'] = 'phone'
            return
        
        fields = {
            'photos': 'Yangi rasm yuboring:',
            'name': 'Yangi ismingizni kiriting:',
            'bio': 'Story yozing:'
        }
        context.user_data['edit_field'] = field
        await query.message.reply_text(fields.get(field, "Ma'lumot kiriting:"))

async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get('edit_field')
    if not field:
        return
    tg_id = update.effective_user.id

    if field == 'photos':
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            await update_user(tg_id, photos=file_id)
            await update.message.reply_text("✅ Rasm yangilandi!")
            context.user_data['edit_field'] = None
    
    elif field == 'phone':
        contact = update.message.contact
        if not contact:
            await update.message.reply_text("❌ Iltimos, kontakt tugmasini bosing!")
            return
        
        # Kontakt egasi tekshirish - faqat o'z kontakti qabul qilish
        if contact.user_id != tg_id:
            await update.message.reply_text("❌ Faqat o'zingizning kontaktingizni ulashing!")
            return
        
        await update_user(tg_id, phone_number=contact.phone_number)
        await update.message.reply_text(f"✅ Telefon yangilandi: {contact.phone_number}")
        context.user_data['edit_field'] = None
    
    elif field == 'bio':
        await update_user(tg_id, bio=update.message.text)
        await update.message.reply_text("✅ Story yangilandi!")
        context.user_data['edit_field'] = None
    else:
        db_fields = {
            'name': 'full_name',
            'city': 'city'
        }
        db_field = db_fields.get(field)
        if db_field:
            await update_user(tg_id, **{db_field: update.message.text})
            await update.message.reply_text("✅ Ma'lumot yangilandi!")
            context.user_data['edit_field'] = None
