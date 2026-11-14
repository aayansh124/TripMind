"""Weather Specialist Agent."""

import time
from datetime import datetime, date
from typing import List, Optional
from backend.api.schemas.travel import (
    AgentStatus,
    WeatherInformation,
    WeatherResult,
)
from backend.tools.weather_tools import get_current_weather, get_forecast
from backend.utils.logger import logger


async def run_weather_agent(
    destination: str,
    departure_date: str,
    return_date: str,
) -> WeatherResult:
    """Execute weather intelligence queries for the destination.

    Returns:
        Structured WeatherResult.
    """
    start_time = time.time()
    logger.info("Weather Agent started for %s (%s to %s)", destination, departure_date, return_date)

    try:
        # Check if travel departure is within OpenWeather 5-day horizon
        dep = datetime.strptime(departure_date, "%Y-%m-%d").date()
        today = date.today()
        days_until_dep = (dep - today).days

        is_within_forecast_window = (0 <= days_until_dep <= 5)

        # 1. Fetch current weather
        current_data = get_current_weather(destination)
        # 2. Fetch forecast if in range
        forecast_data = get_forecast(destination) if is_within_forecast_window else {}

        temp = current_data.get("temperature_celsius")
        cond = current_data.get("condition")
        humidity = current_data.get("humidity")
        wind = current_data.get("wind_speed_mps")

        considerations: List[str] = []
        if temp is not None:
            if temp > 28:
                considerations.append("High temperatures expected. Pack breathable clothing, sunscreen, and stay hydrated.")
            elif temp < 10:
                considerations.append("Cool to cold conditions expected. Bring warm layers, thermal wear, and a wind-resistant jacket.")
            else:
                considerations.append("Mild and pleasant weather. Layered casual attire recommended.")

        if cond and "rain" in cond.lower():
            considerations.append("Precipitation observed. Carry a compact umbrella or waterproof outerwear.")

        forecast_summary = None
        if is_within_forecast_window and "forecast_summary" in forecast_data:
            forecast_summary = forecast_data["forecast_summary"]
        else:
            forecast_summary = (
                f"Travel dates begin in {days_until_dep} days, beyond the live 5-day OpenWeather forecast window. "
                "Current baseline conditions shown above; check the live forecast closer to departure."
            )

        weather_info = WeatherInformation(
            temperature_celsius=temp,
            condition=cond,
            humidity=humidity,
            wind_speed_mps=wind,
            forecast_summary=forecast_summary,
            forecast_available=is_within_forecast_window,
            considerations=considerations,
            source="OpenWeather API",
        )

        elapsed = time.time() - start_time
        logger.info("Weather Agent completed in %.2fs", elapsed)

        return WeatherResult(
            status=AgentStatus.SUCCESS,
            data=weather_info,
            source="OpenWeather API",
            error=current_data.get("error"),
        )

    except Exception as e:
        logger.error("Weather Agent failed: %s", e)
        return WeatherResult(
            status=AgentStatus.FAILED,
            data=None,
            source="OpenWeather API",
            error=str(e),
        )

