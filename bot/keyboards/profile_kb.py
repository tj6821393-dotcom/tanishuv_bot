from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def profile_actions():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Story qoshish", callback_data="profile_bio")],
        [InlineKeyboardButton("✏️ Tahrirlash", callback_data="profile_edit")],
        [InlineKeyboardButton("🗑 O'chirish", callback_data="profile_delete")]
    ])

def profile_edit_fields():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Rasm", callback_data="edit_photos")],
        [InlineKeyboardButton("👤 Ism", callback_data="edit_name")],
        [InlineKeyboardButton("📖 Story", callback_data="edit_bio")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="profile_back")]
    ])

def confirm_delete():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ha, o'chirish", callback_data="profile_delete_confirm")],
        [InlineKeyboardButton("❌ Yoq", callback_data="profile_back")]
    ])