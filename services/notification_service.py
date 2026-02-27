"""Servizi notifiche automatiche (scadenze e reminder)."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional, Tuple

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from database.repository import ExpiryNotificationRepository, IPTVListRepository
from utils.security import escape_html, mask_telegram_id

logger = logging.getLogger(__name__)


class ExpiryNotificationService:
    """Gestione notifiche automatiche su scadenza liste IPTV."""

    REMINDER_DAYS = {7, 3, 1}

    @staticmethod
    def _resolve_notification(days_left: int) -> Tuple[Optional[str], Optional[str]]:
        """Mappa giorni residui -> tipo notifica e prefisso messaggio."""
        if days_left in ExpiryNotificationService.REMINDER_DAYS:
            return f"reminder_{days_left}", f"⏰ <b>Promemoria scadenza</b>\n\nLa tua lista scade tra <b>{days_left}</b> giorni."

        if days_left == -1:
            return "expired", "⛔ <b>Lista scaduta</b>\n\nLa tua lista IPTV risulta scaduta."

        return None, None

    @staticmethod
    async def send_expiry_notifications(bot: Bot) -> None:
        """Invia notifiche automatiche per liste in scadenza/scadute."""
        today = date.today()
        sent_for_date = today.isoformat()
        active_lists = await IPTVListRepository.get_active_with_expiry()

        for iptv_list in active_lists:
            expiry_raw = iptv_list.get("expiry_date")
            if not expiry_raw:
                continue

            try:
                expiry_date = datetime.strptime(expiry_raw, "%Y-%m-%d").date()
            except ValueError:
                continue

            days_left = (expiry_date - today).days
            notification_type, header = ExpiryNotificationService._resolve_notification(days_left)
            if not notification_type or not header:
                continue

            list_id = iptv_list["id"]
            user_id = iptv_list["user_id"]

            if await ExpiryNotificationRepository.exists(list_id, notification_type, sent_for_date):
                continue

            list_name = escape_html(iptv_list.get("list_name", "N/A"))
            message = (
                f"{header}\n\n"
                f"📌 <b>Lista:</b> {list_name}\n"
                f"📅 <b>Data scadenza:</b> {expiry_raw}\n\n"
                "Usa /rinnova per inviare una richiesta di rinnovo."
            )

            try:
                await bot.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.HTML)
            except TelegramError as exc:
                logger.warning(
                    "Failed sending expiry notification user_id=%s list_id=%s type=%s error=%s",
                    mask_telegram_id(user_id),
                    list_id,
                    notification_type,
                    type(exc).__name__,
                )
                continue

            await ExpiryNotificationRepository.mark_sent(
                user_id=user_id,
                list_id=list_id,
                notification_type=notification_type,
                sent_for_date=sent_for_date,
            )

            # Dopo il primo giorno dalla scadenza aggiorniamo automaticamente lo stato lista.
            if notification_type == "expired":
                await IPTVListRepository.update(list_id=list_id, status="expired")

