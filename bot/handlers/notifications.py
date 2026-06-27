from telegram import Update
from telegram.ext import ContextTypes
from bot.database.queries import get_user, get_notifications

async def show_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    notifications = await get_notifications(tg_id)
    if not notifications:
        await update.message.reply_text("🔔 Bildirishnomalar yo'q.")
        return
    text = "🔔 Bildirishnomalar\n\n"
    for n in notifications:
        text += f"• {n['text']}\n"
    await update.message.reply_text(text)