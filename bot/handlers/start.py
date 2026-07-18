import random
import string
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from bot.database.queries import get_user, create_user
from bot.keyboards.main_menu import main_menu

(NAME, GENDER, AGE, LOCATION, PHOTOS, CONTACT) = range(6)

def generate_unique_id():
    digits = ''.join(random.choices(string.digits, k=5))
    return f"TAN-{digits}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if user:
        await update.message.reply_text(
            f"Xush kelibsiz, {user['full_name']}! 👋\n\n"
            f"🆔 Sizning ID: #{user['unique_id']}",
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
    
    # Lokatsiya so'rash
    kb = ReplyKeyboardMarkup([
        [KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)]
    ], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "📍 Lokatsiyangizni yuboring:\n"
        "Bu sizga yaqin atrofdagi odamlarni topishga yordam beradi.",
        reply_markup=kb
    )
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        context.user_data['latitude'] = update.message.location.latitude
        context.user_data['longitude'] = update.message.location.longitude
        context.user_data['city'] = "Lokatsiya bilan"
    else:
        # Lokatsiya yubormasdan davom etish
        context.user_data['latitude'] = None
        context.user_data['longitude'] = None
        context.user_data['city'] = "Lokatsiya yoq"
    
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
        # Kontakt ulashish so'rovi (MAJBURIY)
        kb = ReplyKeyboardMarkup([
            [KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "📱 Telefon raqamingizni ulashing KERAK!\n\n"
            "Bu orqali sizga yozishishadi.",
            reply_markup=kb
        )
        return CONTACT
    return PHOTOS

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.contact:
            context.user_data['phone_number'] = update.message.contact.phone_number
            context.user_data['username'] = update.effective_user.username
        else:
            kb = ReplyKeyboardMarkup([
                [KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]
            ], resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                "❌ Kontakt ulashish KERAK!",
                reply_markup=kb
            )
            return CONTACT
        
        unique_id = generate_unique_id()
        data = {
            'telegram_id': update.effective_user.id,
            'unique_id': unique_id,
            'username': context.user_data.get('username'),
            'phone_number': context.user_data.get('phone_number'),
            'full_name': context.user_data['full_name'],
            'gender': context.user_data['gender'],
            'age': context.user_data['age'],
            'city': context.user_data.get('city'),
            'bio': None,
            'goal': None,
            'interests': None,
            'photos': ','.join(context.user_data.get('photos', [])),
            'latitude': context.user_data.get('latitude'),
            'longitude': context.user_data.get('longitude'),
        }
        await create_user(data)
        await update.message.reply_text(
            f"✅ Profil yaratildi!\n\n"
            f"🆔 ID: #{unique_id}\n"
            f"📱 {context.user_data['phone_number']}\n"
            f"🔗 @{context.user_data['username'] or 'username yoq'}",
            reply_markup=main_menu()
        )
        return ConversationHandler.END
    except Exception as e:
        print(f"ERROR in get_contact: {e}")
        await update.message.reply_text(
            "❌ Xatolik yuz berdi. /start bosib qayta urinib ko'ring.",
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
            LOCATION: [
                MessageHandler(filters.LOCATION, get_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)
            ],
            PHOTOS: [
                MessageHandler(filters.PHOTO, get_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_photos)
            ],
            CONTACT: [
                MessageHandler(filters.CONTACT, get_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)
            ],
        },
        fallbacks=[CommandHandler('start', start)]
    )