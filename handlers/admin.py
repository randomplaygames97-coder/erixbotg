"""
Handler pannello admin.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Tuple

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config.settings import config
from database.repository import RenewalRequestRepository, UserRepository
from keyboards.admin_keyboards import (
    get_admin_action_cancel_keyboard,
    get_admin_panel_keyboard,
    get_admin_renewals_list_keyboard,
    get_admin_users_keyboard,
    get_back_to_admin_keyboard,
    get_back_to_renewals_keyboard,
    get_renewal_action_keyboard,
)
from utils.security import escape_html, mask_telegram_id, validate_admin_note
from utils.telegram_helpers import reject_if_rate_limited, safe_send_message

logger = logging.getLogger(__name__)

RENEWAL_STATUSES = {
    "pending": "Pendenti",
    "approved": "Approvati",
    "rejected": "Rifiutati",
}


class AdminActionStates:
    """Stati conversation action admin."""

    WAIT_APPROVE_INPUT = 1
    WAIT_REJECT_NOTE = 2


def is_admin(update: Update) -> bool:
    """Verifica se utente corrente e admin."""
    user = update.effective_user
    return bool(user and user.id in config.admin_ids)


def _parse_users_page(data: str) -> int:
    if data == "admin_users" or data == "admin_users_":
        return 0

    try:
        page = int(data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        page = 0

    return max(0, page)


def _parse_status_page(data: str) -> Tuple[str, int]:
    parts = data.split("_")
    if len(parts) < 5:
        return "pending", 0

    status = parts[3] if parts[3] in RENEWAL_STATUSES else "pending"
    try:
        page = int(parts[4])
    except ValueError:
        page = 0

    return status, max(0, page)


def _parse_request_action(data: str) -> Tuple[Optional[int], str, int]:
    parts = data.split("_")
    if len(parts) < 5:
        return None, "pending", 0

    try:
        request_id = int(parts[2])
    except ValueError:
        return None, "pending", 0

    status = parts[3] if parts[3] in RENEWAL_STATUSES else "pending"

    try:
        page = int(parts[4])
    except ValueError:
        page = 0

    return request_id, status, max(0, page)


def _parse_view_callback(data: str) -> Tuple[Optional[int], str, int]:
    # admin_renewal_view_{id}_{status}_{page}
    parts = data.split("_")
    if len(parts) < 6:
        return None, "pending", 0

    try:
        request_id = int(parts[3])
    except ValueError:
        return None, "pending", 0

    status = parts[4] if parts[4] in RENEWAL_STATUSES else "pending"
    try:
        page = int(parts[5])
    except ValueError:
        page = 0

    return request_id, status, max(0, page)


def _parse_cancel_callback(data: str) -> Tuple[str, int]:
    # admin_action_cancel_{status}_{page}
    parts = data.split("_")
    if len(parts) < 5:
        return "pending", 0

    status = parts[3] if parts[3] in RENEWAL_STATUSES else "pending"
    try:
        page = int(parts[4])
    except ValueError:
        page = 0

    return status, max(0, page)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /admin."""
    if await reject_if_rate_limited(update, "command:admin", cooldown_seconds=1.0):
        return

    if not is_admin(update):
        await update.message.reply_text("Non hai accesso a questo comando.")
        return

    text = "<b>Pannello Admin</b>\n\nScegli un'opzione:"
    await update.message.reply_text(
        text,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra statistiche del bot."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:admin_stats", cooldown_seconds=1.0):
        return

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return

    total_users = await UserRepository.count()
    registered_users = await UserRepository.count_registered()
    pending_renewals = await RenewalRequestRepository.count_pending()
    approved_renewals = await RenewalRequestRepository.count_by_status("approved")
    rejected_renewals = await RenewalRequestRepository.count_by_status("rejected")

    text = (
        "<b>Statistiche Bot</b>\n\n"
        f"Utenti totali: <b>{total_users}</b>\n"
        f"Utenti registrati: <b>{registered_users}</b>\n"
        f"Utenti non registrati: <b>{total_users - registered_users}</b>\n\n"
        f"Rinnovi pendenti: <b>{pending_renewals}</b>\n"
        f"Rinnovi approvati: <b>{approved_renewals}</b>\n"
        f"Rinnovi rifiutati: <b>{rejected_renewals}</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=get_back_to_admin_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra utenti con paginazione reale."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:admin_users", cooldown_seconds=1.0):
        return

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return

    page = _parse_users_page(query.data)
    limit = 10
    offset = page * limit

    total_users = await UserRepository.count()
    users = await UserRepository.get_all(limit=limit, offset=offset)

    if not users and page > 0:
        page = max(0, (total_users - 1) // limit)
        offset = page * limit
        users = await UserRepository.get_all(limit=limit, offset=offset)

    if not users:
        await query.edit_message_text(
            "Nessun utente trovato.",
            reply_markup=get_back_to_admin_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    text = f"<b>Utenti</b> - Pagina <b>{page + 1}</b>\n\n"

    for user in users:
        status = "SI" if user["is_registered"] else "NO"
        first_name = escape_html(user.get("first_name") or "N/A")
        username = escape_html(user.get("username") or "N/A")
        created_at = (user.get("created_at") or "N/A")[:10]

        text += (
            f"Nome: <b>{first_name}</b>\n"
            f"Username: @{username}\n"
            f"ID: <code>{user['telegram_id']}</code>\n"
            f"Registrato: <b>{status}</b>\n"
            f"Creato il: <b>{created_at}</b>\n\n"
        )

    has_prev = page > 0
    has_next = offset + len(users) < total_users

    await query.edit_message_text(
        text,
        reply_markup=get_admin_users_keyboard(page, has_prev, has_next),
        parse_mode=ParseMode.HTML,
    )


async def admin_renewals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Apri sezione rinnovi con filtro iniziale pendenti."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:admin_renewals", cooldown_seconds=1.0):
        return

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return

    await _render_renewals_page(query, status="pending", page=0)


async def admin_renewals_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra rinnovi filtrati con paginazione reale."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:admin_renewals_list", cooldown_seconds=1.0):
        return

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return

    status, page = _parse_status_page(query.data)
    await _render_renewals_page(query, status=status, page=page)


async def _render_renewals_page(query, status: str, page: int):
    limit = 5
    offset = page * limit

    total = await RenewalRequestRepository.count_by_status(status)
    requests = await RenewalRequestRepository.get_by_status(status, limit=limit, offset=offset)

    if not requests and page > 0:
        page = max(0, (total - 1) // limit)
        offset = page * limit
        requests = await RenewalRequestRepository.get_by_status(status, limit=limit, offset=offset)

    title = RENEWAL_STATUSES.get(status, "Rinnovi")
    text = f"<b>Rinnovi {title}</b> - Pagina <b>{page + 1}</b>\n\n"

    if not requests:
        text += "Nessuna richiesta in questo stato."
    else:
        for req in requests:
            first_name = escape_html(req.get("first_name") or "N/A")
            username = escape_html(req.get("username") or "")
            list_name = escape_html(req.get("list_name") or "N/A")
            expiry = escape_html(req.get("expiry_date") or "N/A")
            request_date = escape_html((req.get("request_date") or "N/A")[:10])

            text += (
                f"Richiesta <b>#{req['id']}</b>\n"
                f"Utente: <b>{first_name}</b>"
            )

            if username:
                text += f" (@{username})"

            text += (
                f"\nID: <code>{req['user_id']}</code>\n"
                f"Lista: <b>{list_name}</b>\n"
                f"Scadenza: <b>{expiry}</b>\n"
                f"Data richiesta: <b>{request_date}</b>\n"
            )

            if req.get("admin_notes"):
                text += f"Note admin: <i>{escape_html(req['admin_notes'])}</i>\n"

            text += "\n"

    has_prev = page > 0
    has_next = offset + len(requests) < total
    request_ids = [req["id"] for req in requests] if status == "pending" else []

    keyboard = get_admin_renewals_list_keyboard(
        status=status,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
        request_ids=request_ids,
    )

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def admin_renewal_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra dettaglio singola richiesta rinnovo."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:admin_renewal_view", cooldown_seconds=1.0):
        return

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return

    request_id, status, page = _parse_view_callback(query.data)
    if not request_id:
        await query.edit_message_text("ID richiesta non valido.")
        return

    request_data = await RenewalRequestRepository.get_by_id(request_id)
    if not request_data:
        await query.edit_message_text(
            "Richiesta non trovata.",
            reply_markup=get_back_to_renewals_keyboard(status, page),
            parse_mode=ParseMode.HTML,
        )
        return

    allow_actions = request_data.get("status") == "pending"

    first_name = escape_html(request_data.get("first_name") or "N/A")
    username = escape_html(request_data.get("username") or "")
    list_name = escape_html(request_data.get("list_name") or "N/A")
    expiry = escape_html(request_data.get("expiry_date") or "N/A")
    request_date = escape_html(str(request_data.get("request_date") or "N/A"))
    req_status = escape_html(request_data.get("status") or "N/A")

    text = (
        f"<b>Dettaglio richiesta #{request_id}</b>\n\n"
        f"Utente: <b>{first_name}</b>"
    )

    if username:
        text += f" (@{username})"

    text += (
        f"\nID: <code>{request_data.get('user_id')}</code>\n"
        f"Lista: <b>{list_name}</b>\n"
        f"Scadenza attuale: <b>{expiry}</b>\n"
        f"Data richiesta: <b>{request_date}</b>\n"
        f"Stato: <b>{req_status}</b>\n"
    )

    if request_data.get("admin_notes"):
        text += f"Note admin: <i>{escape_html(request_data['admin_notes'])}</i>\n"

    keyboard = get_renewal_action_keyboard(
        request_id=request_id,
        return_status=status,
        return_page=page,
        allow_actions=allow_actions,
    )

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def admin_approve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Avvia workflow approvazione con input data+nota."""
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return ConversationHandler.END

    request_id, return_status, return_page = _parse_request_action(query.data)
    if not request_id:
        await query.edit_message_text("ID richiesta non valido.")
        return ConversationHandler.END

    request_data = await RenewalRequestRepository.get_by_id(request_id)
    if not request_data or request_data.get("status") != "pending":
        await query.edit_message_text(
            "Questa richiesta non e piu pendente.",
            reply_markup=get_back_to_renewals_keyboard(return_status, return_page),
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    context.user_data["admin_action_context"] = {
        "action": "approve",
        "request_id": request_id,
        "return_status": return_status,
        "return_page": return_page,
    }

    text = (
        "<b>Approvazione richiesta</b>\n\n"
        "Invia un messaggio nel formato:\n"
        "<code>GG/MM/AAAA | nota opzionale</code>\n\n"
        "Per non aggiornare la scadenza usa:\n"
        "<code>skip | nota opzionale</code>"
    )

    await query.edit_message_text(
        text,
        reply_markup=get_admin_action_cancel_keyboard(return_status, return_page),
        parse_mode=ParseMode.HTML,
    )

    return AdminActionStates.WAIT_APPROVE_INPUT


async def admin_reject_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Avvia workflow rifiuto con nota obbligatoria."""
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return ConversationHandler.END

    request_id, return_status, return_page = _parse_request_action(query.data)
    if not request_id:
        await query.edit_message_text("ID richiesta non valido.")
        return ConversationHandler.END

    request_data = await RenewalRequestRepository.get_by_id(request_id)
    if not request_data or request_data.get("status") != "pending":
        await query.edit_message_text(
            "Questa richiesta non e piu pendente.",
            reply_markup=get_back_to_renewals_keyboard(return_status, return_page),
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    context.user_data["admin_action_context"] = {
        "action": "reject",
        "request_id": request_id,
        "return_status": return_status,
        "return_page": return_page,
    }

    text = (
        "<b>Rifiuto richiesta</b>\n\n"
        "Invia il motivo del rifiuto (obbligatorio)."
    )

    await query.edit_message_text(
        text,
        reply_markup=get_admin_action_cancel_keyboard(return_status, return_page),
        parse_mode=ParseMode.HTML,
    )

    return AdminActionStates.WAIT_REJECT_NOTE


async def admin_approve_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Completa approvazione usando input testuale admin."""
    action_ctx = context.user_data.get("admin_action_context", {})
    if action_ctx.get("action") != "approve":
        return ConversationHandler.END

    request_id = action_ctx["request_id"]
    return_status = action_ctx["return_status"]
    return_page = action_ctx["return_page"]

    raw_input = (update.message.text or "").strip()
    if "|" not in raw_input:
        await update.message.reply_text(
            "Formato non valido. Usa: GG/MM/AAAA | nota oppure skip | nota",
            parse_mode=ParseMode.HTML,
        )
        return AdminActionStates.WAIT_APPROVE_INPUT

    expiry_part, note_part = [chunk.strip() for chunk in raw_input.split("|", 1)]

    new_expiry_date = None
    if expiry_part.lower() not in {"skip", "-", "none", ""}:
        try:
            new_expiry_date = datetime.strptime(expiry_part, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(
                "Data non valida. Usa GG/MM/AAAA oppure skip.",
                parse_mode=ParseMode.HTML,
            )
            return AdminActionStates.WAIT_APPROVE_INPUT

    is_valid_note, admin_note, note_error = validate_admin_note(note_part, required=False)
    if not is_valid_note:
        await update.message.reply_text(note_error, parse_mode=ParseMode.HTML)
        return AdminActionStates.WAIT_APPROVE_INPUT

    if not admin_note:
        admin_note = "Approvato dall'admin"

    current_request = await RenewalRequestRepository.get_by_id(request_id)
    if not current_request or current_request.get("status") != "pending":
        context.user_data.pop("admin_action_context", None)
        await update.message.reply_text(
            "La richiesta non e piu pendente.",
            reply_markup=get_back_to_renewals_keyboard(return_status, return_page),
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    admin_id = update.effective_user.id
    await RenewalRequestRepository.approve(
        request_id,
        admin_id,
        new_expiry_date=new_expiry_date,
        admin_notes=admin_note,
    )

    request_data = await RenewalRequestRepository.get_by_id(request_id)
    await _notify_user_processed_request(
        context=context,
        request_data=request_data,
        approved=True,
        admin_note=admin_note,
        new_expiry_date=new_expiry_date,
    )

    context.user_data.pop("admin_action_context", None)

    text = f"Richiesta #{request_id} approvata con successo."
    await update.message.reply_text(
        text,
        reply_markup=get_back_to_renewals_keyboard(return_status, return_page),
        parse_mode=ParseMode.HTML,
    )

    return ConversationHandler.END


async def admin_reject_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Completa rifiuto usando nota admin."""
    action_ctx = context.user_data.get("admin_action_context", {})
    if action_ctx.get("action") != "reject":
        return ConversationHandler.END

    request_id = action_ctx["request_id"]
    return_status = action_ctx["return_status"]
    return_page = action_ctx["return_page"]

    is_valid_note, admin_note, note_error = validate_admin_note(update.message.text, required=True)
    if not is_valid_note:
        await update.message.reply_text(note_error, parse_mode=ParseMode.HTML)
        return AdminActionStates.WAIT_REJECT_NOTE

    current_request = await RenewalRequestRepository.get_by_id(request_id)
    if not current_request or current_request.get("status") != "pending":
        context.user_data.pop("admin_action_context", None)
        await update.message.reply_text(
            "La richiesta non e piu pendente.",
            reply_markup=get_back_to_renewals_keyboard(return_status, return_page),
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    admin_id = update.effective_user.id
    await RenewalRequestRepository.reject(request_id, admin_id, admin_note)

    request_data = await RenewalRequestRepository.get_by_id(request_id)
    await _notify_user_processed_request(
        context=context,
        request_data=request_data,
        approved=False,
        admin_note=admin_note,
        new_expiry_date=None,
    )

    context.user_data.pop("admin_action_context", None)

    text = f"Richiesta #{request_id} rifiutata."
    await update.message.reply_text(
        text,
        reply_markup=get_back_to_renewals_keyboard(return_status, return_page),
        parse_mode=ParseMode.HTML,
    )

    return ConversationHandler.END


async def _notify_user_processed_request(
    context: ContextTypes.DEFAULT_TYPE,
    request_data: Optional[dict],
    approved: bool,
    admin_note: str,
    new_expiry_date: Optional[str],
):
    if not request_data:
        return

    user_id = request_data.get("telegram_id")
    if not user_id:
        return

    note_text = escape_html(admin_note)

    if approved:
        text = "<b>Rinnovo approvato</b>\n\nLa tua richiesta e stata approvata."
        if new_expiry_date:
            text += f"\nNuova scadenza: <b>{escape_html(new_expiry_date)}</b>"
        if note_text:
            text += f"\nNota admin: <i>{note_text}</i>"
    else:
        text = (
            "<b>Rinnovo rifiutato</b>\n\n"
            "La tua richiesta e stata rifiutata.\n"
            f"Motivo: <i>{note_text}</i>"
        )

    sent = await safe_send_message(
        context.bot,
        user_id,
        text,
        parse_mode=ParseMode.HTML,
    )

    if not sent:
        logger.warning(
            "Unable to notify user request_id=%s user_id=%s",
            request_data.get("id"),
            mask_telegram_id(user_id),
        )


async def admin_action_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annulla operazione admin in corso (via bottone)."""
    query = update.callback_query
    await query.answer()

    context.user_data.pop("admin_action_context", None)

    status, page = _parse_cancel_callback(query.data)

    await query.edit_message_text(
        "Operazione annullata.",
        reply_markup=get_back_to_renewals_keyboard(status, page),
        parse_mode=ParseMode.HTML,
    )

    return ConversationHandler.END


async def admin_action_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annulla operazione admin in corso (via /annulla)."""
    context.user_data.pop("admin_action_context", None)

    await update.message.reply_text(
        "Operazione annullata.",
        reply_markup=get_back_to_admin_keyboard(),
        parse_mode=ParseMode.HTML,
    )

    return ConversationHandler.END


async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ritorna al pannello admin."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:admin_panel", cooldown_seconds=1.0):
        return

    if not is_admin(update):
        await query.edit_message_text("Non hai accesso a questa funzione.")
        return

    text = "<b>Pannello Admin</b>\n\nScegli un'opzione:"
    await query.edit_message_text(
        text,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def admin_noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback no-op per bottoni informativi."""
    query = update.callback_query
    await query.answer()



def get_admin_action_conversation() -> ConversationHandler:
    """ConversationHandler per workflow approva/rifiuta."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_approve_start,
                pattern=r"^admin_approve_\d+_(pending|approved|rejected)_\d+$",
            ),
            CallbackQueryHandler(
                admin_reject_start,
                pattern=r"^admin_reject_\d+_(pending|approved|rejected)_\d+$",
            ),
        ],
        states={
            AdminActionStates.WAIT_APPROVE_INPUT: [
                CallbackQueryHandler(
                    admin_action_cancel_callback,
                    pattern=r"^admin_action_cancel_(pending|approved|rejected)_\d+$",
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_approve_input),
            ],
            AdminActionStates.WAIT_REJECT_NOTE: [
                CallbackQueryHandler(
                    admin_action_cancel_callback,
                    pattern=r"^admin_action_cancel_(pending|approved|rejected)_\d+$",
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reject_input),
            ],
        },
        fallbacks=[CommandHandler("annulla", admin_action_cancel_command)],
        name="admin_action",
        persistent=False,
    )



def get_admin_handlers():
    """Restituisce tutti gli handler admin."""
    return [
        CommandHandler("admin", admin_command),
        CallbackQueryHandler(admin_stats_callback, pattern=r"^admin_stats$"),
        CallbackQueryHandler(admin_users_callback, pattern=r"^admin_users(?:_-?\d+)?$"),
        CallbackQueryHandler(admin_renewals_callback, pattern=r"^admin_renewals$"),
        CallbackQueryHandler(
            admin_renewals_list_callback,
            pattern=r"^admin_renewals_list_(pending|approved|rejected)_-?\d+$",
        ),
        CallbackQueryHandler(
            admin_renewal_view_callback,
            pattern=r"^admin_renewal_view_\d+_(pending|approved|rejected)_-?\d+$",
        ),
        CallbackQueryHandler(admin_noop_callback, pattern=r"^admin_noop$"),
        CallbackQueryHandler(admin_panel_callback, pattern=r"^admin_panel$"),
        CallbackQueryHandler(admin_panel_callback, pattern=r"^admin_exit$"),
        get_admin_action_conversation(),
    ]
