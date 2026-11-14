"""Unit tests for Redis cache resilience, serialization, and graceful degradation."""

import pytest
from unittest.mock import MagicMock
from backend.clients.redis_client import RedisClient


def test_cache_miss_returns_none():
    """Verify that querying a non-existent key returns None without error."""
    client = RedisClient()
    # Mock redis backend
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    client._client = mock_redis
    client._is_available = True
    client._initialized = True

    result = client.get("non_existent_key")
    assert result is None
    mock_redis.get.assert_called_once_with("non_existent_key")


def test_cache_hit_deserialization():
    """Verify that cached JSON payload is accurately deserialized."""
    client = RedisClient()
    mock_redis = MagicMock()
    mock_redis.get.return_value = '{"destination": "Rome", "temp": 24.5}'
    client._client = mock_redis
    client._is_available = True
    client._initialized = True

    result = client.get("weather:rome")
    assert result is not None
    assert result["destination"] == "Rome"
    assert result["temp"] == 24.5


def test_cache_set_with_ttl():
    """Verify that setting a cache entry serializes JSON and specifies TTL."""
    client = RedisClient()
    mock_redis = MagicMock()
    client._client = mock_redis
    client._is_available = True
    client._initialized = True

    success = client.set("hotel:paris", {"name": "Le Meurice"}, ttl_seconds=1800)
    assert success is True
    mock_redis.setex.assert_called_once()
    args, _ = mock_redis.setex.call_args
    assert args[0] == "hotel:paris"
    assert args[1] == 1800
    assert "Le Meurice" in args[2]


def test_redis_unavailable_fallback():
    """Verify that when Redis is disconnected, methods fail safely without raising exceptions."""
    client = RedisClient()
    client._client = None
    client._is_available = False
    client._initialized = True

    assert client.get("any_key") is None
    assert client.set("any_key", {"data": 123}) is False
    assert client.delete("any_key") is False
    assert client.is_healthy() == "disconnected"

