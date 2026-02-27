"""
Servizio per la gestione delle FAQ e troubleshooting

Fornisce metodi per recuperare e gestire le FAQ dal database.
"""

from typing import List, Dict, Any, Optional
from database.repository import FAQRepository


class FAQService:
    """Servizio per la gestione delle FAQ."""
    
    # Mappatura categorie -> emoji e nome visualizzato
    CATEGORY_INFO = {
        'buffering': {'emoji': '🔄', 'name': 'Buffering', 'description': 'Problemi di buffering'},
        'canali': {'emoji': '📺', 'name': 'Canali', 'description': 'Canali non funzionanti'},
        'connessione': {'emoji': '🌐', 'name': 'Connessione', 'description': 'Problemi di connessione'},
        'account': {'emoji': '👤', 'name': 'Account', 'description': 'Problemi account/abbonamento'},
        'app': {'emoji': '📱', 'name': 'App', 'description': 'Problemi con app IPTV'}
    }
    
    @staticmethod
    async def get_all_faqs() -> List[Dict[str, Any]]:
        """Ottiene tutte le FAQ."""
        return await FAQRepository.get_all()
    
    @staticmethod
    async def get_faqs_by_category(category: str) -> List[Dict[str, Any]]:
        """Ottiene le FAQ per categoria."""
        return await FAQRepository.get_by_category(category)
    
    @staticmethod
    async def get_categories() -> List[str]:
        """Ottiene le categorie disponibili."""
        return await FAQRepository.get_categories()
    
    @staticmethod
    async def get_category_info(category: str) -> Optional[Dict[str, str]]:
        """Ottiene le informazioni di una categoria."""
        return FAQService.CATEGORY_INFO.get(category)
    
    @staticmethod
    def get_all_category_info() -> Dict[str, Dict[str, str]]:
        """Ottiene tutte le informazioni delle categorie."""
        return FAQService.CATEGORY_INFO
    
    @staticmethod
    async def format_faq_list(category: str) -> str:
        """Formatta la lista delle FAQ per una categoria."""
        faqs = await FAQRepository.get_faqs_by_category(category)
        
        if not faqs:
            return "Nessuna FAQ disponibile per questa categoria."
        
        category_info = FAQService.CATEGORY_INFO.get(category, {})
        emoji = category_info.get('emoji', '❓')
        name = category_info.get('name', category.title())
        
        text = f"{emoji} <b>FAQ - {name}</b>\n\n"
        
        for faq in faqs:
            text += f"❓ <b>{faq['question']}</b>\n"
            text += f"{faq['answer']}\n\n"
        
        return text
    
    @staticmethod
    async def format_faq_categories() -> str:
        """Formatta la lista delle categorie FAQ."""
        categories = await FAQService.get_categories()
        
        text = "📚 <b>Categorie FAQ</b>\n\n"
        text += "Scegli una categoria per vedere le soluzioni:\n\n"
        
        for cat in categories:
            info = FAQService.CATEGORY_INFO.get(cat, {})
            emoji = info.get('emoji', '📌')
            name = info.get('name', cat.title())
            desc = info.get('description', '')
            text += f"{emoji} <b>{name}</b> - {desc}\n"
        
        return text
    
    @staticmethod
    async def create_faq(
        category: str,
        question: str,
        answer: str,
        priority: int = 0
    ) -> Optional[int]:
        """Crea una nuova FAQ."""
        return await FAQRepository.create(category, question, answer, priority)
    
    @staticmethod
    async def update_faq(
        id: int,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        priority: Optional[int] = None
    ) -> bool:
        """Aggiorna una FAQ."""
        return await FAQRepository.update(id, question, answer, priority)
    
    @staticmethod
    async def delete_faq(id: int) -> bool:
        """Elimina una FAQ."""
        return await FAQRepository.delete(id)
