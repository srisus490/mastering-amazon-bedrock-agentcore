"""Pytest configuration and shared fixtures"""

import os
from typing import Generator

import pytest

# Configure Hypothesis for property-based testing (only if available)
try:
    from hypothesis import settings
    
    settings.register_profile("default", max_examples=100, deadline=None)
    settings.register_profile("ci", max_examples=1000, deadline=None)
    settings.register_profile("dev", max_examples=10, deadline=None)
    
    # Load profile from environment or use default
    profile = os.getenv("HYPOTHESIS_PROFILE", "default")
    settings.load_profile(profile)
except ImportError:
    pass  # Hypothesis not available, skip configuration


@pytest.fixture(scope="session")
def test_settings():
    """Provide test configuration settings"""
    from src.core.config import Settings
    
    # Override with test values
    os.environ["POSTGRES_DATABASE"] = "file_monitoring_test"
    os.environ["INFLUXDB_BUCKET"] = "file_arrivals_test"
    os.environ["REDIS_DB"] = "1"
    os.environ["ENVIRONMENT"] = "test"
    
    return Settings()


@pytest.fixture
def logger():
    """Provide a test logger"""
    from src.core.logging import get_logger
    
    return get_logger("test")


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings singleton between tests"""
    from src.core import config
    
    config._settings = None
    yield
    config._settings = None
