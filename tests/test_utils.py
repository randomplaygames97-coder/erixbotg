"""
Unit tests for utilities and logger.

Tests helper functions, logger setup, and retry mechanism.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.utils.logger import LoggerManager
from src.utils.helpers import retry_on_exception, validate_user_input


class TestLoggerManager:
    """Test suite for LoggerManager."""

    def test_logger_creation(self) -> None:
        """Test logger creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger_manager = LoggerManager(log_dir=tmpdir)
            logger = logger_manager.get_logger("test")
            assert logger is not None
            assert logger.name == "test"

    def test_logger_file_creation(self) -> None:
        """Test that log file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger_manager = LoggerManager(log_dir=tmpdir)
            logger_manager.get_logger("test_app")
            log_path = Path(tmpdir)
            log_files = list(log_path.glob("*.log"))
            assert len(log_files) > 0

    def test_logger_level_configuration(self) -> None:
        """Test logger level configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger_manager = LoggerManager(log_dir=tmpdir, level="DEBUG")
            logger = logger_manager.get_logger("debug_test")
            assert logger is not None

    def test_logger_singleton(self) -> None:
        """Test that logger returns same instance for same name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger_manager = LoggerManager(log_dir=tmpdir)
            logger1 = logger_manager.get_logger("test")
            logger2 = logger_manager.get_logger("test")
            assert logger1 is logger2


class TestRetryDecorator:
    """Test suite for retry_on_exception decorator."""

    def test_retry_success_first_attempt(self) -> None:
        """Test function that succeeds on first attempt."""
        call_count = 0

        @retry_on_exception(max_attempts=3, delay=0.1)
        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self) -> None:
        """Test function that succeeds after retries."""
        call_count = 0

        @retry_on_exception(max_attempts=3, delay=0.1)
        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_max_attempts_exceeded(self) -> None:
        """Test that exception is raised after max attempts."""
        call_count = 0

        @retry_on_exception(max_attempts=2, delay=0.1)
        def test_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            test_func()
        assert call_count == 2

    def test_retry_with_arguments(self) -> None:
        """Test retry decorator with function arguments."""
        call_count = 0

        @retry_on_exception(max_attempts=2, delay=0.1)
        def add(a: int, b: int) -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Error")
            return a + b

        result = add(2, 3)
        assert result == 5
        assert call_count == 2


class TestValidateUserInput:
    """Test suite for validate_user_input function."""

    def test_validate_valid_input(self) -> None:
        """Test validation of valid input."""
        result = validate_user_input("Hello")
        assert result is True

    def test_validate_empty_input(self) -> None:
        """Test validation of empty input."""
        result = validate_user_input("")
        assert result is False

    def test_validate_whitespace_input(self) -> None:
        """Test validation of whitespace-only input."""
        result = validate_user_input("   ")
        assert result is False

    def test_validate_none_input(self) -> None:
        """Test validation of None input."""
        result = validate_user_input(None)
        assert result is False

    def test_validate_long_input(self) -> None:
        """Test validation of very long input."""
        long_text = "a" * 5000
        result = validate_user_input(long_text)
        assert result is False

    def test_validate_special_characters(self) -> None:
        """Test validation of input with special characters."""
        result = validate_user_input("Hello! @#$%")
        assert result is True

    def test_validate_min_length(self) -> None:
        """Test validation with custom min length."""
        result = validate_user_input("Hi", min_length=3)
        assert result is False

    def test_validate_max_length(self) -> None:
        """Test validation with custom max length."""
        result = validate_user_input("Hello", max_length=3)
        assert result is False


class TestIntegration:
    """Integration tests."""

    def test_logger_with_retry_decorator(self) -> None:
        """Test logger integration with retry decorator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger_manager = LoggerManager(log_dir=tmpdir)
            logger = logger_manager.get_logger("integration_test")
            
            call_count = 0

            @retry_on_exception(max_attempts=2, delay=0.1)
            def failing_func() -> None:
                nonlocal call_count
                call_count += 1
                logger.info(f"Attempt {call_count}")
                if call_count < 2:
                    raise RuntimeError("Error")

            failing_func()
            assert call_count == 2
            
            # Check log file was created
            log_path = Path(tmpdir)
            log_files = list(log_path.glob("*.log"))
            assert len(log_files) > 0
