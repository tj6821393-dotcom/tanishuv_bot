import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from bot.config import BOT_TOKEN
from bot.database.connection import create_pool, close_pool
from bot.database.models import create_tables

from bot.handlers.start import get_start_handler
from bot.handlers.search import (
    show_search, handle_like, handle_next, handle_prev_user, handle_tanishish,
    handle_story, handle_photos
)
from bot.handlers.payment import get_payment_handler, show_payment
from bot.handlers.admin import admin_panel, handle_admin_callback, handle_admin_text
from bot.handlers.profile import show_profile, handle_profile_callback, handle_edit_input
from bot.handlers.messages import show_messages, handle_message_input
from bot.handlers.settings import show_settings, handle_settings_callback

logging.basicConfig(level=logging.INFO)


async def post_init(application):
    pool = await create_pool()
    await create_tables(pool)
    application.bot_data['pool'] = pool
    print("✅ Bot ishga tushdi!")


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

    if context.user_data.get('search_by_id') or context.user_data.get('messages_action'):
        await handle_message_input(update, context)
        return


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(get_start_handler())
    app.add_handler(get_payment_handler())

    # Main menu tugmalari
    app.add_handler(MessageHandler(filters.Regex("🔍 Qidiruv"), show_search))
    app.add_handler(MessageHandler(filters.Regex("🆔 ID orqali"), show_messages))
    app.add_handler(MessageHandler(filters.Regex("👤 Profil"), show_profile))
    app.add_handler(MessageHandler(filters.Regex("💳 Balans"), show_payment))
    app.add_handler(MessageHandler(filters.Regex("⚙️ Sozlamalar"), show_settings))

    app.add_handler(CommandHandler("admin", admin_panel))

    # Search callbacklar
    app.add_handler(CallbackQueryHandler(handle_like, pattern="^like_"))
    app.add_handler(CallbackQueryHandler(handle_tanishish, pattern="^tanishish_"))
    app.add_handler(CallbackQueryHandler(handle_story, pattern="^story_"))
    app.add_handler(CallbackQueryHandler(handle_photos, pattern="^photos_"))
    app.add_handler(CallbackQueryHandler(handle_prev_user, pattern="^prev_user"))
    app.add_handler(CallbackQueryHandler(handle_next, pattern="^next_user"))

    # Profile callbacklar
    app.add_handler(CallbackQueryHandler(handle_profile_callback, pattern="^profile_|^edit_"))

    # Settings callbacklar
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern="^settings_"))

    # Admin callbacklar
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_|^broadcast_|^resolve_"))

    # Text handler (ID kiritish, admin text, edit input)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_all_text
    ))
    
    # Contact handler for profile phone edit
    app.add_handler(MessageHandler(
        filters.CONTACT,
        handle_all_text
    ))

    app.run_polling()


if __name__ == "__main__":
    main()
