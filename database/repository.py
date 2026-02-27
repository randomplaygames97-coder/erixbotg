"""
Repository per l'accesso ai dati del database

Contiene tutte le operazioni CRUD per utenti, liste IPTV, richieste rinnovo e FAQ.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
import aiosqlite
from config.database import db_manager


# ==================== USER REPOSITORY ====================

class UserRepository:
    """Repository per la gestione degli utenti."""
    
    @staticmethod
    async def create_or_update(
        telegram_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
        is_admin: bool = False
    ) -> bool:
        """Crea o aggiorna un utente."""
        db = await db_manager.get_connection()
        try:
            await db.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    is_admin = excluded.is_admin,
                    updated_at = CURRENT_TIMESTAMP
            """, (telegram_id, username, first_name, last_name, is_admin))
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_by_id(telegram_id: int) -> Optional[Dict[str, Any]]:
        """Ottiene un utente per ID."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_all(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Ottiene tutti gli utenti."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_registered_users() -> List[Dict[str, Any]]:
        """Ottiene tutti gli utenti registrati."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT * FROM users WHERE is_registered = TRUE ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def set_registered(telegram_id: int, is_registered: bool) -> bool:
        """Aggiorna lo stato di registrazione dell'utente."""
        db = await db_manager.get_connection()
        try:
            await db.execute(
                "UPDATE users SET is_registered = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                (is_registered, telegram_id)
            )
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def count() -> int:
        """Conta il totale degli utenti."""
        db = await db_manager.get_connection()
        try:
            async with db.execute("SELECT COUNT(*) as count FROM users") as cursor:
                row = await cursor.fetchone()
                return row['count'] if row else 0
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def count_registered() -> int:
        """Conta gli utenti registrati."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_registered = TRUE"
            ) as cursor:
                row = await cursor.fetchone()
                return row['count'] if row else 0
        finally:
            await db_manager.close_connection(db)


# ==================== IPTV LIST REPOSITORY ====================

class IPTVListRepository:
    """Repository per la gestione delle liste IPTV."""
    
    @staticmethod
    async def create(
        user_id: int,
        list_name: str,
        list_id: Optional[str] = None,
        m3u_url: Optional[str] = None,
        xmltv_url: Optional[str] = None,
        expiry_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[int]:
        """Crea una nuova lista IPTV."""
        db = await db_manager.get_connection()
        try:
            cursor = await db.execute("""
                INSERT INTO iptv_lists 
                (user_id, list_name, list_id, m3u_url, xmltv_url, expiry_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, list_name, list_id, m3u_url, xmltv_url, expiry_date, notes))
            await db.commit()
            return cursor.lastrowid
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def update(
        list_id: int,
        list_name: Optional[str] = None,
        list_id_value: Optional[str] = None,
        m3u_url: Optional[str] = None,
        xmltv_url: Optional[str] = None,
        expiry_date: Optional[str] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Aggiorna una lista IPTV."""
        db = await db_manager.get_connection()
        try:
            # Costruisci la query dinamicamente
            updates = []
            params = []
            
            if list_name is not None:
                updates.append("list_name = ?")
                params.append(list_name)
            if list_id_value is not None:
                updates.append("list_id = ?")
                params.append(list_id_value)
            if m3u_url is not None:
                updates.append("m3u_url = ?")
                params.append(m3u_url)
            if xmltv_url is not None:
                updates.append("xmltv_url = ?")
                params.append(xmltv_url)
            if expiry_date is not None:
                updates.append("expiry_date = ?")
                params.append(expiry_date)
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(list_id)
            
            query = f"UPDATE iptv_lists SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, params)
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_by_id(id: int) -> Optional[Dict[str, Any]]:
        """Ottiene una lista IPTV per ID."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT * FROM iptv_lists WHERE id = ?", (id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        """Ottiene tutte le liste IPTV di un utente."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT * FROM iptv_lists WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_active_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Ottiene la lista IPTV attiva di un utente."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT * FROM iptv_lists 
                   WHERE user_id = ? AND status = 'active' 
                   ORDER BY created_at DESC LIMIT 1""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db_manager.close_connection(db)

    @staticmethod
    async def get_active_with_expiry() -> List[Dict[str, Any]]:
        """Ottiene tutte le liste attive con data di scadenza valorizzata."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT il.*, u.first_name, u.username
                   FROM iptv_lists il
                   INNER JOIN users u ON u.telegram_id = il.user_id
                   WHERE il.status = 'active' AND il.expiry_date IS NOT NULL
                   ORDER BY il.expiry_date ASC"""
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def delete(id: int) -> bool:
        """Elimina una lista IPTV."""
        db = await db_manager.get_connection()
        try:
            await db.execute("DELETE FROM iptv_lists WHERE id = ?", (id,))
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def update_expiry_date(list_id: int, expiry_date: str) -> bool:
        """Aggiorna la data di scadenza di una lista."""
        db = await db_manager.get_connection()
        try:
            await db.execute(
                """UPDATE iptv_lists 
                   SET expiry_date = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (expiry_date, list_id)
            )
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)


# ==================== RENEWAL REQUEST REPOSITORY ====================

class RenewalRequestRepository:
    """Repository per la gestione delle richieste di rinnovo."""
    
    @staticmethod
    async def create(
        user_id: int,
        list_id: Optional[int] = None
    ) -> Optional[int]:
        """Crea una nuova richiesta di rinnovo."""
        db = await db_manager.get_connection()
        try:
            cursor = await db.execute("""
                INSERT INTO renewal_requests (user_id, list_id, status)
                VALUES (?, ?, 'pending')
            """, (user_id, list_id))
            await db.commit()
            return cursor.lastrowid
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_by_id(id: int) -> Optional[Dict[str, Any]]:
        """Ottiene una richiesta di rinnovo per ID."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT rr.*, u.first_name, u.username, u.telegram_id,
                          il.list_name, il.expiry_date
                   FROM renewal_requests rr
                   LEFT JOIN users u ON rr.user_id = u.telegram_id
                   LEFT JOIN iptv_lists il ON rr.list_id = il.id
                   WHERE rr.id = ?""",
                (id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_pending() -> List[Dict[str, Any]]:
        """Ottiene tutte le richieste di rinnovo pendenti."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT rr.*, u.first_name, u.username, u.telegram_id,
                          il.list_name, il.expiry_date
                   FROM renewal_requests rr
                   LEFT JOIN users u ON rr.user_id = u.telegram_id
                   LEFT JOIN iptv_lists il ON rr.list_id = il.id
                   WHERE rr.status = 'pending'
                   ORDER BY rr.request_date DESC"""
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)

    @staticmethod
    async def get_by_status(
        status: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Ottiene richieste per stato con paginazione."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT rr.*, u.first_name, u.username, u.telegram_id,
                          il.list_name, il.expiry_date
                   FROM renewal_requests rr
                   LEFT JOIN users u ON rr.user_id = u.telegram_id
                   LEFT JOIN iptv_lists il ON rr.list_id = il.id
                   WHERE rr.status = ?
                   ORDER BY rr.request_date DESC
                   LIMIT ? OFFSET ?""",
                (status, limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        """Ottiene tutte le richieste di rinnovo di un utente."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT rr.*, il.list_name
                   FROM renewal_requests rr
                   LEFT JOIN iptv_lists il ON rr.list_id = il.id
                   WHERE rr.user_id = ?
                   ORDER BY rr.request_date DESC""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def approve(
        id: int,
        admin_id: int,
        new_expiry_date: Optional[str] = None,
        admin_notes: Optional[str] = None
    ) -> bool:
        """Approva una richiesta di rinnovo."""
        db = await db_manager.get_connection()
        try:
            # Aggiorna lo stato della richiesta
            await db.execute(
                """UPDATE renewal_requests 
                   SET status = 'approved', 
                       processed_by = ?, 
                       processed_at = CURRENT_TIMESTAMP,
                       admin_notes = ?
                   WHERE id = ?""",
                (admin_id, admin_notes, id)
            )
            
            # Se è stata fornita una nuova data di scadenza, aggiorna la lista
            if new_expiry_date:
                # Prima ottieni la list_id dalla richiesta
                async with db.execute(
                    "SELECT list_id FROM renewal_requests WHERE id = ?", (id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row and row['list_id']:
                        await db.execute(
                            """UPDATE iptv_lists 
                               SET expiry_date = ?, updated_at = CURRENT_TIMESTAMP 
                               WHERE id = ?""",
                            (new_expiry_date, row['list_id'])
                        )
            
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def reject(
        id: int,
        admin_id: int,
        admin_notes: str
    ) -> bool:
        """Rifiuta una richiesta di rinnovo."""
        db = await db_manager.get_connection()
        try:
            await db.execute(
                """UPDATE renewal_requests 
                   SET status = 'rejected', 
                       processed_by = ?, 
                       processed_at = CURRENT_TIMESTAMP,
                       admin_notes = ?
                   WHERE id = ?""",
                (admin_id, admin_notes, id)
            )
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def count_pending() -> int:
        """Conta le richieste pendenti."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT COUNT(*) as count FROM renewal_requests WHERE status = 'pending'"
            ) as cursor:
                row = await cursor.fetchone()
                return row['count'] if row else 0
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def count_by_status(status: str) -> int:
        """Conta le richieste per stato."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT COUNT(*) as count FROM renewal_requests WHERE status = ?",
                (status,)
            ) as cursor:
                row = await cursor.fetchone()
                return row['count'] if row else 0
        finally:
            await db_manager.close_connection(db)

    @staticmethod
    async def count_all() -> int:
        """Conta il totale delle richieste di rinnovo."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT COUNT(*) as count FROM renewal_requests"
            ) as cursor:
                row = await cursor.fetchone()
                return row['count'] if row else 0
        finally:
            await db_manager.close_connection(db)


# ==================== EXPIRY NOTIFICATION REPOSITORY ====================

class ExpiryNotificationRepository:
    """Repository per il tracciamento notifiche scadenza inviate."""

    @staticmethod
    async def exists(list_id: int, notification_type: str, sent_for_date: str) -> bool:
        """Verifica se la notifica e gia stata inviata."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT 1
                   FROM expiry_notifications
                   WHERE list_id = ? AND notification_type = ? AND sent_for_date = ?
                   LIMIT 1""",
                (list_id, notification_type, sent_for_date)
            ) as cursor:
                return (await cursor.fetchone()) is not None
        finally:
            await db_manager.close_connection(db)

    @staticmethod
    async def mark_sent(
        user_id: int,
        list_id: int,
        notification_type: str,
        sent_for_date: str
    ) -> bool:
        """Marca la notifica come inviata."""
        db = await db_manager.get_connection()
        try:
            cursor = await db.execute(
                """INSERT OR IGNORE INTO expiry_notifications
                   (user_id, list_id, notification_type, sent_for_date)
                   VALUES (?, ?, ?, ?)""",
                (user_id, list_id, notification_type, sent_for_date)
            )
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db_manager.close_connection(db)


# ==================== FAQ REPOSITORY ====================

class FAQRepository:
    """Repository per la gestione delle FAQ."""
    
    @staticmethod
    async def get_all() -> List[Dict[str, Any]]:
        """Ottiene tutte le FAQ ordinate per categoria e priorità."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT * FROM faq_data 
                   ORDER BY category, priority DESC, question"""
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_by_category(category: str) -> List[Dict[str, Any]]:
        """Ottiene le FAQ per categoria."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                """SELECT * FROM faq_data 
                   WHERE category = ? ORDER BY priority DESC, question""",
                (category,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_categories() -> List[str]:
        """Ottiene le categorie FAQ disponibili."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT DISTINCT category FROM faq_data ORDER BY category"
            ) as cursor:
                rows = await cursor.fetchall()
                return [row['category'] for row in rows]
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def get_by_id(id: int) -> Optional[Dict[str, Any]]:
        """Ottiene una FAQ per ID."""
        db = await db_manager.get_connection()
        try:
            async with db.execute(
                "SELECT * FROM faq_data WHERE id = ?", (id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def create(
        category: str,
        question: str,
        answer: str,
        priority: int = 0
    ) -> Optional[int]:
        """Crea una nuova FAQ."""
        db = await db_manager.get_connection()
        try:
            cursor = await db.execute(
                """INSERT INTO faq_data (category, question, answer, priority)
                   VALUES (?, ?, ?, ?)""",
                (category, question, answer, priority)
            )
            await db.commit()
            return cursor.lastrowid
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def update(
        id: int,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        priority: Optional[int] = None
    ) -> bool:
        """Aggiorna una FAQ."""
        db = await db_manager.get_connection()
        try:
            updates = []
            params = []
            
            if question is not None:
                updates.append("question = ?")
                params.append(question)
            if answer is not None:
                updates.append("answer = ?")
                params.append(answer)
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            
            if not updates:
                return False
            
            params.append(id)
            query = f"UPDATE faq_data SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, params)
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
    
    @staticmethod
    async def delete(id: int) -> bool:
        """Elimina una FAQ."""
        db = await db_manager.get_connection()
        try:
            await db.execute("DELETE FROM faq_data WHERE id = ?", (id,))
            await db.commit()
            return True
        finally:
            await db_manager.close_connection(db)
