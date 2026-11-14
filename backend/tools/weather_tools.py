
"""OpenWeather API integration for current weather and 5-day forecasts."""

from typing import Any

import httpx

from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.utils.logger import logger

settings = get_settings()

OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_current_weather(city: str) -> dict[str, Any]:
    """Retrieve current weather conditions for a city."""

    city = city.strip()

    if not city:
        return {"error": "City name cannot be empty."}

    if not settings.is_openweather_configured:
        return {"error": "OpenWeather API key not configured."}

    cache_key = f"weather:current:{city.lower()}"
    cached = redis_client.get(cache_key)

    if isinstance(cached, dict):
        logger.info("Retrieved current weather from cache for %s", city)
        return cached

    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        with httpx.Client(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
            response = client.get(OPENWEATHER_CURRENT_URL, params=params)

        if response.status_code == 404:
            return {"error": f"City '{city}' not found by OpenWeather API."}

        response.raise_for_status()

        data = response.json()
        main = data.get("main", {})
        weather_list = data.get("weather", [])
        wind = data.get("wind", {})

        result = {
            "temperature_celsius": main.get("temp"),
            "condition": (
                weather_list[0].get("description", "").title()
                if weather_list
                else "Unknown"
            ),
            "humidity": main.get("humidity"),
            "wind_speed_mps": wind.get("speed"),
            "city": data.get("name", city),
            "source": "OpenWeather API",
        }

        redis_client.set(
            cache_key,
            result,
            ttl_seconds=settings.CACHE_TTL_WEATHER,
        )

        return result

    except httpx.TimeoutException:
        logger.exception("Weather request timed out for %s", city)
        return {"error": "OpenWeather request timed out."}

    except httpx.HTTPStatusError as exc:
        logger.exception("OpenWeather HTTP error for %s", city)
        return {"error": f"OpenWeather HTTP error: {exc.response.status_code}"}

    except Exception:
        logger.exception("OpenWeather API error for %s", city)
        return {"error": "Unable to retrieve current weather."}


def get_forecast(city: str) -> dict[str, Any]:
    """Retrieve and summarize the 5-day, 3-hour weather forecast."""

    city = city.strip()

    if not city:
        return {"error": "City name cannot be empty."}

    if not settings.is_openweather_configured:
        return {"error": "OpenWeather API key not configured."}

    cache_key = f"weather:forecast:{city.lower()}"
    cached = redis_client.get(cache_key)

    if isinstance(cached, dict):
        logger.info("Retrieved forecast from cache for %s", city)
        return cached

    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        with httpx.Client(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
            response = client.get(OPENWEATHER_FORECAST_URL, params=params)

        response.raise_for_status()

        data = response.json()
        entries = data.get("list", [])

        if not entries:
            return {"error": "No forecast data available for this city."}

        temperatures = []
        conditions = []

        for item in entries:
            temperature = item.get("main", {}).get("temp")

            if temperature is not None:
                temperatures.append(temperature)

            weather = item.get("weather", [])
            if weather:
                condition = weather[0].get("main")
                if condition:
                    conditions.append(condition)

        average_temp = (
            round(sum(temperatures) / len(temperatures), 1)
            if temperatures
            else None
        )

        main_condition = (
            max(set(conditions), key=conditions.count)
            if conditions
            else "Unknown"
        )

        result = {
            "forecast_summary": (
                f"5-day forecast: Average temperature around "
                f"{average_temp}°C with predominantly "
                f"{main_condition} conditions."
            ),
            "forecast_available": True,
            "average_temp_celsius": average_temp,
            "source": "OpenWeather 5-Day Forecast API",
        }

        redis_client.set(
            cache_key,
            result,
            ttl_seconds=settings.CACHE_TTL_WEATHER,
        )

        return result

    except httpx.TimeoutException:
        logger.exception("Weather forecast request timed out for %s", city)
        return {"error": "OpenWeather forecast request timed out."}

    except httpx.HTTPStatusError as exc:
        logger.exception("OpenWeather forecast HTTP error for %s", city)
        return {
            "error": f"OpenWeather forecast HTTP error: {exc.response.status_code}"
        }

    except Exception:
        logger.exception("OpenWeather forecast error for %s", city)
        return {"error": "Unable to retrieve weather forecast."}
