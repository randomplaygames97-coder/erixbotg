"""
Schema del Database SQLite

Definisce tutte le tabelle e le operazioni di inizializzazione del database.
"""

from typing import Optional
import aiosqlite
from config.database import db_manager


# SQL per la creazione delle tabelle
CREATE_TABLES_SQL = """
-- Tabella utenti
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NULL,
    is_registered BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabella liste IPTV
CREATE TABLE IF NOT EXISTS iptv_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    list_name VARCHAR(255) NOT NULL,
    list_id VARCHAR(255) NULL,
    m3u_url TEXT NULL,
    xmltv_url TEXT NULL,
    expiry_date DATE NULL,
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- Tabella richieste rinnovo
CREATE TABLE IF NOT EXISTS renewal_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    list_id INTEGER NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    admin_notes TEXT NULL,
    processed_by BIGINT NULL,
    processed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (list_id) REFERENCES iptv_lists(id) ON DELETE SET NULL
);

-- Tabella FAQ
CREATE TABLE IF NOT EXISTS faq_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracciamento notifiche scadenza inviate
CREATE TABLE IF NOT EXISTS expiry_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    list_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    sent_for_date DATE NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (list_id) REFERENCES iptv_lists(id) ON DELETE CASCADE,
    UNIQUE(list_id, notification_type, sent_for_date)
);

-- Indici per migliorare le performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_lists_user_id ON iptv_lists(user_id);
CREATE INDEX IF NOT EXISTS idx_renewal_status ON renewal_requests(status);
CREATE INDEX IF NOT EXISTS idx_renewal_user_id ON renewal_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_data(category);
CREATE INDEX IF NOT EXISTS idx_expiry_notifications_user ON expiry_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_expiry_notifications_type_date ON expiry_notifications(notification_type, sent_for_date);
"""

# SQL per inserire le FAQ iniziali
INSERT_DEFAULT_FAQS = """
INSERT OR IGNORE INTO faq_data (category, question, answer, priority) VALUES
-- Buffering
('buffering', 'Il canale fa buffering continuo', 
 '🔄 <b>Soluzioni buffering:</b>\n\n'
 '1. Verifica la tua connessione internet (minimo 10Mbps)\n'
 '2. Prova un altro canale per verificare se è un problema locale\n'
 '3. Riavvia l''app/IPTV\n'
 '4. Riavvia il dispositivo\n'
 '5. Controlla se altri dispositivi nella rete stanno scaricando/streaming\n'
 '6. Prova a usare un cavo Ethernet invece del WiFi\n'
 '7. Prova a ridurre la qualità del canale', 1),

-- Canali
('canali', 'Un canale non funziona',
 '📺 <b>Soluzioni canali non funzionanti:</b>\n\n'
 '1. Verifica che il canale sia nella tua lista\n'
 '2. Prova a fare refresh della lista (esci e rientra)\n'
 '3. Controlla se il canale è in manutenzione dal provider\n'
 '4. Prova a cercare il canale con un nome diverso\n'
 '5. Verifica che la tua lista non sia scaduta (/info)', 1),

-- Connessione
('connessione', 'Non riesco a connettermi',
 '🌐 <b>Soluzioni problemi di connessione:</b>\n\n'
 '1. Verifica che la tua lista non sia scaduta (/info)\n'
 '2. Controlla le credenziali di accesso\n'
 '3. Verifica che l''URL della lista sia corretto\n'
 '4. Prova a disattivare VPN o proxy\n'
 '5. Contatta il supporto se il problema persiste', 1),

-- Account
('account', 'Problemi con l''account o abbonamento',
 '👤 <b>Soluzioni problemi account:</b>\n\n'
 '1. Verifica lo stato del tuo abbonamento con /info\n'
 '2. Se è scaduto, richiedi il rinnovo con /rinnova\n'
 '3. Controlla di stare usando le credenziali corrette\n'
 '4. Prova a riattivare la lista uscendo e rientrando', 1),

-- App
('app', 'Problemi con l''applicazione IPTV',
 '📱 <b>Soluzioni problemi app:</b>\n\n'
 '1. Aggiorna l''app all''ultima versione\n'
 '2. Cancella la cache dell''app\n'
 '3. Disinstalla e reinstalla l''app\n'
 '4. Prova un''altra app IPTV (es. IPTV Smarters, GSE Smart IPTV)\n'
 '5. Verifica che il formato della lista sia compatibile', 1);
"""


async def init_database() -> bool:
    """
    Inizializza il database creando le tabelle se non esistono
    e inserendo i dati di default.
    
    Returns:
        True se l'inizializzazione è avvenuta con successo
    """
    db = await db_manager.get_connection()
    try:
        # Crea le tabelle
        await db.executescript(CREATE_TABLES_SQL)
        
        # Inserisci le FAQ di default
        await db.executescript(INSERT_DEFAULT_FAQS)
        
        await db.commit()
        return True
    except Exception as e:
        print(f"Errore nell'inizializzazione del database: {e}")
        return False
    finally:
        await db_manager.close_connection(db)


async def get_db_version() -> Optional[str]:
    """Ottiene la versione del database SQLite."""
    db = await db_manager.get_connection()
    try:
        async with db.execute_query("SELECT sqlite_version() as version") as cursor:
            row = await cursor.fetchone()
            return row['version'] if row else None
    finally:
        await db_manager.close_connection(db)
