"""Pytest configuration and global fixtures."""

import os
os.environ["TESTING"] = "1"
os.environ["GEMINI_API_KEY"] = "mock_test_gemini_key"
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"
os.environ["TAVILY_API_KEY"] = "mock_test_tavily_key"
os.environ["AVIATIONSTACK_API_KEY"] = "mock_test_aviation_key"
os.environ["OPENWEATHER_API_KEY"] = "mock_test_weather_key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["LOG_LEVEL"] = "ERROR"

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_external_network_checks():
    """Mock database and Redis connectivity in tests to prevent connection stalls."""
    with patch("backend.clients.database.check_db_health", return_value="connected"), \
         patch("backend.clients.redis_client.redis_client.is_healthy", return_value="connected"):
        yield
