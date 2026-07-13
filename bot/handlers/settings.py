from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database.queries import get_user, update_user
from bot.keyboards.main_menu import main_menu

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    hidden_text = "👁 Ko'rinishni yoqish" if user['is_hidden'] else "🙈 Yashirin rejim"
    hidden_data = "settings_show" if user['is_hidden'] else "settings_hide"
    holat = "Yashirin" if user['is_hidden'] else "Ko'rinadi"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(hidden_text, callback_data=hidden_data)],
        [InlineKeyboardButton("🗑 Profilni o'chirish", callback_data="profile_delete")],
        [InlineKeyboardButton("🔙 Asosiy menyu", callback_data="settings_back")]
    ])
    await update.message.reply_text(
        f"⚙️ Sozlamalar\n\n"
        f"👁 Holat: {holat}",
        reply_markup=kb
    )

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    data = query.data

    if data == "settings_hide":
        await update_user(tg_id, is_hidden=True)
        await query.message.reply_text("🙈 Yashirin rejim yoqildi. Qidiruvda ko'rinmaysiz.")

    elif data == "settings_show":
        await update_user(tg_id, is_hidden=False)
        await query.message.reply_text("👁 Endi qidiruvda ko'rinasiz!")

    elif data == "profile_delete":
        from bot.keyboards.profile_kb import confirm_delete
        await query.message.reply_text(
            "Profilingiz o'chirilsinmi?\n"
            "Bu amalni qaytarib bo'lmaydi!",
            reply_markup=confirm_delete()
        )

    elif data == "profile_delete_confirm":
        from bot.database.queries import delete_user
        await delete_user(tg_id)
        await query.message.reply_text(
            "Profilingiz o'chirildi.\n"
            "Qayta ro'yxatdan o'tish uchun /start bosing."
        )

    elif data == "settings_back":
        await query.message.reply_text("Asosiy menyu:", reply_markup=main_menu())
