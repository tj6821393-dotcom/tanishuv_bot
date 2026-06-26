from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def shop_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💌 Oddiy tanishuv — 5 000 so'm", callback_data="buy_card_1")],
        [InlineKeyboardButton("💖 Jiddiy tanishuv — 10 000 so'm", callback_data="buy_card_2")],
        [InlineKeyboardButton("💍 Oila qurish niyati — 40 000 so'm", callback_data="buy_card_3")],
        [InlineKeyboardButton("📍 Lokatsiya kartochkasi — 25 000 so'm", callback_data="buy_card_4")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="shop_back")]
    ])

def my_cards_kb(cards):
    buttons = []
    for card in cards:
        buttons.append([InlineKeyboardButton(
            f"{card['emoji']} {card['name']} x{card['quantity']}",
            callback_data=f"use_card_{card['id']}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="shop_back")])
    return InlineKeyboardMarkup(buttons)