
"""Main entry point for the Travel Planner FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import chat, health, travel
from backend.clients.database import check_db_health, engine
from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.graph.workflow import (
    close_workflows,
    initialize_workflows,
)
from backend.utils.exceptions import TravelPlannerException
from backend.utils.logger import logger


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown resources."""

    logger.info("Starting Travel Planner backend.")
    logger.info("Configured Gemini model: %s", settings.GEMINI_MODEL)

    try:
        database_status = check_db_health(force=True)

        if database_status != "connected":
            raise RuntimeError(
                "PostgreSQL is unavailable. Backend startup cannot continue."
            )

        logger.info("PostgreSQL connection established.")

        initialize_workflows()

        redis_status = redis_client.is_healthy()
        logger.info("Redis status: %s", redis_status)

        yield

    finally:
        logger.info("Shutting down Travel Planner backend.")

        close_workflows()
        redis_client.close()
        engine.dispose()

        logger.info("Application resources released.")


app = FastAPI(
    title="AI-Powered Multi-Agent Travel Planner",
    description=(
        "Multi-agent travel planning using Gemini, LangGraph, "
        "Tavily, AviationStack, and OpenWeather."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TravelPlannerException)
async def travel_planner_exception_handler(
    request: Request,
    exc: TravelPlannerException,
) -> JSONResponse:
    """Handle application-specific exceptions."""

    logger.warning(
        "Application exception at %s: %s",
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": exc.message,
            "details": exc.details,
        },
    )


app.include_router(health.router)
app.include_router(travel.router)
app.include_router(chat.router)


@app.get("/", tags=["Root"])
def root_status() -> dict:
    """Return basic backend information."""

    return {
        "app": "AI-Powered Multi-Agent Travel Planner API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
    }
