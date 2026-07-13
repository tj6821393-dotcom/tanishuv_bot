from telegram import ReplyKeyboardMarkup

def main_menu():
    keyboard = [
        ["🔍 Qidiruv", "🆔 ID orqali"],
        ["👤 Profil", "💳 Balans"],
        ["⚙️ Sozlamalar"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)