import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.config import BOT_TOKEN
from bot.database.connection import create_pool, close_pool
from bot.database.models import create_tables
from bot.handlers.start import get_start_handler
from bot.handlers.search import show_search, handle_like, handle_next, handle_block
from bot.handlers.shop import show_shop, buy_card, send_card_to_user, use_card, handle_card_accept, handle_card_deny
from bot.handlers.payment import get_payment_handler, show_payment
from bot.handlers.admin import admin_panel, handle_admin_callback, handle_admin_text

logging.basicConfig(level=logging.INFO)

async def main():
    pool = await create_pool()
    await create_tables(pool)
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlerlar
    app.add_handler(get_start_handler())
    app.add_handler(get_payment_handler())

    # Menyu
    app.add_handler(MessageHandler(filters.Regex("🔍 Qidiruv"), show_search))
    app.add_handler(MessageHandler(filters.Regex("🛍️ Do'kon"), show_shop))
    app.add_handler(MessageHandler(filters.Regex("💰 Balans"), show_payment))

    # Admin
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_admin_text
    ))

    # Callback
    app.add_handler(CallbackQueryHandler(handle_like, pattern="^like_"))
    app.add_handler(CallbackQueryHandler(handle_next, pattern="^next_user"))
    app.add_handler(CallbackQueryHandler(handle_block, pattern="^block_"))
    app.add_handler(CallbackQueryHandler(buy_card, pattern="^buy_card_"))
    app.add_handler(CallbackQueryHandler(send_card_to_user, pattern="^send_card_"))
    app.add_handler(CallbackQueryHandler(use_card, pattern="^use_card_"))
    app.add_handler(CallbackQueryHandler(handle_card_accept, pattern="^card_accept_"))
    app.add_handler(CallbackQueryHandler(handle_card_deny, pattern="^card_deny_"))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_|^broadcast_|^resolve_"))

    print("✅ Bot ishga tushdi!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())