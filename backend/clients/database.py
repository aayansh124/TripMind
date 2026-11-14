"""Database engine, session factory, and connection lifecycle."""

import os
import time
from typing import Any, Dict, Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.config.settings import get_settings
from backend.utils.logger import logger

settings = get_settings()

Base = declarative_base()

_db_status_cache: Dict[str, Any] = {"status": None, "last_checked": 0.0}

# Initialize engine conditionally; supports both PostgreSQL and local zero-setup SQLite
try:
    if os.getenv("TESTING") == "1":
        # In automated tests, use SQLite in-memory or mock
        engine = create_engine("sqlite:///:memory:", echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    elif settings.DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        from backend.database.models import TripModel, ConversationModel  # noqa
        Base.metadata.create_all(bind=engine)
        logger.info("Initialized local SQLite database: %s", settings.DATABASE_URL)
    else:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_TIMEOUT,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 1},
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning("Could not initialize database engine with %s: %s", settings.DATABASE_URL, e)
    engine = None
    SessionLocal = None


def check_db_health(force: bool = False) -> str:
    """Check database connection status with caching to avoid repeated timeout delays.

    If configured PostgreSQL is unreachable, automatically falls back to local SQLite persistence.
    """
    global engine, SessionLocal

    if os.getenv("TESTING") == "1":
        return "connected"
    if engine is None:
        return "unconfigured"

    now = time.time()
    # Cache status for 15 seconds so checks don't repeat unnecessary work on every request
    if not force and _db_status_cache["status"] is not None and (now - _db_status_cache["last_checked"]) < 15.0:
        return _db_status_cache["status"]

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _db_status_cache["status"] = "connected"
    except Exception as e:
        logger.debug("Primary database ping failed: %s", e)
        # Resilient fallback: If PostgreSQL is unreachable, switch seamlessly to local SQLite!
        try:
            logger.info("PostgreSQL is unavailable. Automatically activating local persistent SQLite database.")
            engine = create_engine(
                "sqlite:///./travel_planner.db",
                connect_args={"check_same_thread": False},
            )
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            from backend.database.models import TripModel, ConversationModel  # noqa
            Base.metadata.create_all(bind=engine)
            _db_status_cache["status"] = "connected"
        except Exception as fallback_err:
            logger.warning("Local SQLite activation failed: %s", fallback_err)
            _db_status_cache["status"] = "disconnected"

    _db_status_cache["last_checked"] = now
    return _db_status_cache["status"]


def get_db() -> Generator[Optional[Session], None, None]:
    """FastAPI dependency for obtaining a database session."""
    health = check_db_health()
    if SessionLocal is None or not health.startswith("connected"):
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
