"""
Tastiere per il pannello admin.
"""

from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Restituisce la tastiera principale admin."""
    keyboard = [
        [
            InlineKeyboardButton("Statistiche", callback_data="admin_stats"),
            InlineKeyboardButton("Utenti", callback_data="admin_users_0"),
        ],
        [
            InlineKeyboardButton("Rinnovi", callback_data="admin_renewals"),
        ],
        [
            InlineKeyboardButton("Esci", callback_data="admin_exit"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_users_keyboard(page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """Tastiera navigazione utenti."""
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton("Prev", callback_data=f"admin_users_{page - 1}"))

    nav_row.append(InlineKeyboardButton(f"Pagina {page + 1}", callback_data="admin_noop"))

    if has_next:
        nav_row.append(InlineKeyboardButton("Next", callback_data=f"admin_users_{page + 1}"))

    keyboard = [
        nav_row,
        [InlineKeyboardButton("Torna al pannello", callback_data="admin_panel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_renewals_keyboard() -> InlineKeyboardMarkup:
    """Tastiera filtri rinnovi."""
    keyboard = [
        [
            InlineKeyboardButton("Pendenti", callback_data="admin_renewals_list_pending_0"),
            InlineKeyboardButton("Approvati", callback_data="admin_renewals_list_approved_0"),
            InlineKeyboardButton("Rifiutati", callback_data="admin_renewals_list_rejected_0"),
        ],
        [InlineKeyboardButton("Torna al pannello", callback_data="admin_panel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_renewals_list_keyboard(
    status: str,
    page: int,
    has_prev: bool,
    has_next: bool,
    request_ids: List[int],
) -> InlineKeyboardMarkup:
    """Tastiera lista rinnovi filtrata per stato."""
    keyboard = [
        [
            InlineKeyboardButton("Pendenti", callback_data="admin_renewals_list_pending_0"),
            InlineKeyboardButton("Approvati", callback_data="admin_renewals_list_approved_0"),
            InlineKeyboardButton("Rifiutati", callback_data="admin_renewals_list_rejected_0"),
        ]
    ]

    if status == "pending":
        for request_id in request_ids:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"Gestisci richiesta #{request_id}",
                        callback_data=f"admin_renewal_view_{request_id}_{status}_{page}",
                    )
                ]
            )

    nav_row = []
    if has_prev:
        nav_row.append(
            InlineKeyboardButton(
                "Prev", callback_data=f"admin_renewals_list_{status}_{page - 1}"
            )
        )

    nav_row.append(InlineKeyboardButton(f"Pagina {page + 1}", callback_data="admin_noop"))

    if has_next:
        nav_row.append(
            InlineKeyboardButton(
                "Next", callback_data=f"admin_renewals_list_{status}_{page + 1}"
            )
        )

    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("Torna al pannello", callback_data="admin_panel")])

    return InlineKeyboardMarkup(keyboard)


def get_renewal_action_keyboard(
    request_id: int,
    return_status: str,
    return_page: int,
    allow_actions: bool = True,
) -> InlineKeyboardMarkup:
    """Tastiera azioni sulla singola richiesta."""
    keyboard = []

    if allow_actions:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Approva",
                    callback_data=f"admin_approve_{request_id}_{return_status}_{return_page}",
                ),
                InlineKeyboardButton(
                    "Rifiuta",
                    callback_data=f"admin_reject_{request_id}_{return_status}_{return_page}",
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Torna ai rinnovi",
                callback_data=f"admin_renewals_list_{return_status}_{return_page}",
            )
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def get_admin_action_cancel_keyboard(return_status: str, return_page: int) -> InlineKeyboardMarkup:
    """Tastiera annullamento operazione admin in corso."""
    keyboard = [
        [
            InlineKeyboardButton(
                "Annulla", callback_data=f"admin_action_cancel_{return_status}_{return_page}"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_renewals_keyboard(status: str, page: int) -> InlineKeyboardMarkup:
    """Tastiera di ritorno alla lista rinnovi filtrata."""
    keyboard = [
        [
            InlineKeyboardButton(
                "Torna ai rinnovi",
                callback_data=f"admin_renewals_list_{status}_{page}",
            )
        ],
        [InlineKeyboardButton("Torna al pannello", callback_data="admin_panel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per tornare al pannello admin."""
    keyboard = [[InlineKeyboardButton("Torna al pannello", callback_data="admin_panel")]]
    return InlineKeyboardMarkup(keyboard)
