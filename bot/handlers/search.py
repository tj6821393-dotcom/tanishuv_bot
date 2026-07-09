from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from bot.database.queries import (
    get_user, search_users, add_like, check_match,
    create_match, add_notification, get_like_count
)
from bot.keyboards.search_kb import search_actions
from bot.config import LIKE_LIMIT_FREE, LIKE_LIMIT_PREMIUM

async def show_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    context.user_data['search_offset'] = context.user_data.get('search_offset', 0)
    await show_next_user(update, context, user)

async def show_next_user(update, context, current_user):
    tg_id = current_user['telegram_id']
    offset = context.user_data.get('search_offset', 0)
    users = await search_users(tg_id, current_user['gender'], limit=1, offset=offset)
    if not users:
        context.user_data['search_offset'] = 0
        msg = "🔍 Hozircha yangi foydalanuvchilar yo'q.\nKeyinroq qayta urinib ko'ring!"
        if update.callback_query:
            await update.callback_query.message.reply_text(msg)
        else:
            await update.message.reply_text(msg)
        return
    target = users[0]
    context.user_data['current_target'] = target['telegram_id']
    context.user_data['search_offset'] = offset + 1
    photos = target['photos'].split(',') if target['photos'] else []
    interests = target['interests'] or "Ko'rsatilmagan"
    goal = target['goal'] or "Ko'rsatilmagan"
    bio = target['bio'] or "Ko'rsatilmagan"
    caption = (
        f"👤 {target['full_name']}, {target['age']} yosh\n"
        f"🆔 #{target['unique_id']}\n"
        f"📍 {target['city']}\n"
        f"❤️ {interests}\n"
        f"🎯 {goal}\n"
        f"📝 {bio}"
    )
    kb = search_actions(target['telegram_id'])
    if photos:
        if update.callback_query:
            await update.callback_query.message.reply_photo(
                photo=photos[0], caption=caption, reply_markup=kb
            )
        else:
            await update.message.reply_photo(
                photo=photos[0], caption=caption, reply_markup=kb
            )
    else:
        if update.callback_query:
            await update.callback_query.message.reply_text(caption, reply_markup=kb)
        else:
            await update.message.reply_text(caption, reply_markup=kb)

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    to_user = int(query.data.split('_')[1])
    user = await get_user(tg_id)
    target = await get_user(to_user)
    like_limit = LIKE_LIMIT_FREE if user['tariff'] == 'free' else LIKE_LIMIT_PREMIUM
    current_likes = await get_like_count(tg_id)
    if user['tariff'] == 'free' and current_likes >= like_limit:
        await query.message.reply_text(
            f"❤️ Like limitingiz tugadi ({like_limit} ta/12 soat)\n"
            "Premium olib cheksiz like yuboring!"
        )
        return
    success = await add_like(tg_id, to_user)
    if success:
        is_match = await check_match(tg_id, to_user)
        if is_match:
            await create_match(tg_id, to_user)
            await query.message.reply_text(
                f"🎉 Match! {target['full_name']} ham sizni yoqtirdi!\n"
                f"Endi yozishingiz mumkin. 🆔 #{target['unique_id']}"
            )
            await add_notification(
                to_user,
                f"🤝 Siz #{user['unique_id']} bilan match bo'ldingiz!"
            )
            # Match bo'lganda ikki tomon ham xabar oladi
            await context.bot.send_message(
                chat_id=to_user,
                text=f"🎉 Siz match bo'ldingiz!\n\n"
                     f"❤️ #{user['unique_id']} ({user['full_name']}) sizni yoqtirdi!\n\n"
                     f"🆔 Ularning ID: #{user['unique_id']}\n"
                     f"Endi siz ham yozishingiz mumkin!"
            )
        else:
            # Oddiy like - qabul qiluvchiga SMS kabi bildirishnoma yuborish
            await add_notification(
                to_user,
                f"❤️ #{user['unique_id']} sizni yoqtirdi!"
            )
            # 📱 SMS kabi to'g'ridan-to'g'ri xabar yuborish
            await context.bot.send_message(
                chat_id=to_user,
                text=f"💌 Yangi bildirishnoma!\n\n"
                     f"❤️ #{user['unique_id']} ({user['full_name']}) sizni yoqtirdi!\n\n"
                     f"👉 Qidiruv orqali ularni topishingiz mumkin."
            )
            await query.answer("❤️ Yoqtirildi!", show_alert=False)
    current_user = await get_user(tg_id)
    await show_next_user(update, context, current_user)

async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await get_user(update.effective_user.id)
    await show_next_user(update, context, user)

async def handle_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    to_user = int(query.data.split('_')[1])
    from bot.database.connection import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO complaints (from_user, to_user) VALUES ($1, $2)",
            update.effective_user.id, to_user
        )
    await query.message.reply_text("🚫 Foydalanuvchi bloklandi va shikoyat yuborildi.")
    user = await get_user(update.effective_user.id)
    await show_next_user(update, context, user)