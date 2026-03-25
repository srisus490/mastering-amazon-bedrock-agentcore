"""Tests for configuration management"""

import os

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.core.config import (
    AppConfig,
    DatabaseConfig,
    Settings,
    get_settings,
    reload_settings,
)


class TestDatabaseConfig:
    """Test SQLite configuration"""

    def test_default_values(self):
        """Test default configuration values"""
        config = DatabaseConfig()
        assert config.path == "data/file_monitoring.db"
        assert config.pool_size == 5
        assert config.max_overflow == 10

    def test_connection_url(self):
        """Test SQLite connection URL generation"""
        config = DatabaseConfig(path="test.db")
        expected = "sqlite:///test.db"
        assert config.url == expected

    @given(path=st.text(min_size=1, max_size=50))
    def test_url_generation_property(self, path: str):
        """Property test: URL should always contain path"""
        config = DatabaseConfig(path=path)
        assert path in config.url
        assert config.url.startswith("sqlite:///")


class TestAppConfig:
    """Test application configuration"""

    def test_default_values(self):
        """Test default configuration values"""
        config = AppConfig()
        assert config.environment == "development"
        assert config.log_level == "INFO"
        assert config.api_port == 8000


class TestSettings:
    """Test main settings"""

    def test_settings_initialization(self):
        """Test settings can be initialized"""
        settings = Settings()
        assert settings.app is not None
        assert settings.database is not None

    def test_get_settings_singleton(self):
        """Test settings singleton pattern"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_reload_settings(self):
        """Test settings reload"""
        settings1 = get_settings()
        settings2 = reload_settings()
        assert settings1 is not settings2
