from bot.database.connection import get_pool

async def get_stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        today = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURRENT_DATE"
        )
        premium = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE tariff != 'free'"
        )
        total_income = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status='confirmed'"
        )
        matches = await conn.fetchval("SELECT COUNT(*) FROM matches")
        return {
            'total_users': total,
            'today_users': today,
            'premium_users': premium,
            'total_income': total_income,
            'total_matches': matches
        }

async def get_user_by_unique_id(unique_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE unique_id=$1", unique_id
        )

async def block_user(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_blocked=TRUE WHERE telegram_id=$1", telegram_id
        )

async def unblock_user(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_blocked=FALSE WHERE telegram_id=$1", telegram_id
        )

async def add_balance_admin(telegram_id: int, amount: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET balance=balance+$1 WHERE telegram_id=$2",
            amount, telegram_id
        )

async def get_all_users_ids():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT telegram_id, gender FROM users WHERE is_blocked=FALSE")
        return rows

async def get_complaints():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT c.*, 
                   u1.full_name as from_name,
                   u2.full_name as to_name,
                   u2.unique_id as to_unique_id,
                   u2.telegram_id as to_telegram_id
            FROM complaints c
            JOIN users u1 ON c.from_user = u1.telegram_id
            JOIN users u2 ON c.to_user = u2.telegram_id
            WHERE c.status = 'new'
            ORDER BY c.created_at
        """)

async def resolve_complaint(complaint_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE complaints SET status='resolved' WHERE id=$1", complaint_id
        )