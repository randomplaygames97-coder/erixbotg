"""
Tastiera del menu principale

Definisce la tastiera inline per il menu principale del bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard(is_registered: bool = False) -> InlineKeyboardMarkup:
    """
    Restituisce la tastiera del menu principale.
    
    Args:
        is_registered: Se True, mostra le opzioni per utenti registrati
    
    Returns:
        InlineKeyboardMarkup con le opzioni del menu
    """
    keyboard = []
    
    # Prima riga - Azioni principali
    keyboard.append([
        InlineKeyboardButton("📝 Registra Lista", callback_data="menu_registra"),
    ])
    
    # Seconda riga - Info e Rinnovo (solo per registrati)
    if is_registered:
        keyboard.append([
            InlineKeyboardButton("📡 Info Linea", callback_data="menu_info"),
            InlineKeyboardButton("🔄 Rinnova", callback_data="menu_rinnova"),
        ])
    
    # Terza riga - FAQ
    keyboard.append([
        InlineKeyboardButton("❓ FAQ & Troubleshooting", callback_data="menu_faq"),
    ])
    
    # Quarta riga - Help
    keyboard.append([
        InlineKeyboardButton("❓ Aiuto", callback_data="menu_help"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Restituisce la tastiera iniziale dopo /start."""
    keyboard = [
        [
            InlineKeyboardButton("📝 Registra Lista IPTV", callback_data="menu_registra"),
        ],
        [
            InlineKeyboardButton("❓ FAQ", callback_data="menu_faq"),
            InlineKeyboardButton("❓ Aiuto", callback_data="menu_help"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_registration_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per la procedura di registrazione."""
    keyboard = [
        [
            InlineKeyboardButton("❌ Annulla", callback_data="registra_annulla"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_renewal_confirm_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per confermare la richiesta di rinnovo."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Conferma", callback_data="renewal_confirm"),
            InlineKeyboardButton("❌ Annulla", callback_data="renewal_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per tornare al menu principale."""
    keyboard = [
        [
            InlineKeyboardButton("🔙 Menu Principale", callback_data="menu_main"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_info_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per il menu info."""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Aggiorna", callback_data="info_refresh"),
        ],
        [
            InlineKeyboardButton("🔙 Menu Principale", callback_data="menu_main"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

