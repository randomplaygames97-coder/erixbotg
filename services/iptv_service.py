"""
Servizi business IPTV e rinnovi.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from database.repository import IPTVListRepository, RenewalRequestRepository, UserRepository
from utils.security import escape_html


class IPTVService:
    """Servizio gestione utenti e liste IPTV."""

    @staticmethod
    async def register_user(
        telegram_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
    ) -> bool:
        return await UserRepository.create_or_update(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

    @staticmethod
    async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
        return await UserRepository.get_by_id(telegram_id)

    @staticmethod
    async def is_user_registered(telegram_id: int) -> bool:
        user = await UserRepository.get_by_id(telegram_id)
        return user is not None and user.get("is_registered", False)

    @staticmethod
    async def create_iptv_list(
        user_id: int,
        list_name: str,
        list_id: Optional[str] = None,
        m3u_url: Optional[str] = None,
        xmltv_url: Optional[str] = None,
        expiry_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[int]:
        await UserRepository.set_registered(user_id, True)

        return await IPTVListRepository.create(
            user_id=user_id,
            list_name=list_name,
            list_id=list_id,
            m3u_url=m3u_url,
            xmltv_url=xmltv_url,
            expiry_date=expiry_date,
            notes=notes,
        )

    @staticmethod
    async def update_iptv_list(
        list_id: int,
        list_name: Optional[str] = None,
        list_id_value: Optional[str] = None,
        m3u_url: Optional[str] = None,
        xmltv_url: Optional[str] = None,
        expiry_date: Optional[str] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        return await IPTVListRepository.update(
            list_id=list_id,
            list_name=list_name,
            list_id_value=list_id_value,
            m3u_url=m3u_url,
            xmltv_url=xmltv_url,
            expiry_date=expiry_date,
            status=status,
            notes=notes,
        )

    @staticmethod
    async def get_user_lists(user_id: int) -> List[Dict[str, Any]]:
        return await IPTVListRepository.get_by_user_id(user_id)

    @staticmethod
    async def get_active_list(user_id: int) -> Optional[Dict[str, Any]]:
        return await IPTVListRepository.get_active_by_user_id(user_id)

    @staticmethod
    async def delete_iptv_list(list_id: int) -> bool:
        return await IPTVListRepository.delete(list_id)

    @staticmethod
    async def format_list_info(user_id: int) -> str:
        """Formatta informazioni lista IPTV in modo sicuro per HTML."""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return "Utente non trovato."

        if not user.get("is_registered", False):
            return "Non hai ancora registrato una lista IPTV.\n\nUsa /registra per iniziare."

        iptv_list = await IPTVListRepository.get_active_by_user_id(user_id)
        if not iptv_list:
            return "Nessuna lista IPTV attiva trovata."

        list_name = escape_html(iptv_list.get("list_name") or "N/A")
        text = "<b>Info Lista IPTV</b>\n\n"
        text += f"Nome: <b>{list_name}</b>\n"

        if iptv_list.get("list_id"):
            text += f"ID Lista: <code>{escape_html(iptv_list['list_id'])}</code>\n"

        expiry_raw = iptv_list.get("expiry_date")
        if expiry_raw:
            text += f"Scadenza: <b>{escape_html(expiry_raw)}</b>\n"

            try:
                expiry_date = datetime.strptime(expiry_raw, "%Y-%m-%d").date()
                today = date.today()
                days_left = (expiry_date - today).days

                if days_left < 0:
                    text += "Stato: <b>SCADUTA</b>\n"
                elif days_left == 0:
                    text += "Stato: <b>Scade oggi</b>\n"
                elif days_left <= 7:
                    text += f"Stato: <b>Scade tra {days_left} giorni</b>\n"
                else:
                    text += "Stato: <b>Attiva</b>\n"
            except ValueError:
                text += "Stato: <b>Data non valida</b>\n"
        else:
            text += "Scadenza: <b>Non specificata</b>\n"

        status = iptv_list.get("status", "active")
        if status == "active":
            text += "Stato tecnico: <b>Attiva</b>\n"
        elif status == "expired":
            text += "Stato tecnico: <b>Scaduta</b>\n"
        elif status == "suspended":
            text += "Stato tecnico: <b>Sospesa</b>\n"

        if iptv_list.get("notes"):
            text += f"\nNote: {escape_html(iptv_list['notes'])}\n"

        return text


class RenewalService:
    """Servizio gestione richieste rinnovo."""

    @staticmethod
    async def create_renewal_request(user_id: int, list_id: Optional[int] = None) -> Optional[int]:
        return await RenewalRequestRepository.create(user_id, list_id)

    @staticmethod
    async def get_renewal_request(request_id: int) -> Optional[Dict[str, Any]]:
        return await RenewalRequestRepository.get_by_id(request_id)

    @staticmethod
    async def get_pending_requests() -> List[Dict[str, Any]]:
        return await RenewalRequestRepository.get_pending()

    @staticmethod
    async def get_user_renewal_requests(user_id: int) -> List[Dict[str, Any]]:
        return await RenewalRequestRepository.get_by_user_id(user_id)

    @staticmethod
    async def approve_renewal(
        request_id: int,
        admin_id: int,
        new_expiry_date: Optional[str] = None,
        admin_notes: Optional[str] = None,
    ) -> bool:
        return await RenewalRequestRepository.approve(
            request_id, admin_id, new_expiry_date, admin_notes
        )

    @staticmethod
    async def reject_renewal(request_id: int, admin_id: int, admin_notes: str) -> bool:
        return await RenewalRequestRepository.reject(request_id, admin_id, admin_notes)

    @staticmethod
    async def count_pending() -> int:
        return await RenewalRequestRepository.count_pending()

    @staticmethod
    async def format_renewal_request(request: Dict[str, Any]) -> str:
        text = "<b>Richiesta Rinnovo</b>\n\n"
        text += f"Utente: <b>{escape_html(request.get('first_name', 'N/A'))}</b>"

        username = request.get("username")
        if username:
            text += f" (@{escape_html(username)})"

        text += f"\nID: <code>{request.get('telegram_id')}</code>\n"

        list_name = request.get("list_name")
        if list_name:
            text += f"Lista: <b>{escape_html(list_name)}</b>\n"

        expiry = request.get("expiry_date")
        if expiry:
            text += f"Scadenza attuale: <b>{escape_html(expiry)}</b>\n"

        text += f"Data richiesta: <b>{escape_html(request.get('request_date', 'N/A'))}</b>\n"

        status = request.get("status", "pending")
        if status == "pending":
            text += "Stato: <b>In attesa</b>"
        elif status == "approved":
            text += "Stato: <b>Approvata</b>"
        elif status == "rejected":
            text += "Stato: <b>Rifiutata</b>"

        return text

    @staticmethod
    async def has_pending_request(user_id: int) -> bool:
        requests = await RenewalRequestRepository.get_by_user_id(user_id)
        return any(r["status"] == "pending" for r in requests)
