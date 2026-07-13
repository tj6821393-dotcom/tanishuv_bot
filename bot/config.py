import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

_admin_id = os.getenv("ADMIN_ID")
ADMIN_ID = int(_admin_id) if _admin_id else None

DATABASE_URL = os.getenv("DATABASE_URL")

CARD_NUMBER = os.getenv("CARD_NUMBER", "")
CARD_OWNER = os.getenv("CARD_OWNER", "")

MIN_PAYMENT = 5000

# Tanishish narxi
PRICE_TANISHISH = 15000
