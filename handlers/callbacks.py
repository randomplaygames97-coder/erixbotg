"""
Handler per callback query utente.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, ContextTypes

from keyboards.admin_keyboards import get_renewal_action_keyboard
from keyboards.faq_keyboards import get_faq_categories_keyboard, get_faq_detail_keyboard
from keyboards.main_menu import (
    get_info_keyboard,
    get_main_menu_keyboard,
    get_renewal_confirm_keyboard,
)
from services.faq_service import FAQService
from services.iptv_service import IPTVService, RenewalService
from utils.security import escape_html, mask_telegram_id
from utils.telegram_helpers import reject_if_rate_limited, safe_send_message

logger = logging.getLogger(__name__)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce i callback del menu principale."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:menu", cooldown_seconds=1.0):
        return

    user = update.effective_user
    data = query.data
    is_registered = await IPTVService.is_user_registered(user.id)

    if data == "menu_main":
        text = (
            "<b>Menu Principale</b>\n\n"
            f"Ciao <b>{escape_html(user.first_name)}</b>! Scegli un'opzione:"
        )
        keyboard = get_main_menu_keyboard(is_registered)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif data == "menu_registra":
        text = (
            "<b>Registrazione Lista IPTV</b>\n\n"
            "Inserisci il <b>nome</b> della tua lista IPTV.\n"
            "Esempio: Lista Premium Giovanni o Lista Base"
        )
        from keyboards.main_menu import get_registration_keyboard

        keyboard = get_registration_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif data == "menu_info":
        text = await IPTVService.format_list_info(user.id)
        keyboard = get_info_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif data == "menu_rinnova":
        if not is_registered:
            text = (
                "Non hai ancora registrato una lista IPTV.\n\n"
                "Usa /registra per registrare la tua lista."
            )
            keyboard = get_main_menu_keyboard(is_registered=False)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            return

        if await RenewalService.has_pending_request(user.id):
            text = (
                "Hai gia una richiesta di rinnovo in corso.\n\n"
                "Attendi che l'admin processi la richiesta precedente."
            )
            keyboard = get_main_menu_keyboard(is_registered=True)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            return

        text = await IPTVService.format_list_info(user.id)
        text += "\n\n<b>Richiesta Rinnovo</b>\nConfermi di voler inviare la richiesta?"
        keyboard = get_renewal_confirm_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif data == "menu_faq":
        text = await FAQService.format_faq_categories()
        keyboard = await get_faq_categories_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif data == "menu_help":
        help_text = (
            "<b>Guida ai Comandi</b>\n\n"
            "- /start\n"
            "- /help\n"
            "- /registra\n"
            "- /info\n"
            "- /rinnova\n"
            "- /faq\n"
            "- /annulla"
        )
        keyboard = get_main_menu_keyboard(is_registered)
        await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    elif data == "info_refresh":
        text = await IPTVService.format_list_info(user.id)
        keyboard = get_info_keyboard()
        try:
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except BadRequest as exc:
            if "Message is not modified" not in str(exc):
                raise


async def faq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce i callback delle FAQ."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:faq", cooldown_seconds=1.0):
        return

    data = query.data

    if data.startswith("faq_"):
        category = data.replace("faq_", "")

        if category == "back":
            text = await FAQService.format_faq_categories()
            keyboard = await get_faq_categories_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        elif category in FAQService.CATEGORY_INFO:
            text = await FAQService.format_faq_list(category)
            keyboard = await get_faq_detail_keyboard(category)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def renewal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce i callback del flusso rinnovo."""
    query = update.callback_query
    await query.answer()

    if await reject_if_rate_limited(update, "callback:renewal", cooldown_seconds=1.5):
        return

    user = update.effective_user
    data = query.data

    if data == "renewal_cancel":
        text = "Richiesta di rinnovo annullata."
        keyboard = get_main_menu_keyboard(is_registered=True)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return

    if data != "renewal_confirm" and not data.startswith("renewal_confirm_"):
        return

    if not await IPTVService.is_user_registered(user.id):
        text = "Non hai una lista registrata. Usa /registra prima di inviare un rinnovo."
        keyboard = get_main_menu_keyboard(is_registered=False)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return

    if await RenewalService.has_pending_request(user.id):
        text = "Hai gia una richiesta pendente. Attendi la lavorazione da parte dell'admin."
        keyboard = get_main_menu_keyboard(is_registered=True)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return

    user_list = await IPTVService.get_active_list(user.id)
    list_id = user_list["id"] if user_list else None

    request_id = await RenewalService.create_renewal_request(user.id, list_id)
    if not request_id:
        await query.edit_message_text(
            "Errore durante la creazione della richiesta. Riprova tra poco.",
            reply_markup=get_main_menu_keyboard(is_registered=True),
            parse_mode=ParseMode.HTML,
        )
        return

    text = (
        "<b>Richiesta di rinnovo inviata</b>\n\n"
        "La richiesta e stata inoltrata all'admin. Riceverai una notifica quando verra processata."
    )
    keyboard = get_main_menu_keyboard(is_registered=True)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    await notify_admin_renewal(context, user.id, user_list, request_id)


async def notify_admin_renewal(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    user_list: dict | None,
    request_id: int,
):
    """Notifica agli admin una nuova richiesta rinnovo."""
    from config.settings import config
    from database.repository import UserRepository

    user = await UserRepository.get_by_id(user_id)
    if not user:
        return

    first_name = escape_html(user.get("first_name") or "N/A")
    username = escape_html(user.get("username") or "")

    text = (
        "<b>Nuova Richiesta di Rinnovo</b>\n\n"
        f"Richiesta: <b>#{request_id}</b>\n"
        f"Utente: <b>{first_name}</b>"
    )

    if username:
        text += f" (@{username})"

    text += f"\nID: <code>{user_id}</code>\n"

    if user_list:
        list_name = escape_html(user_list.get("list_name") or "N/A")
        expiry = escape_html(user_list.get("expiry_date") or "N/A")
        text += f"Lista: <b>{list_name}</b>\n"
        text += f"Scadenza attuale: <b>{expiry}</b>\n"

    keyboard = get_renewal_action_keyboard(
        request_id=request_id,
        return_status="pending",
        return_page=0,
        allow_actions=True,
    )

    for admin_id in config.admin_ids:
        sent = await safe_send_message(
            context.bot,
            admin_id,
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        if not sent:
            logger.warning(
                "Unable to notify admin admin_id=%s request_id=%s",
                mask_telegram_id(admin_id),
                request_id,
            )


def get_callback_handlers():
    """Restituisce la lista callback handler utente."""
    return [
        CallbackQueryHandler(menu_callback, pattern="^menu_"),
        CallbackQueryHandler(faq_callback, pattern="^faq_"),
        CallbackQueryHandler(renewal_callback, pattern="^renewal_"),
    ]
