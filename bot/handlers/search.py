from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from bot.database.queries import (
    get_user, search_users, add_like, check_match,
    create_match, add_notification, get_balance, deduct_balance, add_balance
)
from bot.keyboards.search_kb import search_actions

PRICE_TANISHISH = 15000


async def show_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    if not user:
        await update.message.reply_text("Avval ro'yxatdan o'ting! /start")
        return
    context.user_data['search_offset'] = 0
    context.user_data['search_history'] = []
    await show_next_user(update, context, user)


async def show_user_profile(update, context, target, user):
    """Foydalanuvchi profilini ko'rsatish"""
    photos = target['photos'].split(',') if target['photos'] else []
    
    # ID ni yashirish - faqat tanishuvdan keyin ko'rinadi
    caption = (
        f"👤 {target['full_name']}, {target['age']} yosh\n"
        f"📍 {target.get('city') or 'Lokatsiya'}"
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
    
    # History ga qo'shish
    if 'search_history' not in context.user_data:
        context.user_data['search_history'] = []
    if target['telegram_id'] not in context.user_data['search_history']:
        context.user_data['search_history'].append(target['telegram_id'])
    
    context.user_data['search_offset'] = offset + 1
    await show_user_profile(update, context, target, current_user)


async def handle_prev_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oldingi profilga qaytish"""
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    user = await get_user(tg_id)
    
    history = context.user_data.get('search_history', [])
    if len(history) < 2:
        await query.message.reply_text("⬅️ Oldingi profil yo'q.")
        return
    
    # Oxirgi profilni history dan o'chirish
    history.pop()
    context.user_data['search_history'] = history
    
    # Oldingi profilni olish
    from bot.database.connection import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        prev_user_id = history[-1] if history else None
        if prev_user_id:
            target = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", prev_user_id
            )
            if target:
                context.user_data['search_offset'] = max(0, context.user_data.get('search_offset', 1) - 1)
                await show_user_profile(update, context, dict(target), user)
        else:
            await show_next_user(update, context, user)


async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bepul like - cheklov yo'q"""
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    to_user = int(query.data.split('_')[1])
    user = await get_user(tg_id)
    target = await get_user(to_user)
    
    success = await add_like(tg_id, to_user)
    if not success:
        await query.message.reply_text("❌ Xatolik yuz berdi!")
        return
    
    is_match = await check_match(tg_id, to_user)
    if is_match:
        await create_match(tg_id, to_user)
        await query.message.reply_text(
            f"🎉 Match! {target['full_name']} ham sizni yoqtirdi!\n"
            f"🆔 Ularning ID: #{target['unique_id']}\n\n"
            f"Endi yozishingiz mumkin!"
        )
        await context.bot.send_message(
            chat_id=to_user,
            text=f"🎉 Match!\n\n"
                 f"❤️ #{user['unique_id']} ({user['full_name']}) sizni yoqtirdi!\n\n"
                 f"🆔 Ularning ID: #{user['unique_id']}\n"
                 f"Endi siz ham yozishingiz mumkin!"
        )
    else:
        await context.bot.send_message(
            chat_id=to_user,
            text=f"❤️ Yangi like!\n\n"
                 f"#{user['unique_id']} ({user['full_name']}) sizni yoqtirdi!\n\n"
                 f"🆔 Ularning ID: #{user['unique_id']}\n"
                 f"ID orqali qidirib, tanishish xati yuborishingiz mumkin!"
        )
        await query.answer("❤️ Yoqtirildi!", show_alert=True)
    
    current_user = await get_user(tg_id)
    await show_next_user(update, context, current_user)


async def handle_tanishish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tanishish tugmasi - 15,000 som"""
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    to_user_id = int(query.data.split('_')[1])
    user = await get_user(tg_id)
    target = await get_user(to_user_id)
    
    balance = await get_balance(tg_id)
    if balance < PRICE_TANISHISH:
        await query.message.reply_text(
            "❌ Balans yetarli emas!\n"
            f"💰 Balansingiz: {balance:,} so'm"
        )
        return
    
    # Balans yechish - atomik
    if not await deduct_balance(tg_id, PRICE_TANISHISH):
        await query.message.reply_text("❌ Balans yechishda xatolik!")
        return
    
    # Match yaratish - xatolik tekshirish
    match_ok = await create_match(tg_id, to_user_id)
    if not match_ok:
        # Match allaqachon mavjud - pul qaytarish
        await add_balance(tg_id, PRICE_TANISHISH)
        await query.message.reply_text("❌ Siz bu odam bilan allaqachon tanishgansiz!")
        return
    
    # SENDER GA HABAR
    msg1 = f"✅ Tanishuv tasdiqlandi! (-{PRICE_TANISHISH:,} so'm)\n\n"
    msg1 += f"👤 {target['full_name']}\n"
    if target.get('phone_number'):
        msg1 += f"📱 {target['phone_number']}\n"
    if target.get('username'):
        msg1 += f"🔗 @{target['username']}"
    await query.message.reply_text(msg1)
    
    # QARSHI TOMONGA HABAR
    msg2 = f"💌 Yangi tanishish!\n\n"
    msg2 += f"👤 {user['full_name']}\n"
    if user.get('phone_number'):
        msg2 += f"📱 {user['phone_number']}\n"
    if user.get('username'):
        msg2 += f"🔗 @{user['username']}"
    await context.bot.send_message(chat_id=to_user_id, text=msg2)


async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await get_user(update.effective_user.id)
    await show_next_user(update, context, user)


async def handle_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Story ko'rish"""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split('_')[1])
    target = await get_user(user_id)
    
    if not target:
        await query.message.reply_text("❌ Profil topilmadi!")
        return
    
    bio = target.get('bio') or "Story yoq"
    
    await query.message.reply_text(
        f"📖 {target['full_name']} haqida:\n\n"
        f"{bio}\n\n"
        f"🆔 #{target['unique_id']}"
    )


async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Suratlarni ko'rish"""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split('_')[1])
    target = await get_user(user_id)
    
    if not target:
        await query.message.reply_text("❌ Profil topilmadi!")
        return
    
    photos = target['photos'].split(',') if target['photos'] else []
    
    if not photos:
        await query.message.reply_text("📸 Suratlar yoq!")
        return
    
    # Har bir rasmni alohida yuborish
    for i, photo_id in enumerate(photos, 1):
        try:
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=photo_id,
                caption=f"📸 Surat {i}/{len(photos)}"
            )
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"Rasm {i} yuklab bo'lmadi."
            )