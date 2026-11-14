
"""Pydantic schemas for standardized API responses."""

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class APIResponse(BaseModel, Generic[DataT]):
    """Standardized API response wrapper."""

    success: bool = True
    data: DataT | None = None
    message: str | None = None
    errors: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=utc_now_iso)


class HealthResponse(BaseModel):
    """Represent the application health status."""

    status: str = Field(
        "healthy",
        description="Overall application health status.",
    )
    backend: str = "operational"
    database: str = Field(
        ...,
        description="PostgreSQL connection status.",
    )
    redis: str = Field(
        ...,
        description="Redis connection status.",
    )
    model: str = Field(
        "gemini-2.5-flash",
        description="Configured Gemini model.",
    )
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=utc_now_iso)
