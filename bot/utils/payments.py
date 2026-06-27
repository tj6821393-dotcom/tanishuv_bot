from bot.config import CARD_NUMBER, CARD_OWNER, MIN_PAYMENT

def get_payment_info() -> str:
    return (
        f"💳 To'lov ma'lumotlari:\n\n"
        f"🏦 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: {CARD_OWNER}\n"
        f"⚠️ Minimal: {MIN_PAYMENT:,} so'm"
    )