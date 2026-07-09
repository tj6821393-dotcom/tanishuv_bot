from telegram import ReplyKeyboardMarkup

def main_menu():
    keyboard = [
        ["🔍 Qidiruv", "🔍 ID bilan qidiruv"],
        ["👤 Profil", "🔔 Bildirishnomalar"],
        ["💳 Balans to'ldirish", "📊 Statistika"],
        ["⚙️ Sozlamalar"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)