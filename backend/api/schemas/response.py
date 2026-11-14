"""Pydantic schemas for standardized API responses and system health."""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


def utc_now_iso() -> str:
    """Return ISO format string of current UTC time."""
    return datetime.now(timezone.utc).isoformat()


class APIResponse(BaseModel, Generic[DataT]):
    """Standardized API response wrapper."""
    success: bool = True
    data: Optional[DataT] = None
    message: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=utc_now_iso)


class HealthResponse(BaseModel):
    """System health status response."""
    status: str = Field("healthy", description="Overall health state ('healthy', 'degraded', 'unhealthy').")
    backend: str = "operational"
    database: str = Field(..., description="PostgreSQL connection state ('connected', 'disconnected', 'unconfigured').")
    redis: str = Field(..., description="Redis connection state ('connected', 'disconnected', 'unconfigured').")
    model: str = Field("gemini-2.5-flash", description="Configured Gemini LLM model name.")
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=utc_now_iso)
