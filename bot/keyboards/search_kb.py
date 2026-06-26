from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def search_actions(user_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️ Yoqtirish", callback_data=f"like_{user_id}"),
            InlineKeyboardButton("💌 Xat yuborish", callback_data=f"send_card_{user_id}")
        ],
        [
            InlineKeyboardButton("➡️ Keyingisi", callback_data="next_user"),
            InlineKeyboardButton("🚫 Bloklash", callback_data=f"block_{user_id}")
        ]
    ])