from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def search_actions(user_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️ Yoqtirish", callback_data=f"like_{user_id}"),
            InlineKeyboardButton("💌 Tanishish", callback_data=f"tanishish_{user_id}")
        ],
        [
            InlineKeyboardButton("📖 Story", callback_data=f"story_{user_id}"),
            InlineKeyboardButton("📸 Suratlar", callback_data=f"photos_{user_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Oldingi", callback_data="prev_user"),
            InlineKeyboardButton("➡️ Keyingi", callback_data="next_user")
        ]
    ])