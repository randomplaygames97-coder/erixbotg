"""
Configurazione ID Admin Telegram

Inserisci gli ID Telegram degli admin autorizzati a gestire il bot.
Per trovare il tuo ID Telegram, scrivi a @userinfobot su Telegram.
"""

# Lista di ID Telegram autorizzati come admin
ADMIN_IDS = [
    # Esempio: 123456789,  # Inserisci il tuo ID qui
]

# ID del proprietario/super admin (ha accesso a tutte le funzionalità)
SUPER_ADMIN_ID = None  # Inserisci il tuo ID qui


def is_admin(telegram_id: int) -> bool:
    """Verifica se un utente è un admin."""
    return telegram_id in ADMIN_IDS


def is_super_admin(telegram_id: int) -> bool:
    """Verifica se un utente è il super admin."""
    return telegram_id == SUPER_ADMIN_ID
