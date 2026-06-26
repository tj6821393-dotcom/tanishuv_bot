import os
from dotenv import load_dotenv

load_dotenv()

# Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Karta ma'lumotlari (to'lov uchun)
CARD_NUMBER = os.getenv("CARD_NUMBER")
CARD_OWNER = os.getenv("CARD_OWNER")

# Minimal to'lov summasi
MIN_PAYMENT = 5000

# Like limiti (12 soatda)
LIKE_LIMIT_FREE = 5
LIKE_LIMIT_PREMIUM = 20

# Narxlar (so'mda)
PRICE_CARD_SIMPLE = 5000      # Oddiy tanishuv
PRICE_CARD_SERIOUS = 15000     # Jiddiy tanishuv
PRICE_CARD_FAMILY = 40000      # Oila qurish
PRICE_LOCATION = 25000         # Lokatsiya kartochkasi
PRICE_HIDDEN = 10000           # Yashirin rejim (oylik)
PRICE_PREMIUM = 50000          # Premium (oylik)
PRICE_PREMIUM_VIP = 100000     # VIP (oylik)

# Story davomiyligi (soatda)
STORY_DURATION_FREE = 24
STORY_DURATION_VIP = 48