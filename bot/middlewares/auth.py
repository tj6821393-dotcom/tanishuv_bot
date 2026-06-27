from telegram import Update
from telegram.ext import ContextTypes
from bot.database.queries import get_user

async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    user = await get_user(update.effective_user.id)
    if user and user['is_blocked']:
        await update.message.reply_text("🚫 Hisobingiz bloklangan.")
        return