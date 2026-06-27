from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database.admin_queries import get_stats, get_user_by_unique_id, block_user, unblock_user, get_all_users_ids, get_complaints
from bot.database.queries import add_balance, get_pending_transactions, update_transaction, get_user
from bot.keyboards.admin_kb import admin_menu, user_actions, broadcast_targets
from bot.config import ADMIN_ID

def is_admin(telegram_id: int):
    return telegram_id == ADMIN_ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("Admin Panel", reply_markup=admin_menu())

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return
    data = query.data

    if data == "admin_stats":
        stats = await get_stats()
        msg = "Statistika\n\n"
        msg += "Jami foydalanuvchilar: " + str(stats['total_users']) + "\n"
        msg += "Bugun yangi: " + str(stats['today_users']) + "\n"
        msg += "Premium/VIP: " + str(stats['premium_users']) + "\n"
        msg += "Jami daromad: " + str(stats['total_income']) + " som\n"
        msg += "Jami matchlar: " + str(stats['total_matches'])
        await query.message.reply_text(msg)

    elif data == "admin_search_user":
        await query.message.reply_text("Foydalanuvchi ID sini kiriting (TAN-00547):")
        context.user_data['admin_action'] = 'search_user'

    elif data == "admin_payments":
        transactions = await get_pending_transactions()
        if not transactions:
            await query.message.reply_text("Kutayotgan tovlovlar yoq.")
            return
        for tx in transactions:
            caption = "Tovlov sorovi\n\n"
            caption += tx['full_name'] + " (#" + tx['unique_id'] + ")\n"
            caption += "Summa: " + str(tx['amount']) + " som\n"
            caption += "Tranzaksiya: #" + str(tx['id'])
            
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("Tasdiqlash", callback_data="admin_confirm_" + str(tx['id']) + "_" + str(tx['telegram_id'])),
                InlineKeyboardButton("Rad etish", callback_data="admin_reject_" + str(tx['id']) + "_" + str(tx['telegram_id']))
            ]])
            await context.bot.send_photo(chat_id=update.effective_user.id, photo=tx['check_file_id'], caption=caption, reply_markup=kb)

    elif data == "admin_broadcast":
        await query.message.reply_text("Kimga yubormoqchisiz?", reply_markup=broadcast_targets())

    elif data == "admin_complaints":
        complaints = await get_complaints()
        if not complaints:
            await query.message.reply_text("Yangi shikoyatlar yoq.")
            return
        for c in complaints:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("Bloklash", callback_data="admin_block_" + str(c['to_telegram_id'])),
                InlineKeyboardButton("Hal qilindi", callback_data="resolve_" + str(c['id']))
            ]])
            msg = "Shikoyat\n\n"
            msg += "Kim shikoyat qildi: " + c['from_name'] + "\n"
            msg += "Kim haqida: " + c['to_name'] + " (#" + c['to_unique_id'] + ")"
            await query.message.reply_text(msg, reply_markup=kb)

    elif data.startswith("admin_confirm_"):
        parts = data.split('_')
        tx_id = int(parts[2])
        tg_id = int(parts[3])
        tx_list = await get_pending_transactions()
        amount = 0
        for t in tx_list:
            if t['id'] == tx_id:
                amount = t['amount']
                break
        await update_transaction(tx_id, 'confirmed')
        await add_balance(tg_id, amount)
        msg = "Tovlovingiz tasdiqlandi!\n" + str(amount) + " som balansingizga qoshildi."
        await context.bot.send_message(chat_id=tg_id, text=msg)
        await query.message.reply_text("Tovlov tasdiqlandi!")

    elif data.startswith("admin_reject_"):
        parts = data.split('_')
        tx_id = int(parts[2])
        tg_id = int(parts[3])
        await update_transaction(tx_id, 'rejected')
        await context.bot.send_message(chat_id=tg_id, text="Tovlovingiz rad etildi.")
        await query.message.reply_text("Tovlov rad etildi.")

    elif data.startswith("admin_block_"):
        tg_id = int(data.split('_')[-1])
        await block_user(tg_id)
        await context.bot.send_message(chat_id=tg_id, text="Hisobingiz bloklandi.")
        await query.message.reply_text("Foydalanuvchi bloklandi.")

    elif data.startswith("admin_unblock_"):
        tg_id = int(data.split('_')[-1])
        await unblock_user(tg_id)
        await context.bot.send_message(chat_id=tg_id, text="Blok olib tashlandi.")
        await query.message.reply_text("Blok olib tashlandi.")

    elif data.startswith("broadcast_"):
        target = data.split('_')[1]
        context.user_data['broadcast_target'] = target
        await query.message.reply_text("Xabar matnini yozing:")
        context.user_data['admin_action'] = 'broadcast'

async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    action = context.user_data.get('admin_action')

    if action == 'search_user':
        unique_id = update.message.text.replace('#', '').strip()
        user = await get_user_by_unique_id(unique_id)
        if not user:
            await update.message.reply_text("Foydalanuvchi topilmadi.")
            return
        
        blocked_status = "Ha" if user['is_blocked'] else "Yoq"
        verified_status = "Ha" if user['is_verified'] else "Yoq"
        
        msg = "Foydalanuvchi malumotlari\n\n"
        msg += "Ism: " + user['full_name'] + "\n"
        msg += "#" + user['unique_id'] + "\n"
        msg += "Jins: " + user['gender'] + "\n"
        msg += "Yosh: " + str(user['age']) + "\n"
        msg += "Shahar: " + user['city'] + "\n"
        msg += "Tarif: " + user['tariff'] + "\n"
        msg += "Balans: " + str(user['balance']) + " som\n"
        msg += "Bloklangan: " + blocked_status + "\n"
        msg += "Tasdiqlangan: " + verified_status
        
        await update.message.reply_text(msg, reply_markup=user_actions(user['telegram_id'], user['is_blocked']))
        context.user_data['admin_action'] = None

    elif action == 'broadcast':
        text = update.message.text
        target = context.user_data.get('broadcast_target', 'all')
        users = await get_all_users_ids()
        count = 0
        for u in users:
            if target == 'male' and u['gender'] != 'male':
                continue
            if target == 'female' and u['gender'] != 'female':
                continue
            try:
                await context.bot.send_message(chat_id=u['telegram_id'], text=text)
                count += 1
            except Exception:
                pass
        msg = "Xabar " + str(count) + " ta foydalanuvchiga yuborildi."
        await update.message.reply_text(msg)
        context.user_data['admin_action'] = None