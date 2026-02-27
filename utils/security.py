"""Funzioni di validazione, sanitizzazione e masking dati sensibili."""

from __future__ import annotations

import html
import re
from typing import Optional, Tuple

LIST_NAME_MIN_LENGTH = 2
LIST_NAME_MAX_LENGTH = 80
LIST_ID_MAX_LENGTH = 64
ADMIN_NOTE_MAX_LENGTH = 500

LIST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:@-]{1,64}$")


def escape_html(value: Optional[str]) -> str:
    """Escapa testo utente per output in parse_mode HTML."""
    return html.escape((value or "").strip(), quote=False)


def normalize_text(value: Optional[str]) -> str:
    """Normalizza input testuale utente rimuovendo spazi iniziali/finali."""
    return (value or "").strip()


def validate_list_name(raw_value: Optional[str]) -> Tuple[bool, str, str]:
    """Valida il nome della lista IPTV."""
    value = normalize_text(raw_value)

    if len(value) < LIST_NAME_MIN_LENGTH:
        return False, "", "Il nome e troppo corto (minimo 2 caratteri)."

    if len(value) > LIST_NAME_MAX_LENGTH:
        return False, "", f"Il nome e troppo lungo (massimo {LIST_NAME_MAX_LENGTH} caratteri)."

    if any(ord(ch) < 32 for ch in value):
        return False, "", "Il nome contiene caratteri non validi."

    return True, value, ""


def validate_list_id(raw_value: Optional[str]) -> Tuple[bool, Optional[str], str]:
    """Valida l'ID lista IPTV (opzionale)."""
    value = normalize_text(raw_value)

    if not value:
        return True, None, ""

    if len(value) > LIST_ID_MAX_LENGTH or not LIST_ID_PATTERN.match(value):
        return (
            False,
            None,
            "ID lista non valido. Usa solo lettere, numeri e i simboli . _ : @ -",
        )

    return True, value, ""


def validate_admin_note(raw_value: Optional[str], required: bool = False) -> Tuple[bool, str, str]:
    """Valida una nota admin."""
    value = normalize_text(raw_value)

    if required and not value:
        return False, "", "La nota e obbligatoria."

    if len(value) > ADMIN_NOTE_MAX_LENGTH:
        return False, "", f"La nota e troppo lunga (massimo {ADMIN_NOTE_MAX_LENGTH} caratteri)."

    if any(ord(ch) < 32 and ch not in ("\n", "\t") for ch in value):
        return False, "", "La nota contiene caratteri non validi."

    return True, value, ""


def mask_telegram_id(telegram_id: Optional[int]) -> str:
    """Maschera un ID Telegram per logging."""
    if telegram_id is None:
        return "N/A"

    raw = str(telegram_id)
    if len(raw) <= 4:
        return "*" * len(raw)

    return f"{'*' * (len(raw) - 4)}{raw[-4:]}"

