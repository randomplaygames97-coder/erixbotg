"""
Entry point bot IPTV Telegram.
"""

from __future__ import annotations

import logging
import os
import sys

from telegram import Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
)

from config.settings import config
from database.schema import init_database
from handlers.admin import get_admin_handlers
from handlers.callbacks import get_callback_handlers
from handlers.commands import (
    annulla_command,
    faq_command,
    get_registration_handler,
    help_command,
    info_command,
    rinnova_command,
    start_command,
)
from services.notification_service import ExpiryNotificationService
from utils.security import mask_telegram_id

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configura logging applicativo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def expiry_notifications_job(context: ContextTypes.DEFAULT_TYPE):
    """Job periodico per reminder scadenze."""
    await ExpiryNotificationService.send_expiry_notifications(context.bot)


async def post_init(application: Application):
    """Callback eseguito dopo init application."""
    print(f"\nBot avviato: {config.bot_name} v{config.bot_version}")
    print(f"Token configurato: {'Si' if config.token else 'NO'}")
    print(f"Admin configurati: {len(config.admin_ids)}")
    print(f"Database: {config.database_path}")

    print("\nInizializzazione database...")
    success = await init_database()

    if success:
        print("Database inizializzato correttamente.")
    else:
        print("Errore nell'inizializzazione database.")

    if application.job_queue:
        application.job_queue.run_repeating(
            expiry_notifications_job,
            interval=3600,
            first=20,
            name="expiry_notifications",
        )
        print("Scheduler notifiche scadenza attivo (ogni 60 minuti).")
    else:
        print("JobQueue non disponibile: scheduler notifiche disattivato.")


async def post_shutdown(application: Application):
    """Callback shutdown."""
    print("\nArresto bot in corso...")
    print("Bot arrestato correttamente.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Gestione errori globale con logging sicuro."""
    error = context.error

    if isinstance(error, BadRequest) and "Message is not modified" in str(error):
        return

    user_id = None
    if isinstance(update, Update) and update.effective_user:
        user_id = update.effective_user.id

    logger.exception(
        "Unhandled exception error_type=%s user_id=%s",
        type(error).__name__,
        mask_telegram_id(user_id),
    )

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Si e verificato un errore temporaneo. Riprova tra poco."
            )
        except TelegramError:
            pass



def main():
    """Avvio principale bot."""
    configure_logging()

    if not config.token:
        print("ERRORE: token bot non configurato.")
        print("Crea un file .env con TELEGRAM_BOT_TOKEN=...")
        sys.exit(1)

    if not config.admin_ids:
        print("AVVISO: nessun admin configurato.")

    db_dir = os.path.dirname(config.database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    persistence_path = "./data/conversation.pickle"
    persistence_dir = os.path.dirname(persistence_path)
    if persistence_dir and not os.path.exists(persistence_dir):
        os.makedirs(persistence_dir, exist_ok=True)

    persistence = PicklePersistence(filepath=persistence_path)

    application = (
        Application.builder()
        .token(config.token)
        .persistence(persistence)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    application.add_error_handler(error_handler)

    print("\nRegistrazione handlers...")

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("aiuto", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("stato", info_command))
    application.add_handler(CommandHandler("linea", info_command))
    application.add_handler(CommandHandler("rinnova", rinnova_command))
    application.add_handler(CommandHandler("renew", rinnova_command))
    application.add_handler(CommandHandler("faq", faq_command))
    application.add_handler(CommandHandler("problemi", faq_command))
    application.add_handler(CommandHandler("annulla", annulla_command))
    application.add_handler(CommandHandler("cancel", annulla_command))

    application.add_handler(get_registration_handler())

    for handler in get_callback_handlers():
        application.add_handler(handler)

    for handler in get_admin_handlers():
        application.add_handler(handler)

    print("Handlers registrati.")
    print("\nAvvio bot in polling...")

    try:
        application.run_polling(
            allowed_updates=["message", "edited_message", "callback_query"]
        )
    except KeyboardInterrupt:
        print("\nArresto richiesto dall'utente.")
    except Exception:
        logger.exception("Fatal error during bot execution")
        print("Errore durante l'esecuzione del bot.")
        sys.exit(1)


if __name__ == "__main__":
    main()
