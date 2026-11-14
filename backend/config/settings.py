"""Application configuration and environment settings."""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Gemini LLM Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.4

    # External APIs
    TAVILY_API_KEY: str = ""
    AVIATIONSTACK_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""

    # Database Settings
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/travel_planner"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_TIMEOUT: int = 10

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SOCKET_TIMEOUT: float = 2.0
    REDIS_CONNECT_TIMEOUT: float = 2.0

    # Server Configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501

    # Cache TTLs (in seconds)
    CACHE_TTL_WEATHER: int = 1800        # 30 minutes
    CACHE_TTL_HOTEL: int = 3600          # 1 hour
    CACHE_TTL_DESTINATION: int = 86400   # 24 hours

    # Logging
    LOG_LEVEL: str = "INFO"

    # API Request Timeouts (seconds)
    EXTERNAL_API_TIMEOUT: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() and not self.GEMINI_API_KEY.startswith("your_"))

    @property
    def is_tavily_configured(self) -> bool:
        """Check if Tavily API key is configured."""
        return bool(self.TAVILY_API_KEY and self.TAVILY_API_KEY.strip() and not self.TAVILY_API_KEY.startswith("your_"))

    @property
    def is_aviationstack_configured(self) -> bool:
        """Check if AviationStack API key is configured."""
        return bool(self.AVIATIONSTACK_API_KEY and self.AVIATIONSTACK_API_KEY.strip() and not self.AVIATIONSTACK_API_KEY.startswith("your_"))

    @property
    def is_openweather_configured(self) -> bool:
        """Check if OpenWeather API key is configured."""
        return bool(self.OPENWEATHER_API_KEY and self.OPENWEATHER_API_KEY.strip() and not self.OPENWEATHER_API_KEY.startswith("your_"))


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()

