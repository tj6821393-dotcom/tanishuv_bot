from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    keyboard = [
        ["🗺️ Xarita", "🔍 Qidiruv"],
        ["🔔 Bildirishnomalar", "💌 Xabarlar"],
        ["🛍️ Do'kon", "👤 Profil"],
        ["📊 Statistika", "⚙️ Sozlamalar"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)