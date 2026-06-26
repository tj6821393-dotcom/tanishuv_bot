import asyncpg
from bot.config import DATABASE_URL

pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

async def get_pool():
    global pool
    if pool is None:
        await create_pool()
    return pool

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None