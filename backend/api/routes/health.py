
"""Provide application health-check endpoints."""

from fastapi import APIRouter

from backend.api.schemas.response import HealthResponse
from backend.clients.database import check_db_health
from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings


router = APIRouter(tags=["Health"])

settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Check the health of backend services."""

    database_status = check_db_health()
    redis_status = redis_client.is_healthy()

    overall_status = (
        "healthy"
        if database_status == "connected"
        else "degraded"
    )

    return HealthResponse(
        status=overall_status,
        backend="operational",
        database=database_status,
        redis=redis_status,
        model=settings.GEMINI_MODEL,
        version="1.0.0",
    )
