import math
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from bot.database.queries import (
    get_user, search_users, add_like, check_match,
    create_match, add_notification, get_like_count, get_balance, deduct_balance
)
from bot.keyboards.search_kb import search_actions
from bot.config import LIKE_LIMIT_FREE, LIKE_LIMIT_PREMIUM, PRICE_CARD_SIMPLE

PRICE_TANISHISH = 15000
PRICE_OILA = 35000
PRICE_LOCATION = 25000


def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula - ikki nuqta orasidagi masofa (km)"""
    if not all([lat1, lon1, lat2, lon2]):
        return None
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return round(R * c, 1)


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
    interests = target['interests'] or "Ko'rsatilmagan"
    goal = target['goal'] or "Ko'rsatilmagan"
    bio = target['bio'] or "Ko'rsatilmagan"
    
    # Masofani hisoblash
    distance_text = ""
    if target['latitude'] and target['longitude'] and user['latitude'] and user['longitude']:
        dist = calculate_distance(
            user['latitude'], user['longitude'],
            target['latitude'], target['longitude']
        )
        if dist is not None:
            if dist < 1:
                distance_text = f"📍 {int(dist * 1000)} m uzoqlikda"
            else:
                distance_text = f"📍 {dist} km uzoqlikda"
    
    caption = (
        f"👤 {target['full_name']}, {target['age']} yosh\n"
        f"🆔 #{target['unique_id']}\n"
        f"{distance_text}\n"
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
                # Offset ni kamaytirish
                context.user_data['search_offset'] = max(0, context.user_data.get('search_offset', 1) - 1)
                await show_user_profile(update, context, dict(target), user)
        else:
            await show_next_user(update, context, user)


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
            await context.bot.send_message(
                chat_id=to_user,
                text=f"🎉 Siz match bo'ldingiz!\n\n"
                     f"❤️ #{user['unique_id']} ({user['full_name']}) sizni yoqtirdi!\n\n"
                     f"🆔 Ularning ID: #{user['unique_id']}\n"
                     f"Endi siz ham yozishingiz mumkin!"
            )
        else:
            await add_notification(
                to_user,
                f"❤️ #{user['unique_id']} sizni yoqtirdi!"
            )
            await context.bot.send_message(
                chat_id=to_user,
                text=f"💌 Yangi bildirishnoma!\n\n"
                     f"❤️ #{user['unique_id']} ({user['full_name']}) sizni yoqtirdi!\n\n"
                     f"👉 Qidiruv orqali ularni topishingiz mumkin."
            )
            await query.answer("❤️ Yoqtirildi!", show_alert=False)
    
    current_user = await get_user(tg_id)
    await show_next_user(update, context, current_user)


async def handle_tanishish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tanishish kartochkasi (15,000 som)"""
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    to_user = int(query.data.split('_')[1])
    user = await get_user(tg_id)
    target = await get_user(to_user)
    
    balance = await get_balance(tg_id)
    if balance < PRICE_TANISHISH:
        await query.message.reply_text(
            f"❌ Balans yetarli emas!\n\n"
            f"💰 Balansingiz: {balance:,} so'm\n"
            f"💳 Kerakli summa: {PRICE_TANISHISH:,} so'm\n\n"
            "Balansni to'ldiring: /payment"
        )
        return
    
    # Pul yechish
    success = await deduct_balance(tg_id, PRICE_TANISHISH)
    if not success:
        await query.message.reply_text("❌ Xatolik yuz berdi!")
        return
    
    # Match yaratish
    await create_match(tg_id, to_user)
    
    # Yigitga xabar
    await query.message.reply_text(
        f"✅ Tanishish tasdiqlandi!\n"
        f"Endi yozishingiz mumkin. 🆔 #{target['unique_id']}"
    )
    
    # Qizga bildirishnoma
    await add_notification(
        to_user,
        f"💌 {user['full_name']} (ID: #{user['unique_id']}) siz bilan tanishdi!"
    )
    await context.bot.send_message(
        chat_id=to_user,
        text=f"💌 Yangi tanishish so'rovi!\n\n"
             f"💌 #{user['unique_id']} ({user['full_name']}) siz bilan tanishishni xohlaydi!\n\n"
             f"🆔 Ularning ID: #{user['unique_id']}\n\n"
             f"Endi siz ham yozishingiz mumkin!"
    )


async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await get_user(update.effective_user.id)
    await show_next_user(update, context, user)