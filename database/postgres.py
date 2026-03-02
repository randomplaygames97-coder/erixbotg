import asyncpg
import os
from loguru import logger

DATABASE_URL = os.getenv("DATABASE_URL")
_pool = None

async def init_db_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        logger.info("Pool di connessioni PostgreSQL creato")
        await create_tables()
    return _pool

async def get_pool():
    if _pool is None:
        await init_db_pool()
    return _pool

async def create_tables():
    """Crea le tabelle se non esistono (adatta al tuo schema)"""
    create_table_queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS iptv_lists (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            list_url TEXT NOT NULL,
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        # Aggiungi qui tutte le altre tabelle necessarie
    ]
    pool = await get_pool()
    async with pool.acquire() as conn:
        for query in create_table_queries:
            await conn.execute(query)
    logger.info("Tabelle verificate/crete")
