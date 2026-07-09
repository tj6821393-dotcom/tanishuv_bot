from telegram import ReplyKeyboardMarkup

def main_menu():
    keyboard = [
        ["🔍 Qidiruv", "👤 Profil"],
        ["🔔 Bildirishnomalar", "💌 Xabarlar"],
        ["💳 Balans to'ldirish", "📊 Statistika"],
        ["⚙️ Sozlamalar"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)