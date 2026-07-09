from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def search_actions(user_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️ Yoqtirish", callback_data=f"like_{user_id}"),
            InlineKeyboardButton("💌 Tanishish", callback_data=f"tanishish_{user_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Oldingi", callback_data="prev_user"),
            InlineKeyboardButton("➡️ Keyingi", callback_data="next_user")
        ]
    ])