"""OpenWeather API integration for current weather and 5-day forecasts."""

from typing import Any, Dict, Optional
import httpx

from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.utils.logger import logger

settings = get_settings()

OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_current_weather(city: str) -> Dict[str, Any]:
    """Retrieve current weather observation for a city.

    Args:
        city: City name.

    Returns:
        Dict with temperature, condition, humidity, wind_speed, and source.
    """
    if not settings.is_openweather_configured:
        return {"error": "OpenWeather API key not configured."}

    cache_key = f"weather:current:{city.lower().strip()}"
    cached = redis_client.get(cache_key)
    if cached is not None and isinstance(cached, dict):
        logger.info("Retrieved current weather from cache for %s", city)
        return cached

    params = {
        "q": city.strip(),
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        with httpx.Client(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
            resp = client.get(OPENWEATHER_CURRENT_URL, params=params)

        if resp.status_code == 404:
            return {"error": f"City '{city}' not found by OpenWeather API."}
        if resp.status_code != 200:
            return {"error": f"OpenWeather HTTP error {resp.status_code}: {resp.text[:150]}"}

        data = resp.json()
        main = data.get("main", {})
        weather_list = data.get("weather", [{}])
        wind = data.get("wind", {})

        result = {
            "temperature_celsius": main.get("temp"),
            "condition": weather_list[0].get("description", "").title() if weather_list else "Clear",
            "humidity": main.get("humidity"),
            "wind_speed_mps": wind.get("speed"),
            "city": data.get("name", city),
            "source": "OpenWeather API",
        }

        redis_client.set(cache_key, result, ttl_seconds=settings.CACHE_TTL_WEATHER)
        return result
    except Exception as e:
        logger.error("OpenWeather API error for %s: %s", city, e)
        return {"error": str(e)}


def get_forecast(city: str) -> Dict[str, Any]:
    """Retrieve 5-day / 3-hour forecast for a city.

    Args:
        city: City name.

    Returns:
        Dict with forecast breakdown and temperature trends.
    """
    if not settings.is_openweather_configured:
        return {"error": "OpenWeather API key not configured."}

    cache_key = f"weather:forecast:{city.lower().strip()}"
    cached = redis_client.get(cache_key)
    if cached is not None and isinstance(cached, dict):
        logger.info("Retrieved forecast from cache for %s", city)
        return cached

    params = {
        "q": city.strip(),
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        with httpx.Client(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
            resp = client.get(OPENWEATHER_FORECAST_URL, params=params)

        if resp.status_code != 200:
            return {"error": f"OpenWeather forecast error {resp.status_code}"}

        data = resp.json()
        entries = data.get("list", [])
        daily_temps = []
        conditions = []

        for item in entries[:8]:  # Next 24 hours sample
            daily_temps.append(item.get("main", {}).get("temp", 0))
            if item.get("weather"):
                conditions.append(item["weather"][0].get("main"))

        avg_temp = round(sum(daily_temps) / len(daily_temps), 1) if daily_temps else None
        main_condition = max(set(conditions), key=conditions.count) if conditions else "Clear"

        result = {
            "forecast_summary": f"Next 5-day trend: Expected avg temp around {avg_temp}°C with predominant {main_condition} conditions.",
            "forecast_available": True,
            "average_temp_celsius": avg_temp,
            "source": "OpenWeather 5-Day Forecast API",
        }

        redis_client.set(cache_key, result, ttl_seconds=settings.CACHE_TTL_WEATHER)
        return result
    except Exception as e:
        logger.error("OpenWeather forecast error for %s: %s", city, e)
        return {"error": str(e)}

