"""Helper Telegram riusabili (rate-limit e invio sicuro)."""

from __future__ import annotations

import logging
from typing import Any

from telegram import Update
from telegram.error import TelegramError

from utils.rate_limiter import rate_limiter
from utils.security import mask_telegram_id

logger = logging.getLogger(__name__)


async def reject_if_rate_limited(
    update: Update,
    scope: str,
    cooldown_seconds: float = 1.5,
) -> bool:
    """
    Applica rate limit su update utente.

    Returns:
        True se la richiesta e stata bloccata.
    """
    user = update.effective_user
    if not user:
        return False

    if not rate_limiter.is_limited(user.id, scope, cooldown_seconds):
        return False

    if update.callback_query:
        try:
            await update.callback_query.answer(
                "Troppi tentativi ravvicinati. Riprova tra pochi secondi."
            )
        except TelegramError:
            pass
        return True

    message = update.effective_message
    if message:
        try:
            await message.reply_text("⏳ Troppi comandi ravvicinati. Riprova tra pochi secondi.")
        except TelegramError:
            pass

    return True


async def safe_send_message(bot: Any, chat_id: int, text: str, **kwargs: Any) -> bool:
    """
    Invia messaggio Telegram in modo sicuro.

    Returns:
        True se inviato con successo.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return True
    except TelegramError as exc:
        logger.warning(
            "Telegram send_message failed chat_id=%s error_type=%s",
            mask_telegram_id(chat_id),
            type(exc).__name__,
        )
        return False

