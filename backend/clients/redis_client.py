"""Redis client connection and resilient caching operations."""

import json
import os
from typing import Any, Optional
import redis
from backend.config.settings import get_settings
from backend.utils.logger import logger

settings = get_settings()


class RedisClient:
    """Resilient Redis cache manager with graceful degradation."""

    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None
        self._is_available: bool = False
        self._initialized: bool = False

    def _ensure_init(self) -> None:
        """Lazy-initialize Redis connection."""
        if self._initialized:
            return
        self._initialized = True

        if os.getenv("TESTING") == "1":
            self._is_available = False
            return

        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
            )
            self._client.ping()
            self._is_available = True
            logger.info("Successfully connected to Redis cache at %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Redis is currently unavailable. Operating in bypass/fallback mode: %s", e)
            self._is_available = False

    def is_healthy(self) -> str:
        """Check Redis connectivity."""
        self._ensure_init()
        if not self._is_available or self._client is None:
            return "disconnected"
        if os.getenv("TESTING") == "1":
            return "connected"
        try:
            self._client.ping()
            return "connected"
        except Exception:
            return "disconnected"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize a cached JSON object.

        Returns None on cache miss or when Redis is unavailable.
        """
        self._ensure_init()
        if not self._is_available or self._client is None:
            return None

        try:
            val = self._client.get(key)
            if val is not None:
                logger.debug("Cache HIT for key: %s", key)
                return json.loads(val)
            logger.debug("Cache MISS for key: %s", key)
            return None
        except Exception as e:
            logger.warning("Error reading from Redis for key '%s': %s", key, e)
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Serialize and cache a value with a specific TTL.

        Returns False if caching fails or Redis is offline.
        """
        self._ensure_init()
        if not self._is_available or self._client is None:
            return False

        try:
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl_seconds, serialized)
            logger.debug("Cached key '%s' with TTL %ds", key, ttl_seconds)
            return True
        except Exception as e:
            logger.warning("Error writing to Redis for key '%s': %s", key, e)
            return False

    def delete(self, key: str) -> bool:
        """Remove a cached key."""
        self._ensure_init()
        if not self._is_available or self._client is None:
            return False

        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning("Error deleting key '%s' from Redis: %s", key, e)
            return False


# Singleton instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Dependency provider for RedisClient."""
    return redis_client
