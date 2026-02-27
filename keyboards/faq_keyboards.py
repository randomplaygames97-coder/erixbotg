"""
Tastiere per le FAQ

Definisce le tastiere inline per la navigazione delle FAQ.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.faq_service import FAQService


async def get_faq_categories_keyboard() -> InlineKeyboardMarkup:
    """
    Restituisce la tastiera con le categorie FAQ.
    
    Returns:
        InlineKeyboardMarkup con le categorie FAQ
    """
    keyboard = []
    
    # Ottieni le informazioni sulle categorie
    categories = FAQService.get_all_category_info()
    
    # Crea le righe (2 per volta)
    items = list(categories.items())
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                cat_key, info = items[i + j]
                emoji = info.get('emoji', '📌')
                name = info.get('name', cat_key.title())
                row.append(InlineKeyboardButton(
                    f"{emoji} {name}",
                    callback_data=f"faq_{cat_key}"
                ))
        keyboard.append(row)
    
    # Pulsante per tornare al menu principale
    keyboard.append([
        InlineKeyboardButton("🔙 Menu Principale", callback_data="menu_main"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def get_faq_detail_keyboard(category: str) -> InlineKeyboardMarkup:
    """
    Restituisce la tastiera per il dettaglio FAQ.
    
    Args:
        category: Categoria della FAQ
    
    Returns:
        InlineKeyboardMarkup con opzioni per la FAQ
    """
    keyboard = [
        [
            InlineKeyboardButton("🔙 Categorie FAQ", callback_data="faq_back"),
        ],
        [
            InlineKeyboardButton("🔙 Menu Principale", callback_data="menu_main"),
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_faq_category_button(category: str) -> InlineKeyboardButton:
    """Crea un pulsante per una categoria FAQ."""
    info = FAQService.CATEGORY_INFO.get(category, {})
    emoji = info.get('emoji', '📌')
    name = info.get('name', category.title())
    
    return InlineKeyboardButton(
        f"{emoji} {name}",
        callback_data=f"faq_{category}"
    )
