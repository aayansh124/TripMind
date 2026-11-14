
"""Manage PostgreSQL connections and SQLAlchemy sessions."""

import time
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.config.settings import get_settings
from backend.utils.logger import logger


settings = get_settings()

if not settings.DATABASE_URL.startswith(
    ("postgresql://", "postgresql+psycopg://")
):
    raise ValueError(
        "DATABASE_URL must use PostgreSQL with the psycopg driver."
    )

Base = declarative_base()

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_TIMEOUT,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

_db_status_cache: dict[str, Any] = {
    "status": None,
    "last_checked": 0.0,
}


def check_db_health(force: bool = False) -> str:
    """Check PostgreSQL connectivity with a short-lived status cache."""

    now = time.monotonic()

    if (
        not force
        and _db_status_cache["status"] is not None
        and now - _db_status_cache["last_checked"] < 15.0
    ):
        return _db_status_cache["status"]

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        status = "connected"

    except Exception:
        logger.exception("PostgreSQL health check failed.")
        status = "disconnected"

    _db_status_cache["status"] = status
    _db_status_cache["last_checked"] = now

    return status


def get_db() -> Generator[Session, None, None]:
    """Provide a PostgreSQL session to a FastAPI request."""

    if check_db_health() != "connected":
        raise RuntimeError("PostgreSQL is unavailable.")

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
