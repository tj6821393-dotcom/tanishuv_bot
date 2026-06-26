from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Foydalanuvchi qidirish", callback_data="admin_search_user")],
        [InlineKeyboardButton("💰 Kutayotgan to'lovlar", callback_data="admin_payments")],
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚫 Shikoyatlar", callback_data="admin_complaints")]
    ])

def user_actions(telegram_id: int, is_blocked: bool):
    block_text = "✅ Blokdan chiqarish" if is_blocked else "🚫 Bloklash"
    block_data = f"admin_unblock_{telegram_id}" if is_blocked else f"admin_block_{telegram_id}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(block_text, callback_data=block_data)],
        [InlineKeyboardButton("💰 Balans qo'shish", callback_data=f"admin_add_balance_{telegram_id}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ])

def payment_actions(tx_id: int, telegram_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_confirm_{tx_id}_{telegram_id}")],
        [InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_reject_{tx_id}_{telegram_id}")]
    ])

def broadcast_targets():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Hammaga", callback_data="broadcast_all")],
        [InlineKeyboardButton("👨 Faqat erkaklarga", callback_data="broadcast_male")],
        [InlineKeyboardButton("👩 Faqat ayollarga", callback_data="broadcast_female")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ])