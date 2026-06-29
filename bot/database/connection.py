import asyncpg
import ssl
import os
from bot.config import DATABASE_URL

pool = None

async def create_pool():
    global pool
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set!")
    
    print(f"[DB] Connecting to database...")
    print(f"[DB] URL starts with: {DATABASE_URL[:30] if DATABASE_URL else 'NONE'}...")
    
    try:
        # Try with SSL first (Supabase requires it)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        pool = await asyncpg.create_pool(DATABASE_URL, ssl=ctx)
        print("[DB] Connected successfully with SSL!")
    except Exception as e:
        print(f"[DB] SSL connection failed: {e}")
        print("[DB] Trying without SSL...")
        try:
            pool = await asyncpg.create_pool(DATABASE_URL)
            print("[DB] Connected successfully without SSL!")
        except Exception as e2:
            print(f"[DB] Both connection attempts failed: {e2}")
            raise e2
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
