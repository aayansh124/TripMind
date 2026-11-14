"""FastAPI Application Main Entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import chat, health, travel
from backend.clients.database import check_db_health, engine
from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.utils.exceptions import TravelPlannerException
from backend.utils.logger import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: handle startup and shutdown tasks."""
    logger.info("Initializing AI Multi-Agent Travel Planner Backend...")
    logger.info("Configured Gemini model: %s", settings.GEMINI_MODEL)
    logger.info("Database status on startup: %s", check_db_health())
    logger.info("Redis status on startup: %s", redis_client.is_healthy())

    yield

    logger.info("Shutting down AI Multi-Agent Travel Planner Backend...")
    if engine is not None:
        try:
            engine.dispose()
            logger.info("Database connection pool disposed.")
        except Exception as e:
            logger.warning("Error disposing database connection pool: %s", e)


app = FastAPI(
    title="AI-Powered Multi-Agent Travel Planner",
    description="Production-grade AI Multi-Agent Travel Planner orchestrating Gemini, LangGraph, Tavily, AviationStack, and OpenWeather.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Streamlit frontend and local browser access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Exception Handler for custom application errors
@app.exception_handler(TravelPlannerException)
async def travel_planner_exception_handler(request: Request, exc: TravelPlannerException) -> JSONResponse:
    logger.warning("Application exception intercepted [%s]: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "details": exc.details},
    )


# Register Routers
app.include_router(health.router)
app.include_router(travel.router)
app.include_router(chat.router)


@app.get("/", tags=["Root"])
def root_status() -> dict:
    """Root landing endpoint."""
    return {
        "app": "AI-Powered Multi-Agent Travel Planner API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
    }

