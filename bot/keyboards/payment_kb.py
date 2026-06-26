from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def payment_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Balans to'ldirish", callback_data="payment_topup")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="payment_back")]
    ])

def location_perm_kb(from_user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Doimiy ruxsat", callback_data=f"loc_perm_permanent_{from_user_id}")],
        [InlineKeyboardButton("⏳ Bir martalik (1 soat)", callback_data=f"loc_perm_once_{from_user_id}")],
        [InlineKeyboardButton("❌ Rozi emasman", callback_data=f"loc_perm_deny_{from_user_id}")]
    ])

def card_response_kb(from_user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Roziman", callback_data=f"card_accept_{from_user_id}")],
        [InlineKeyboardButton("❌ Rozi emasman", callback_data=f"card_deny_{from_user_id}")]
    ])