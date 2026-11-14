"""Application configuration and environment settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini LLM Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = Field(default=0.4, ge=0.0, le=2.0)

    # External API Configuration
    TAVILY_API_KEY: str = ""
    AVIATIONSTACK_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    # PostgreSQL Configuration
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/travel_brain"
    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_TIMEOUT: int = Field(default=10, ge=1)

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SOCKET_TIMEOUT: float = 2.0
    REDIS_CONNECT_TIMEOUT: float = 2.0

    # Server Configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501

    # Cache TTL Configuration (seconds)
    CACHE_TTL_WEATHER: int = 1800
    CACHE_TTL_HOTEL: int = 3600
    CACHE_TTL_DESTINATION: int = 86400

    # Logging
    LOG_LEVEL: str = "INFO"

    # External API Timeout (seconds)
    EXTERNAL_API_TIMEOUT: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @staticmethod
    def _is_configured(value: str) -> bool:
        """Check whether an API key contains a configured value."""
        return bool(
            value
            and value.strip()
            and not value.strip().lower().startswith("your_")
        )

    @property
    def is_gemini_configured(self) -> bool:
        return self._is_configured(self.GEMINI_API_KEY)

    @property
    def is_tavily_configured(self) -> bool:
        return self._is_configured(self.TAVILY_API_KEY)

    @property
    def is_aviationstack_configured(self) -> bool:
        return self._is_configured(self.AVIATIONSTACK_API_KEY)

    @property
    def is_openweather_configured(self) -> bool:
        return self._is_configured(self.OPENWEATHER_API_KEY)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()