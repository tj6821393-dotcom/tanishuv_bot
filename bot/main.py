import asyncio
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from bot.config import BOT_TOKEN
from bot.database.connection import create_pool, close_pool
from bot.database.models import create_tables

from bot.handlers.start import get_start_handler
from bot.handlers.search import show_search, handle_like, handle_next, handle_block
from bot.handlers.shop import show_shop, buy_card, send_card_to_user, use_card, handle_card_accept, handle_card_deny
from bot.handlers.payment import get_payment_handler, show_payment
from bot.handlers.admin import admin_panel, handle_admin_callback, handle_admin_text
from bot.handlers.profile import show_profile, handle_profile_callback, handle_edit_input
from bot.handlers.messages import show_messages, handle_message_input
from bot.handlers.notifications import show_notifications
from bot.handlers.settings import show_settings, handle_settings_callback, handle_new_location

logging.basicConfig(level=logging.INFO)

async def main():
    pool = await create_pool()
    await create_tables(pool)

    app = Application.builder().token(BOT_TOKEN).build()

    # ═══════════════════════════
    # CONVERSATION HANDLERLAR
    # ═══════════════════════════
    app.add_handler(get_start_handler())
    app.add_handler(get_payment_handler())

    # ═══════════════════════════
    # MENYU TUGMALARI
    # ═══════════════════════════
    app.add_handler(MessageHandler(filters.Regex("🔍 Qidiruv"), show_search))
    app.add_handler(MessageHandler(filters.Regex("🛍️ Do'kon"), show_shop))
    app.add_handler(MessageHandler(filters.Regex("👤 Profil"), show_profile))
    app.add_handler(MessageHandler(filters.Regex("🔔 Bildirishnomalar"), show_notifications))
    app.add_handler(MessageHandler(filters.Regex("💌 Xabarlar"), show_messages))
    app.add_handler(MessageHandler(filters.Regex("⚙️ Sozlamalar"), show_settings))
    app.add_handler(MessageHandler(filters.Regex("📊 Statistika"), show_stats))

    # ═══════════════════════════
    # LOKATSIYA
    # ═══════════════════════════
    app.add_handler(MessageHandler(filters.LOCATION, handle_new_location))

    # ═══════════════════════════
    # ADMIN
    # ═══════════════════════════
    app.add_handler(CommandHandler("admin", admin_panel))

    # ═══════════════════════════
    # CALLBACK QUERYLAR
    # ═══════════════════════════

    # Qidiruv
    app.add_handler(CallbackQueryHandler(handle_like, pattern="^like_"))
    app.add_handler(CallbackQueryHandler(handle_next, pattern="^next_user"))
    app.add_handler(CallbackQueryHandler(handle_block, pattern="^block_"))

    # Do'kon
    app.add_handler(CallbackQueryHandler(buy_card, pattern="^buy_card_"))
    app.add_handler(CallbackQueryHandler(send_card_to_user, pattern="^send_card_"))
    app.add_handler(CallbackQueryHandler(use_card, pattern="^use_card_"))
    app.add_handler(CallbackQueryHandler(handle_card_accept, pattern="^card_accept_"))
    app.add_handler(CallbackQueryHandler(handle_card_deny, pattern="^card_deny_"))

    # Profil
    app.add_handler(CallbackQueryHandler(handle_profile_callback, pattern="^profile_|^edit_"))

    # Sozlamalar
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern="^settings_"))

    # Lokatsiya ruxsati
    app.add_handler(CallbackQueryHandler(handle_location_perm, pattern="^loc_perm_"))

    # Admin
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_|^broadcast_|^resolve_"))

    # ═══════════════════════════
    # MATN HANDLERLAR (eng oxirida)
    # ═══════════════════════════
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_all_text
    ))

    print("✅ Bot ishga tushdi!")
    await app.run_polling()

async def show_stats(update, context):
    from bot.database.queries import get_user
    from bot.database.connection import get_pool
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        views = await conn.fetchval(
            "SELECT COUNT(*) FROM likes WHERE to_user=$1", tg_id
        )
        matches = await conn.fetchval(
            "SELECT COUNT(*) FROM matches WHERE user1=$1 OR user2=$1", tg_id
        )
    await update.message.reply_text(
        f"📊 Statistika\n\n"
        f"🆔 #{user['unique_id']}\n"
        f"❤️ Yoqtirishlar: {views}\n"
        f"🤝 Matchlar: {matches}\n"
        f"💰 Balans: {user['balance']:,} so'm\n"
        f"⭐ Tarif: {user['tariff'].upper()}"
    )

async def handle_location_perm(update, context):
    from bot.database.queries import set_location_perm, get_user
    query = update.callback_query
    await query.answer()
    parts = query.data.split('_')
    perm_type = parts[2]
    from_user_id = int(parts[3])
    tg_id = update.effective_user.id

    if perm_type == 'deny':
        await query.message.reply_text("❌ Rad etdingiz.")
        return

    await set_location_perm(tg_id, from_user_id, perm_type)

    if perm_type == 'permanent':
        await query.message.reply_text(
            "✅ Doimiy ruxsat berildi.\n"
            "Sozlamalar orqali istalgan vaqtda o'chirishingiz mumkin."
        )
        await context.bot.send_message(
            chat_id=from_user_id,
            text="✅ Lokatsiya ruxsati olindi!\n"
                 "Mini App orqali ko'rishingiz mumkin."
        )
    elif perm_type == 'once':
        await query.message.reply_text(
            "⏳ Bir martalik ruxsat berildi.\n"
            "1 soatdan keyin avtomatik o'chadi."
        )
        await context.bot.send_message(
            chat_id=from_user_id,
            text="⏳ 1 soatlik lokatsiya ruxsati olindi!"
        )

async def handle_all_text(update, context):
    from bot.handlers.admin import is_admin, handle_admin_text
    from bot.handlers.messages import handle_message_input
    from bot.handlers.profile import handle_edit_input

    tg_id = update.effective_user.id

    if is_admin(tg_id) and context.user_data.get('admin_action'):
        await handle_admin_text(update, context)
        return

    if context.user_data.get('edit_field'):
        await handle_edit_input(update, context)
        return

    if context.user_data.get('messages_action'):
        await handle_message_input(update, context)
        return

if __name__ == "__main__":
    asyncio.run(main())