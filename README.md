# Bot Telegram IPTV Manager

Bot Telegram per la gestione automatizzata di un servizio IPTV.

## Caratteristiche

- 📝 Registrazione liste IPTV
- 📡 Visualizzazione stato e data di scadenza
- 🔄 Richieste di rinnovo automatiche
- ❓ Sistema FAQ e troubleshooting
- ⚙️ Pannello admin per gestione rinnovi

## Struttura del Progetto

```
iptv_bot/
├── config/          # Configurazione (admin, settings, database)
├── database/        # Schema e repository SQLite
├── handlers/        # Gestione comandi e callback
├── keyboards/       # Tastiere inline
├── services/        # Logica di business
├── main.py          # Entry point del bot
├── requirements.txt # Dipendenze Python
└── .env.example     # Template configurazione
```

## Installazione

1. Clona il repository
2. Copia `.env.example` in `.env` e configura:
   - `TELEGRAM_BOT_TOKEN` - Token del bot
   - `ADMIN_IDS` - ID admin separati da virgola
3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
4. Esegui il bot:
   ```bash
   python main.py
   ```

## Comandi Utente

| Comando | Descrizione |
|---------|-------------|
| `/start` | Messaggio di benvenuto |
| `/help` | Guida ai comandi |
| `/registra` | Registra la tua lista IPTV |
| `/info` | Visualizza info linea |
| `/rinnova` | Richiedi rinnovo |
| `/faq` | FAQ e troubleshooting |
| `/annulla` | Annulla operazione |

## Comandi Admin

| Comando | Descrizione |
|---------|-------------|
| `/admin` | Pannello admin |

## Requisiti

- Python 3.10+
- python-telegram-bot 20+
- aiosqlite
- python-dotenv
- loguru
