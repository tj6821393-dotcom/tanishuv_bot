import asyncpg
import ssl
from bot.config import DATABASE_URL

pool = None

async def create_pool():
    global pool
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    pool = await asyncpg.create_pool(DATABASE_URL, ssl=ctx)
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
