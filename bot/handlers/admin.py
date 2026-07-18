from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database.admin_queries import get_stats, get_user_by_unique_id, block_user, unblock_user, get_all_users_ids, get_complaints, resolve_complaint, add_balance_admin
from bot.database.queries import add_balance, get_pending_transactions, update_transaction, get_user
from bot.keyboards.admin_kb import admin_menu, user_actions, broadcast_targets
from bot.config import ADMIN_ID

def is_admin(telegram_id: int):
    return ADMIN_ID is not None and telegram_id == ADMIN_ID

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
        msg = (
            "Statistika\n\n"
            f"Jami foydalanuvchilar: {stats['total_users']}\n"
            f"Bugun yangi: {stats['today_users']}\n"
            f"Premium/VIP: {stats['premium_users']}\n"
            f"Jami daromad: {stats['total_income']} som\n"
            f"Jami matchlar: {stats['total_matches']}"
        )
        await query.message.reply_text(msg)

    elif data == "admin_search_user":
        await query.message.reply_text("Foydalanuvchi ID sini kiriting (TAN-00547):")
        context.user_data['admin_action'] = 'search_user'

    elif data == "admin_payments":
        transactions = await get_pending_transactions()
        if not transactions:
            await query.message.reply_text("Kutayotgan to'lovlar yo'q.")
            return
        for tx in transactions:
            caption = (
                f"To'lov so'rovi\n\n"
                f"{tx['full_name']} (#{tx['unique_id']})\n"
                f"Summa: {tx['amount']} so'm\n"
                f"Tranzaksiya: #{tx['id']}"
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("Tasdiqlash", callback_data=f"admin_confirm_{tx['id']}_{tx['telegram_id']}"),
                InlineKeyboardButton("Rad etish", callback_data=f"admin_reject_{tx['id']}_{tx['telegram_id']}")
            ]])
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=tx['check_file_id'],
                caption=caption,
                reply_markup=kb
            )

    elif data == "admin_broadcast":
        await query.message.reply_text("Kimga yubormoqchisiz?", reply_markup=broadcast_targets())

    elif data == "admin_complaints":
        complaints = await get_complaints()
        if not complaints:
            await query.message.reply_text("Yangi shikoyatlar yo'q.")
            return
        for c in complaints:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("Bloklash", callback_data=f"admin_block_{c['to_telegram_id']}"),
                InlineKeyboardButton("Hal qilindi", callback_data=f"resolve_{c['id']}")
            ]])
            msg = (
                f"Shikoyat\n\n"
                f"Kim shikoyat qildi: {c['from_name']}\n"
                f"Kim haqida: {c['to_name']} (#{c['to_unique_id']})"
            )
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
        await context.bot.send_message(
            chat_id=tg_id,
            text=f"To'lovingiz tasdiqlandi!\n{amount} so'm balansingizga qo'shildi."
        )
        await query.message.reply_text("To'lov tasdiqlandi!")

    elif data.startswith("admin_reject_"):
        parts = data.split('_')
        tx_id = int(parts[2])
        tg_id = int(parts[3])
        await update_transaction(tx_id, 'rejected')
        await context.bot.send_message(chat_id=tg_id, text="To'lovingiz rad etildi.")
        await query.message.reply_text("To'lov rad etildi.")

    elif data.startswith("admin_block_"):
        tg_id = int(data.split('_')[-1])
        await block_user(tg_id)
        try:
            await context.bot.send_message(chat_id=tg_id, text="Hisobingiz bloklandi.")
        except Exception:
            pass
        await query.message.reply_text("Foydalanuvchi bloklandi.")

    elif data.startswith("admin_unblock_"):
        tg_id = int(data.split('_')[-1])
        await unblock_user(tg_id)
        try:
            await context.bot.send_message(chat_id=tg_id, text="Blok olib tashlandi.")
        except Exception:
            pass
        await query.message.reply_text("Blok olib tashlandi.")

    elif data.startswith("admin_add_balance_"):
        tg_id = int(data.split('_')[-1])
        context.user_data['admin_action'] = 'add_balance'
        context.user_data['admin_target_user'] = tg_id
        await query.message.reply_text("Qo'shmoqchi bo'lgan summani kiriting (so'mda):")

    elif data.startswith("broadcast_"):
        target = data.split('_')[1]
        context.user_data['broadcast_target'] = target
        await query.message.reply_text("Xabar matnini yozing:")
        context.user_data['admin_action'] = 'broadcast'

    elif data.startswith("resolve_"):
        complaint_id = int(data.split('_')[1])
        await resolve_complaint(complaint_id)
        await query.message.reply_text("Shikoyat hal qilindi.")

    elif data == "admin_back":
        await query.message.reply_text("Admin Panel", reply_markup=admin_menu())

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
        msg = (
            f"Foydalanuvchi ma'lumotlari\n\n"
            f"Ism: {user['full_name']}\n"
            f"#{user['unique_id']}\n"
            f"Jins: {user['gender']}\n"
            f"Yosh: {user['age']}\n"
            f"Shahar: {user['city']}\n"
            f"Tarif: {user['tariff']}\n"
            f"Balans: {user['balance']} so'm\n"
            f"Bloklangan: {blocked_status}\n"
            f"Tasdiqlangan: {verified_status}"
        )
        await update.message.reply_text(msg, reply_markup=user_actions(user['telegram_id'], user['is_blocked']))
        context.user_data['admin_action'] = None

    elif action == 'add_balance':
        try:
            amount = int(update.message.text.replace(' ', '').replace(',', ''))
            tg_id = context.user_data.get('admin_target_user')
            if tg_id:
                await add_balance_admin(tg_id, amount)
                await update.message.reply_text(f"✅ {amount:,} so'm qo'shildi.")
                try:
                    await context.bot.send_message(
                        chat_id=tg_id,
                        text=f"✅ Balansingizga {amount:,} so'm qo'shildi!"
                    )
                except Exception:
                    pass
            context.user_data['admin_action'] = None
            context.user_data['admin_target_user'] = None
        except ValueError:
            await update.message.reply_text("Iltimos, faqat raqam kiriting!")

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
        await update.message.reply_text(f"Xabar {count} ta foydalanuvchiga yuborildi.")
        context.user_data['admin_action'] = None
