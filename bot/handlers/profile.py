from telegram import Update
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
    text = (
        "👤 Sizning profilingiz\n\n"
        f"🆔 #{user['unique_id']}\n"
        f"👤 Ism: {user['full_name']}\n"
        f"🎂 Yosh: {user['age']}\n"
        f"📍 Shahar: {user['city']}\n"
        f"📱 Telefon: {user['phone_number'] or \"Ko'rsatilmagan\"}\n\n"
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

    elif data == "profile_delete":
        await query.message.reply_text(
            "Profilingiz o'chirilsinmi?\n"
            "Bu amalni qaytarib bo'lmaydi!",
            reply_markup=confirm_delete()
        )

    elif data == "profile_delete_confirm":
        await delete_user(update.effective_user.id)
        await query.message.reply_text(
            "Profilingiz o'chirildi.\n"
            "Qayta ro'yxatdan o'tish uchun /start bosing."
        )

    elif data == "profile_back":
        await query.message.reply_text("Asosiy menyu:", reply_markup=main_menu())

    elif data.startswith("edit_"):
        field = data.split('_')[1]
        fields = {
            'photos': 'Yangi rasm yuboring:',
            'name': 'Yangi ismingizni kiriting:',
            'city': 'Yangi shahringizni kiriting:'
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
