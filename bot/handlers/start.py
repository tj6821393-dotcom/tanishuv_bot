import random
import string
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from bot.database.queries import get_user, create_user
from bot.keyboards.main_menu import main_menu

(NAME, GENDER, AGE, CITY, LOCATION, PHOTOS, INTERESTS, GOAL, BIO) = range(9)

def generate_unique_id():
    digits = ''.join(random.choices(string.digits, k=5))
    return f"TAN-{digits}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if user:
        await update.message.reply_text(
            f"Xush kelibsiz, {user['full_name']}! 👋",
            reply_markup=main_menu()
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "👋 Salom! TanishBot ga xush kelibsiz!\n\n"
        "Ro'yxatdan o'tish uchun bir necha savollarga javob bering.\n\n"
        "Ismingizni kiriting:"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    from telegram import ReplyKeyboardMarkup
    kb = ReplyKeyboardMarkup([["👨 Erkak", "👩 Ayol"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Jinsingizni tanlang:", reply_markup=kb)
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Erkak" in text:
        context.user_data['gender'] = 'male'
    elif "Ayol" in text:
        context.user_data['gender'] = 'female'
    else:
        await update.message.reply_text("Iltimos, tugmadan tanlang!")
        return GENDER
    await update.message.reply_text("Yoshingizni kiriting (masalan: 22):")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if age < 18 or age > 60:
            await update.message.reply_text("Yosh 18 dan 60 gacha bo'lishi kerak!")
            return AGE
        context.user_data['age'] = age
    except ValueError:
        await update.message.reply_text("Iltimos, faqat raqam kiriting!")
        return AGE
    await update.message.reply_text("Shahringizni kiriting (masalan: Toshkent, Chilonzor):")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text
    from telegram import KeyboardButton, ReplyKeyboardMarkup
    kb = ReplyKeyboardMarkup([
        [KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]
    ], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "📍 Lokatsiyangizni yuboring:\n"
        "(Bu xaritada ko'rinish uchun kerak)", reply_markup=kb
    )
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        context.user_data['latitude'] = update.message.location.latitude
        context.user_data['longitude'] = update.message.location.longitude
    await update.message.reply_text(
        "📸 Profil rasmingizni yuboring (1-3 ta rasm):\n"
        "(Birinchi rasm asosiy bo'ladi)"
    )
    context.user_data['photos'] = []
    return PHOTOS

async def get_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        context.user_data['photos'].append(file_id)
        if len(context.user_data['photos']) < 3:
            from telegram import ReplyKeyboardMarkup
            kb = ReplyKeyboardMarkup([["✅ Tayyor"]], resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                f"✅ Rasm qabul qilindi ({len(context.user_data['photos'])}/3)\n"
                "Yana rasm yuboring yoki 'Tayyor' bosing:",
                reply_markup=kb
            )
            return PHOTOS
    if update.message.text == "✅ Tayyor" or len(context.user_data['photos']) >= 3:
        if not context.user_data['photos']:
            await update.message.reply_text("Kamida 1 ta rasm yuborish shart!")
            return PHOTOS
        interests_kb = [
            ["⚽ Sport", "🎵 Musiqa", "✈️ Sayohat"],
            ["🎬 Kino", "📚 Kitob", "🎮 O'yin"],
            ["🍳 Oshpazlik", "🎨 San'at", "💻 Texnologiya"],
            ["✅ Tayyor"]
        ]
        from telegram import ReplyKeyboardMarkup
        await update.message.reply_text(
            "❤️ Qiziqishlaringizni tanlang:",
            reply_markup=ReplyKeyboardMarkup(interests_kb, resize_keyboard=True)
        )
        context.user_data['interests'] = []
        return INTERESTS
    return PHOTOS

async def get_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "✅ Tayyor":
        from telegram import ReplyKeyboardMarkup
        goal_kb = ReplyKeyboardMarkup([
            ["💍 Jiddiy tanishuv", "🤝 Do'stlik"],
            ["💬 Suhbat"]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("🎯 Maqsadingizni tanlang:", reply_markup=goal_kb)
        return GOAL
    if text not in context.user_data['interests']:
        context.user_data['interests'].append(text)
    await update.message.reply_text(
        f"Tanlangan: {', '.join(context.user_data['interests'])}\n"
        "Yana tanlang yoki 'Tayyor' bosing."
    )
    return INTERESTS

async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['goal'] = update.message.text
    await update.message.reply_text(
        "📝 O'zingiz haqingizda qisqacha yozing:\n"
        "(Ixtiyoriy — o'tkazib yuborish uchun '-' yozing)"
    )
    return BIO

async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['bio'] = None if text == '-' else text
    unique_id = generate_unique_id()
    data = {
        'telegram_id': update.effective_user.id,
        'unique_id': unique_id,
        'full_name': context.user_data['full_name'],
        'gender': context.user_data['gender'],
        'age': context.user_data['age'],
        'city': context.user_data['city'],
        'bio': context.user_data.get('bio'),
        'goal': context.user_data.get('goal'),
        'interests': ', '.join(context.user_data.get('interests', [])),
        'photos': ','.join(context.user_data.get('photos', [])),
        'latitude': context.user_data.get('latitude'),
        'longitude': context.user_data.get('longitude'),
    }
    await create_user(data)
    await update.message.reply_text(
        f"✅ Profil muvaffaqiyatli yaratildi!\n\n"
        f"🆔 Sizning ID: #{unique_id}\n\n"
        f"Endi tanishuvni boshlashingiz mumkin!",
        reply_markup=main_menu()
    )
    return ConversationHandler.END

def get_start_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            LOCATION: [
                MessageHandler(filters.LOCATION, get_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)
            ],
            PHOTOS: [
                MessageHandler(filters.PHOTO, get_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_photos)
            ],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_interests)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
        },
        fallbacks=[CommandHandler('start', start)]
    )