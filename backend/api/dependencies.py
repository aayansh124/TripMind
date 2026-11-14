
"""Reusable dependency providers for FastAPI routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.clients.database import get_db
from backend.clients.redis_client import RedisClient, get_redis
from backend.services.travel_service import TravelService


def get_database_session(
    db: Session = Depends(get_db),
) -> Session:
    """Provide a PostgreSQL database session."""
    return db


def get_cache_client(
    cache: RedisClient = Depends(get_redis),
) -> RedisClient:
    """Provide the Redis cache client."""
    return cache


def get_travel_service(
    db: Session = Depends(get_db),
) -> TravelService:
    """Provide a TravelService with a PostgreSQL session."""
    return TravelService(db=db)


DatabaseSession = Annotated[Session, Depends(get_database_session)]
CacheClient = Annotated[RedisClient, Depends(get_cache_client)]
TravelServiceDependency = Annotated[
    TravelService,
    Depends(get_travel_service),
]
