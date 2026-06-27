import time
from telegram import Update
from telegram.ext import ContextTypes

user_last_action = {}
THROTTLE_TIME = 1

async def throttle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    tg_id = update.effective_user.id
    now = time.time()
    last = user_last_action.get(tg_id, 0)
    if now - last < THROTTLE_TIME:
        await update.message.reply_text("⏳ Biroz kuting...")
        return
    user_last_action[tg_id] = now