
"""Manage Redis connections and resilient caching operations."""

import json
from typing import Any

import redis

from backend.config.settings import get_settings
from backend.utils.logger import logger


settings = get_settings()


class RedisClient:
    """Manage Redis caching with graceful fallback."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._is_available = False
        self._initialized = False

    def _ensure_init(self) -> None:
        """Initialize the Redis connection when required."""

        if self._initialized:
            return

        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            )
            self._initialized = True
            self._check_connection()

        except Exception:
            logger.exception("Redis client initialization failed.")
            self._is_available = False

    def _check_connection(self) -> bool:
        """Check Redis connectivity and update availability."""

        if self._client is None:
            self._is_available = False
            return False

        try:
            self._client.ping()
            self._is_available = True
            return True

        except redis.RedisError:
            self._is_available = False
            logger.warning("Redis is unavailable. Cache operations are bypassed.")
            return False

    def _get_available_client(self) -> redis.Redis | None:
        """Return a connected Redis client when available."""

        self._ensure_init()

        if not self._is_available:
            self._check_connection()

        return self._client if self._is_available else None

    def is_healthy(self) -> str:
        """Return the current Redis connection status."""

        if self._get_available_client() is not None:
            return "connected"

        return "disconnected"

    def get(self, key: str) -> Any | None:
        """Retrieve and deserialize a cached JSON value."""

        client = self._get_available_client()

        if client is None:
            return None

        try:
            value = client.get(key)

            if value is None:
                logger.debug("Cache MISS for key: %s", key)
                return None

            logger.debug("Cache HIT for key: %s", key)
            return json.loads(value)

        except (redis.RedisError, ValueError, TypeError):
            logger.exception("Redis cache read failed for key: %s", key)
            self._is_available = False
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> bool:
        """Serialize and store a value with an expiration time."""

        if ttl_seconds <= 0:
            raise ValueError("Cache TTL must be greater than zero.")

        client = self._get_available_client()

        if client is None:
            return False

        try:
            serialized = json.dumps(value, default=str)
            client.setex(key, ttl_seconds, serialized)

            logger.debug(
                "Cached key '%s' with TTL %d seconds.",
                key,
                ttl_seconds,
            )
            return True

        except (redis.RedisError, TypeError, ValueError):
            logger.exception("Redis cache write failed for key: %s", key)
            self._is_available = False
            return False

    def delete(self, key: str) -> bool:
        """Delete a cached value."""

        client = self._get_available_client()

        if client is None:
            return False

        try:
            client.delete(key)
            return True

        except redis.RedisError:
            logger.exception("Redis cache deletion failed for key: %s", key)
            self._is_available = False
            return False

    def close(self) -> None:
        """Close the Redis connection."""

        if self._client is not None:
            self._client.close()

        self._client = None
        self._is_available = False
        self._initialized = False


# Shared Redis client instance.
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Provide the shared Redis client."""
    return redis_client
