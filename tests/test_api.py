"""Unit tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns basic application information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "AI-Powered Multi-Agent Travel Planner API"
    assert "version" in data


def test_health_endpoint():
    """Verify health endpoint reports operational backend and service statuses."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "operational"
    assert "database" in data
    assert "redis" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


def test_invalid_travel_dates():
    """Verify validation fails when return date is before departure date."""
    payload = {
        "origin": "New York",
        "destination": "London",
        "departure_date": "2026-06-15",
        "return_date": "2026-06-10",  # Invalid: before departure
        "travellers": 2,
        "budget": 3000,
        "currency": "USD",
        "travel_style": "Standard",
    }
    response = client.post("/api/v1/travel", json=payload)
    assert response.status_code == 400
    assert "Return date" in response.json()["detail"]


def test_get_nonexistent_trip():
    """Verify getting an invalid trip ID returns 404."""
    response = client.get("/api/v1/travel/nonexistent-trip-id-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_trips_endpoint():
    """Verify listing saved trips returns a list."""
    response = client.get("/api/v1/travel")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chat_endpoint_validation():
    """Verify chat endpoint processes conversational request."""
    from unittest.mock import AsyncMock, patch

    with patch("backend.graph.runner.run_chat_turn", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = ("Here are packing recommendations for Tokyo.", None, ["OpenWeather"])
        payload = {
            "thread_id": "test_api_thread_1",
            "message": "What should I pack?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "assistant_response" in data
        assert data["thread_id"] == "test_api_thread_1"


def test_delete_nonexistent_trip():
    """Verify deleting an invalid trip ID returns 404."""
    response = client.delete("/api/v1/travel/missing-trip-id-999")
    assert response.status_code == 404
