from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database.queries import get_user, update_user

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    hidden_text = "👁 Ko'rinishni yoqish" if user['is_hidden'] else "🙈 Yashirin rejim"
    hidden_data = "settings_show" if user['is_hidden'] else "settings_hide"
    holat = "Yashirin" if user['is_hidden'] else "Ko'rinadi"
    lokatsiya = "Ulangan" if user['latitude'] else "Ulanmagan"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(hidden_text, callback_data=hidden_data)],
        [InlineKeyboardButton("📍 Lokatsiyani yangilash", callback_data="settings_location")],
        [InlineKeyboardButton("🗑 Profilni o'chirish", callback_data="profile_delete")]
    ])
    await update.message.reply_text(
        f"⚙️ Sozlamalar\n\n"
        f"👁 Holat: {holat}\n"
        f"📍 Lokatsiya: {lokatsiya}",
        reply_markup=kb
    )

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    data = query.data

    if data == "settings_hide":
        await update_user(tg_id, is_hidden=True)
        await query.message.reply_text("🙈 Yashirin rejim yoqildi. Xaritada ko'rinmaysiz.")

    elif data == "settings_show":
        await update_user(tg_id, is_hidden=False)
        await query.message.reply_text("👁 Endi xaritada ko'rinasiz!")

    elif data == "settings_location":
        from telegram import KeyboardButton, ReplyKeyboardMarkup
        kb = ReplyKeyboardMarkup([
            [KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]
        ], resize_keyboard=True, one_time_keyboard=True)
        await query.message.reply_text("📍 Yangi lokatsiyangizni yuboring:", reply_markup=kb)
        context.user_data['update_location'] = True

async def handle_new_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('update_location') and update.message.location:
        await update_user(
            update.effective_user.id,
            latitude=update.message.location.latitude,
            longitude=update.message.location.longitude
        )
        await update.message.reply_text("✅ Lokatsiya yangilandi!")
        context.user_data['update_location'] = False
