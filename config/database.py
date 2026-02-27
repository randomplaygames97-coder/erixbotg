"""
Configurazione Database

Gestisce la connessione al database SQLite.
"""

import os
import aiosqlite
from typing import Optional
from config.settings import config


class DatabaseManager:
    """Gestore della connessione al database."""
    
    _instance: Optional['DatabaseManager'] = None
    _db_path: str = ""
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db_path = config.database_path
        return cls._instance
    
    async def get_connection(self) -> aiosqlite.Connection:
        """Ottiene una connessione al database."""
        # Assicurati che la directory esista
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        db = await aiosqlite.connect(self._db_path)
        db.row_factory = aiosqlite.Row
        return db
    
    async def close_connection(self, db: aiosqlite.Connection):
        """Chiude la connessione al database."""
        if db:
            await db.close()


# Istanza globale del gestore database
db_manager = DatabaseManager()


async def get_db() -> aiosqlite.Connection:
    """Dependency per ottenere una connessione al database."""
    return await db_manager.get_connection()
