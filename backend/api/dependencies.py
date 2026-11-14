"""FastAPI reusable dependency injections."""

from typing import Generator, Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.clients.database import get_db
from backend.clients.redis_client import RedisClient, get_redis
from backend.services.travel_service import TravelService


def get_database_session(db: Optional[Session] = Depends(get_db)) -> Optional[Session]:
    """Dependency for providing database sessions."""
    return db


def get_cache_client(cache: RedisClient = Depends(get_redis)) -> RedisClient:
    """Dependency for providing Redis caching service."""
    return cache


def get_travel_service(db: Optional[Session] = Depends(get_db)) -> TravelService:
    """Dependency for providing TravelService."""
    return TravelService(db=db)
