"""
Handler comandi utente.
"""

from __future__ import annotations

from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
from keyboards.faq_keyboards import get_faq_categories_keyboard
from keyboards.main_menu import (
    get_main_menu_keyboard,
    get_registration_keyboard,
    get_renewal_confirm_keyboard,
    get_start_keyboard,
)
from services.faq_service import FAQService
from services.iptv_service import IPTVService, RenewalService
from utils.security import escape_html, validate_list_id, validate_list_name
from utils.telegram_helpers import reject_if_rate_limited


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /start."""
    if await reject_if_rate_limited(update, "command:start", cooldown_seconds=1.0):
        return

    user = update.effective_user

    await IPTVService.register_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    welcome_text = (
        f"Ciao <b>{escape_html(user.first_name)}</b>!\n\n"
        f"Benvenuto nel <b>{escape_html(config.bot_name)}</b>.\n\n"
        "Posso aiutarti a:\n"
        "- Registrare la lista IPTV\n"
        "- Visualizzare stato e scadenza\n"
        "- Inviare richieste di rinnovo\n"
        "- Consultare FAQ e troubleshooting"
    )

    keyboard = get_start_keyboard()

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /help e /aiuto."""
    if await reject_if_rate_limited(update, "command:help", cooldown_seconds=1.0):
        return

    user = update.effective_user
    is_registered = await IPTVService.is_user_registered(user.id)

    help_text = (
        "<b>Guida ai comandi</b>\n\n"
        "/start - Benvenuto\n"
        "/help - Questa guida\n"
        "/registra - Registra la lista IPTV\n"
        "/info - Visualizza info linea\n"
        "/rinnova - Richiedi rinnovo\n"
        "/faq - FAQ e troubleshooting\n"
        "/annulla - Annulla operazione"
    )

    if is_registered:
        help_text += "\n\nStato registrazione: completata"
    else:
        help_text += "\n\nStato registrazione: non completata"

    keyboard = get_main_menu_keyboard(is_registered)

    if update.message:
        await update.message.reply_text(help_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            help_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )


async def registra_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /registra."""
    if await reject_if_rate_limited(update, "command:registra", cooldown_seconds=1.5):
        return ConversationHandler.END

    user = update.effective_user

    await IPTVService.register_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    text = (
        "<b>Registrazione Lista IPTV</b>\n\n"
        "Inserisci il <b>nome</b> della tua lista IPTV."
    )
    keyboard = get_registration_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    return RegistrationStates.ASK_NAME


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /info."""
    if await reject_if_rate_limited(update, "command:info", cooldown_seconds=1.0):
        return

    user = update.effective_user

    if not await IPTVService.is_user_registered(user.id):
        text = "Non hai ancora registrato una lista IPTV. Usa /registra per iniziare."
        keyboard = get_main_menu_keyboard(is_registered=False)

        if update.message:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return

    text = await IPTVService.format_list_info(user.id)
    keyboard = get_main_menu_keyboard(is_registered=True)

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def rinnova_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /rinnova."""
    if await reject_if_rate_limited(update, "command:rinnova", cooldown_seconds=1.5):
        return

    user = update.effective_user

    if not await IPTVService.is_user_registered(user.id):
        text = (
            "Non hai ancora registrato una lista IPTV.\n\n"
            "Usa /registra prima di richiedere un rinnovo."
        )
        keyboard = get_main_menu_keyboard(is_registered=False)

        if update.message:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return

    if await RenewalService.has_pending_request(user.id):
        text = "Hai gia una richiesta di rinnovo in corso. Attendi la lavorazione dell'admin."
        keyboard = get_main_menu_keyboard(is_registered=True)

        if update.message:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return

    text = await IPTVService.format_list_info(user.id)
    text += "\n\n<b>Richiesta Rinnovo</b>\nConfermi di voler inviare la richiesta?"

    keyboard = get_renewal_confirm_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /faq."""
    if await reject_if_rate_limited(update, "command:faq", cooldown_seconds=1.0):
        return

    text = await FAQService.format_faq_categories()
    keyboard = await get_faq_categories_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def annulla_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce /annulla."""
    user = update.effective_user
    is_registered = await IPTVService.is_user_registered(user.id)

    if context.user_data:
        context.user_data.clear()

    text = "Operazione annullata."
    keyboard = get_main_menu_keyboard(is_registered)

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il nome lista in registrazione."""
    if await reject_if_rate_limited(update, "conv:reg_name", cooldown_seconds=1.0):
        return RegistrationStates.ASK_NAME

    is_valid, list_name, error = validate_list_name(update.message.text)
    if not is_valid:
        await update.message.reply_text(error, parse_mode=ParseMode.HTML)
        return RegistrationStates.ASK_NAME

    context.user_data["registration_list_name"] = list_name

    text = (
        f"Nome lista: <b>{escape_html(list_name)}</b>\n\n"
        "Ora inserisci l'<b>ID lista</b> (opzionale).\n"
        "Se non lo hai, invia un messaggio vuoto o '-'"
    )
    keyboard = get_registration_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    return RegistrationStates.ASK_LIST_ID


async def registration_list_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce l'ID lista in registrazione."""
    if await reject_if_rate_limited(update, "conv:reg_listid", cooldown_seconds=1.0):
        return RegistrationStates.ASK_LIST_ID

    raw_value = (update.message.text or "").strip()
    if raw_value == "-":
        raw_value = ""

    is_valid, list_id, error = validate_list_id(raw_value)
    if not is_valid:
        await update.message.reply_text(error, parse_mode=ParseMode.HTML)
        return RegistrationStates.ASK_LIST_ID

    context.user_data["registration_list_id"] = list_id

    text = (
        "Inserisci la <b>data di scadenza</b> della lista.\n"
        "Formato: <b>GG/MM/AAAA</b> (esempio: 31/12/2026).\n"
        "Se non la conosci, invia '-'"
    )
    keyboard = get_registration_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    return RegistrationStates.ASK_EXPIRY


async def registration_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce la data di scadenza in registrazione."""
    if await reject_if_rate_limited(update, "conv:reg_expiry", cooldown_seconds=1.0):
        return RegistrationStates.ASK_EXPIRY
    expiry_text = (update.message.text or "").strip()

    if expiry_text == "-":
        expiry_text = ""

    expiry_date = None
    if expiry_text:
        try:
            dt = datetime.strptime(expiry_text, "%d/%m/%Y")
            expiry_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(
                "Formato data non valido. Usa GG/MM/AAAA oppure '-'",
                parse_mode=ParseMode.HTML,
            )
            return RegistrationStates.ASK_EXPIRY

    context.user_data["registration_expiry"] = expiry_date

    list_name = context.user_data["registration_list_name"]
    list_id = context.user_data.get("registration_list_id")

    text = (
        "<b>Riepilogo Registrazione</b>\n\n"
        f"Nome: <b>{escape_html(list_name)}</b>\n"
    )

    if list_id:
        text += f"ID Lista: <b>{escape_html(list_id)}</b>\n"

    if expiry_date:
        text += f"Scadenza: <b>{escape_html(expiry_date)}</b>\n"
    else:
        text += "Scadenza: <b>Non specificata</b>\n"

    text += "\nConfermi i dati?"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Conferma", callback_data="registra_conferma"),
                InlineKeyboardButton("Annulla", callback_data="registra_annulla"),
            ]
        ]
    )

    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    return RegistrationStates.ASK_CONFIRM


async def registration_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conferma registrazione lista IPTV."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    list_name = context.user_data.get("registration_list_name")
    list_id = context.user_data.get("registration_list_id")
    expiry_date = context.user_data.get("registration_expiry")

    if not list_name:
        await query.edit_message_text(
            "Errore: dati registrazione non trovati. Riprova con /registra",
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    await IPTVService.create_iptv_list(
        user_id=user.id,
        list_name=list_name,
        list_id=list_id,
        expiry_date=expiry_date,
    )

    context.user_data.clear()

    text = (
        "<b>Registrazione completata</b>\n\n"
        f"Nome: <b>{escape_html(list_name)}</b>\n"
    )

    if list_id:
        text += f"ID: <b>{escape_html(list_id)}</b>\n"

    if expiry_date:
        text += f"Scadenza: <b>{escape_html(expiry_date)}</b>\n"

    text += "\nUsa /info per visualizzare i dettagli della tua lista."

    keyboard = get_main_menu_keyboard(is_registered=True)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    return ConversationHandler.END


async def registration_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annulla registrazione in corso."""
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    text = "Registrazione annullata."
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    return ConversationHandler.END


async def registration_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce input non valido durante registrazione."""
    if await reject_if_rate_limited(update, "conv:reg_invalid", cooldown_seconds=1.0):
        return
    await update.message.reply_text(
        "Input non valido. Usa /annulla per annullare o /help per assistenza.",
        parse_mode=ParseMode.HTML,
    )


class RegistrationStates:
    """Stati conversazione registrazione."""

    ASK_NAME = 1
    ASK_LIST_ID = 2
    ASK_EXPIRY = 3
    ASK_CONFIRM = 4


def get_registration_handler():
    """Restituisce ConversationHandler registrazione."""
    return ConversationHandler(
        entry_points=[CommandHandler("registra", registra_command)],
        states={
            RegistrationStates.ASK_NAME: [
                CallbackQueryHandler(registration_cancel, pattern="^registra_annulla$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, registration_name),
            ],
            RegistrationStates.ASK_LIST_ID: [
                CallbackQueryHandler(registration_cancel, pattern="^registra_annulla$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, registration_list_id),
            ],
            RegistrationStates.ASK_EXPIRY: [
                CallbackQueryHandler(registration_cancel, pattern="^registra_annulla$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, registration_expiry),
            ],
            RegistrationStates.ASK_CONFIRM: [
                CallbackQueryHandler(registration_confirm, pattern="^registra_conferma$"),
                CallbackQueryHandler(registration_cancel, pattern="^registra_annulla$"),
            ],
        },
        fallbacks=[
            CommandHandler("annulla", annulla_command),
            CallbackQueryHandler(registration_cancel, pattern="^registra_annulla$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, registration_invalid_input),
        ],
        name="registration",
        persistent=False,
    )
