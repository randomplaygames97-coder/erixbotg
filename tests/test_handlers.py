"""
Unit tests for handlers.

Tests command handlers, message handlers, and callback handlers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes
from src.handlers import CommandHandler, MessageHandler, CallbackHandler


@pytest.fixture
def mock_update() -> Update:
    """Create a mock Telegram update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.first_name = "Test"
    update.message = MagicMock(spec=Message)
    update.message.text = "Test message"
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context() -> ContextTypes.DEFAULT_TYPE:
    """Create a mock Telegram context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.mark.asyncio
async def test_handle_start(mock_update: Update, mock_context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test /start command handler."""
    await CommandHandler.handle_start(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Benvenuto" in call_args


@pytest.mark.asyncio
async def test_handle_help(mock_update: Update, mock_context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test /help command handler."""
    await CommandHandler.handle_help(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Comandi" in call_args


@pytest.mark.asyncio
async def test_handle_info(mock_update: Update, mock_context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test /info command handler."""
    await CommandHandler.handle_info(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "ErixBotG" in call_args


@pytest.mark.asyncio
async def test_handle_message(mock_update: Update, mock_context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test text message handler."""
    mock_update.message.text = "Hello bot!"
    await MessageHandler.handle_message(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_invalid(mock_update: Update, mock_context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test message handler with invalid message."""
    mock_update.message.text = ""
    await MessageHandler.handle_message(mock_update, mock_context)
    mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_handle_callback(mock_context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test callback query handler."""
    mock_update = MagicMock(spec=Update)
    mock_update.callback_query = MagicMock()
    mock_update.callback_query.data = "button_1"
    mock_update.callback_query.answer = AsyncMock()
    mock_update.callback_query.edit_message_text = AsyncMock()
    mock_update.effective_user = MagicMock(spec=User)
    mock_update.effective_user.id = 12345
    
    await CallbackHandler.handle_button_press(mock_update, mock_context)
    mock_update.callback_query.answer.assert_called_once()
    mock_update.callback_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_unknown(mock_update: Update, mock_context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test unknown command handler."""
    await CommandHandler.handle_unknown(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "non riconosciuto" in call_args
