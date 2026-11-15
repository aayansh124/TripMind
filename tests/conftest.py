
"""Pytest configuration and shared test fixtures."""

import os

# Configure test environment before importing application modules.
os.environ["TESTING"] = "1"
os.environ["GEMINI_API_KEY"] = "mock_test_gemini_key"
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"
os.environ["TAVILY_API_KEY"] = "mock_test_tavily_key"
os.environ["AVIATIONSTACK_API_KEY"] = "mock_test_aviation_key"
os.environ["OPENWEATHER_API_KEY"] = "mock_test_weather_key"

# Use a valid PostgreSQL URL because the application rejects SQLite.
# Unit tests will mock database-dependent operations.
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://test_user:test_password@localhost:5432/travel_planner_test"
)

os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["LOG_LEVEL"] = "ERROR"

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_external_network_checks():
    """Prevent real database and Redis health checks during tests."""

    with (
        patch(
            "backend.clients.database.check_db_health",
            return_value="connected",
        ),
        patch(
            "backend.api.routes.health.check_db_health",
            return_value="connected",
        ),
        patch(
            "backend.clients.redis_client.redis_client.is_healthy",
            return_value="connected",
        ),
    ):
        yield
