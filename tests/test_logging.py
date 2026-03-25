"""Tests for logging configuration"""

import logging

import pytest
import structlog

from src.core.logging import get_logger, setup_logging


class TestLogging:
    """Test logging configuration"""

    def test_setup_logging(self):
        """Test logging setup"""
        setup_logging(log_level="DEBUG", service_name="test-service")
        logger = get_logger(__name__)
        assert logger is not None

    def test_get_logger(self):
        """Test logger retrieval"""
        setup_logging()
        logger = get_logger("test_module")
        # Logger should be a structlog logger (BoundLogger or BoundLoggerLazyProxy)
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')

    def test_logger_levels(self):
        """Test different log levels"""
        setup_logging(log_level="INFO")
        logger = get_logger(__name__)
        
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_logger_with_context(self):
        """Test logging with context"""
        setup_logging()
        logger = get_logger(__name__)
        
        # Log with additional context
        logger.info("Test message", user_id="123", action="test")
