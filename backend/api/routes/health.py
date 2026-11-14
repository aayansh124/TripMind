"""System health check endpoint."""

from fastapi import APIRouter
from backend.api.schemas.response import HealthResponse
from backend.clients.database import check_db_health
from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Check health status of backend, database, and Redis cache."""
    db_status = check_db_health()
    redis_status = redis_client.is_healthy()

    overall = "healthy"
    if db_status == "disconnected":
        overall = "degraded"

    return HealthResponse(
        status=overall,
        backend="operational",
        database=db_status,
        redis=redis_status,
        model=settings.GEMINI_MODEL,
        version="1.0.0",
    )

