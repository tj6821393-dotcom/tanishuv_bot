from bot.database.connection import get_pool
from datetime import datetime, timedelta

# ═══════════════════════════
# FOYDALANUVCHI
# ═══════════════════════════

async def get_user(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1", telegram_id
        )

async def create_user(data: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            INSERT INTO users 
            (telegram_id, unique_id, full_name, gender, age, city, 
             bio, goal, interests, photos, latitude, longitude)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            RETURNING *
        """, data['telegram_id'], data['unique_id'], data['full_name'],
            data['gender'], data['age'], data['city'],
            data.get('bio'), data.get('goal'), data.get('interests'),
            data.get('photos'), data.get('latitude'), data.get('longitude')
        )

async def update_user(telegram_id: int, **kwargs):
    pool = await get_pool()
    fields = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(kwargs))
    values = list(kwargs.values())
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {fields} WHERE telegram_id = $1",
            telegram_id, *values
        )

async def delete_user(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM users WHERE telegram_id = $1", telegram_id
        )

# ═══════════════════════════
# QIDIRUV
# ═══════════════════════════

async def search_users(telegram_id: int, gender: str, limit: int = 10, offset: int = 0):
    pool = await get_pool()
    opposite = 'female' if gender == 'male' else 'male'
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM users
            WHERE gender = $1
            AND telegram_id != $2
            AND is_blocked = FALSE
            AND is_hidden = FALSE
            AND telegram_id NOT IN (
                SELECT to_user FROM likes WHERE from_user = $2
            )
            ORDER BY is_verified DESC, created_at DESC
            LIMIT $3 OFFSET $4
        """, opposite, telegram_id, limit, offset)

# ═══════════════════════════
# LIKE
# ═══════════════════════════

async def add_like(from_user: int, to_user: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO likes (from_user, to_user) VALUES ($1, $2)",
                from_user, to_user
            )
            return True
        except Exception:
            return False

async def check_match(user1: int, user2: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        like1 = await conn.fetchrow(
            "SELECT id FROM likes WHERE from_user=$1 AND to_user=$2", user1, user2
        )
        like2 = await conn.fetchrow(
            "SELECT id FROM likes WHERE from_user=$1 AND to_user=$2", user2, user1
        )
        return like1 and like2

async def create_match(user1: int, user2: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO matches (user1, user2) VALUES ($1, $2)",
                min(user1, user2), max(user1, user2)
            )
            return True
        except Exception:
            return False

async def get_like_count(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT like_count, like_reset_at, tariff FROM users WHERE telegram_id=$1",
            telegram_id
        )
        if not user:
            return 0
        now = datetime.now()
        if user['like_reset_at'] and now > user['like_reset_at']:
            await conn.execute(
                "UPDATE users SET like_count=0, like_reset_at=$1 WHERE telegram_id=$2",
                now + timedelta(hours=12), telegram_id
            )
            return 0
        return user['like_count']

# ═══════════════════════════
# BALANS
# ═══════════════════════════

async def get_balance(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT balance FROM users WHERE telegram_id=$1", telegram_id
        )
        return row['balance'] if row else 0

async def add_balance(telegram_id: int, amount: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET balance = balance + $1 WHERE telegram_id = $2",
            amount, telegram_id
        )

async def deduct_balance(telegram_id: int, amount: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        balance = await get_balance(telegram_id)
        if balance < amount:
            return False
        await conn.execute(
            "UPDATE users SET balance = balance - $1 WHERE telegram_id = $2",
            amount, telegram_id
        )
        return True

# ═══════════════════════════
# KARTOCHKALAR
# ═══════════════════════════

async def get_all_cards():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM cards ORDER BY price")

async def get_card(card_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM cards WHERE id=$1", card_id
        )

async def get_user_cards(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT c.*, uc.quantity FROM cards c
            JOIN user_cards uc ON c.id = uc.card_id
            WHERE uc.telegram_id = $1 AND uc.quantity > 0
        """, telegram_id)

async def add_user_card(telegram_id: int, card_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM user_cards WHERE telegram_id=$1 AND card_id=$2",
            telegram_id, card_id
        )
        if existing:
            await conn.execute(
                "UPDATE user_cards SET quantity=quantity+1 WHERE telegram_id=$1 AND card_id=$2",
                telegram_id, card_id
            )
        else:
            await conn.execute(
                "INSERT INTO user_cards (telegram_id, card_id) VALUES ($1, $2)",
                telegram_id, card_id
            )

async def use_user_card(telegram_id: int, card_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE user_cards SET quantity=quantity-1 WHERE telegram_id=$1 AND card_id=$2",
            telegram_id, card_id
        )

# ═══════════════════════════
# LOKATSIYA RUXSATI
# ═══════════════════════════

async def set_location_perm(from_user: int, to_user: int, perm_type: str):
    pool = await get_pool()
    expires = None
    if perm_type == 'once':
        expires = datetime.now() + timedelta(hours=1)
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO location_perms (from_user, to_user, perm_type, expires_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (from_user, to_user)
            DO UPDATE SET perm_type=$3, expires_at=$4
        """, from_user, to_user, perm_type, expires)

async def check_location_perm(from_user: int, to_user: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM location_perms
            WHERE from_user=$1 AND to_user=$2
        """, from_user, to_user)
        if not row:
            return False
        if row['expires_at'] and datetime.now() > row['expires_at']:
            await conn.execute(
                "DELETE FROM location_perms WHERE from_user=$1 AND to_user=$2",
                from_user, to_user
            )
            return False
        return True

# ═══════════════════════════
# XABARLAR
# ═══════════════════════════

async def send_message_db(from_user: int, to_user: int, text: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (from_user, to_user, text) VALUES ($1, $2, $3)",
            from_user, to_user, text
        )

async def get_messages(user1: int, user2: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM messages
            WHERE (from_user=$1 AND to_user=$2)
            OR (from_user=$2 AND to_user=$1)
            ORDER BY created_at
        """, user1, user2)

# ═══════════════════════════
# BILDIRISHNOMALAR
# ═══════════════════════════

async def add_notification(telegram_id: int, text: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO notifications (telegram_id, text) VALUES ($1, $2)",
            telegram_id, text
        )

async def get_notifications(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM notifications
            WHERE telegram_id=$1
            ORDER BY created_at DESC
            LIMIT 20
        """, telegram_id)
        await conn.execute(
            "UPDATE notifications SET is_read=TRUE WHERE telegram_id=$1",
            telegram_id
        )
        return rows

# ═══════════════════════════
# TO'LOV
# ═══════════════════════════

async def create_transaction(telegram_id: int, amount: int, check_file_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            INSERT INTO transactions (telegram_id, amount, check_file_id)
            VALUES ($1, $2, $3) RETURNING id
        """, telegram_id, amount, check_file_id)

async def get_pending_transactions():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT t.*, u.full_name, u.unique_id
            FROM transactions t
            JOIN users u ON t.telegram_id = u.telegram_id
            WHERE t.status = 'pending'
            ORDER BY t.created_at
        """)

async def update_transaction(tx_id: int, status: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE transactions SET status=$1 WHERE id=$2",
            status, tx_id
        )