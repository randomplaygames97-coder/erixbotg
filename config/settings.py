"""
Configurazione centralizzata del Bot IPTV

Carica le impostazioni da variabili d'ambiente.
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Carica variabili d'ambiente dal file .env
load_dotenv()


@dataclass
class BotConfig:
    """Configurazione principale del bot."""
    token: str
    database_path: str
    admin_ids: List[int]
    super_admin_id: int
    bot_name: str
    bot_version: str
    debug_mode: bool
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Carica la configurazione dalle variabili d'ambiente."""
        # Carica admin_ids da config.admin_ids
        from config.admin_ids import ADMIN_IDS, SUPER_ADMIN_ID
        
        # Leggi da env (override possibile)
        env_admin_ids = os.getenv('ADMIN_IDS', '')
        if env_admin_ids:
            try:
                admin_ids = [int(x) for x in env_admin_ids.split(',') if x.strip()]
            except ValueError:
                admin_ids = ADMIN_IDS
        else:
            admin_ids = ADMIN_IDS
        
        # Super admin ha la priorità
        env_super_admin = os.getenv('SUPER_ADMIN_ID')
        if env_super_admin:
            super_admin_id = int(env_super_admin)
        else:
            super_admin_id = SUPER_ADMIN_ID
        
        return cls(
            token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            database_path=os.getenv('DATABASE_PATH', './data/iptv_bot.db'),
            admin_ids=admin_ids,
            super_admin_id=super_admin_id,
            bot_name=os.getenv('BOT_NAME', 'IPTV Manager Bot'),
            bot_version=os.getenv('BOT_VERSION', '1.0.0'),
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        )
    
    def is_admin(self, telegram_id: int) -> bool:
        """Verifica se l'utente è un admin."""
        return telegram_id in self.admin_ids
    
    def is_super_admin(self, telegram_id: int) -> bool:
        """Verifica se l'utente è il super admin."""
        return telegram_id == self.super_admin_id


# Istanza globale della configurazione
config = BotConfig.from_env()
