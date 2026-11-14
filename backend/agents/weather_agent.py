
"""Weather specialist agent."""

import asyncio
import time
from datetime import date, datetime

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
    """Retrieve current weather and available forecast information."""

    start_time = time.perf_counter()

    logger.info(
        "Weather Agent started for %s (%s to %s)",
        destination,
        departure_date,
        return_date,
    )

    try:
        departure = datetime.strptime(
            departure_date,
            "%Y-%m-%d",
        ).date()

        days_until_departure = (departure - date.today()).days

        forecast_available = 0 <= days_until_departure <= 5

        # Retrieve current weather without blocking the event loop.
        current_data = await asyncio.to_thread(
            get_current_weather,
            destination,
        )

        if current_data.get("error") and not current_data.get(
            "temperature_celsius"
        ):
            return WeatherResult(
                status=AgentStatus.UNAVAILABLE,
                data=None,
                source="OpenWeather API",
                error=current_data["error"],
            )

        forecast_data = {}

        # Retrieve forecast only when the departure date is within range.
        if forecast_available:
            forecast_data = await asyncio.to_thread(
                get_forecast,
                destination,
            )

        temperature = current_data.get("temperature_celsius")
        condition = current_data.get("condition")
        humidity = current_data.get("humidity")
        wind_speed = current_data.get("wind_speed_mps")

        considerations = []

        if temperature is not None:
            if temperature > 28:
                considerations.append(
                    "High temperatures expected. Pack breathable clothing, "
                    "sunscreen, and stay hydrated."
                )
            elif temperature < 10:
                considerations.append(
                    "Cool to cold conditions expected. Bring warm layers "
                    "and a wind-resistant jacket."
                )
            else:
                considerations.append(
                    "Mild temperatures currently observed. "
                    "Layered casual clothing is recommended."
                )

        if condition and "rain" in condition.lower():
            considerations.append(
                "Rain conditions observed. Carry an umbrella "
                "or waterproof outerwear."
            )

        if forecast_available:
            forecast_summary = forecast_data.get("forecast_summary")

            if not forecast_summary:
                forecast_summary = (
                    "The departure date is within the five-day forecast "
                    "window, but forecast information could not be retrieved."
                )
        else:
            forecast_summary = (
                f"The departure date is {days_until_departure} days from today. "
                "It is outside the available five-day forecast window. "
                "Check the forecast closer to departure."
            )

        weather_info = WeatherInformation(
            temperature_celsius=temperature,
            condition=condition,
            humidity=humidity,
            wind_speed_mps=wind_speed,
            forecast_summary=forecast_summary,
            forecast_available=(
                forecast_available
                and bool(forecast_data.get("forecast_summary"))
            ),
            considerations=considerations,
            source="OpenWeather API",
        )

        elapsed = time.perf_counter() - start_time

        logger.info(
            "Weather Agent completed in %.2f seconds",
            elapsed,
        )

        return WeatherResult(
            status=AgentStatus.SUCCESS,
            data=weather_info,
            source="OpenWeather API",
            error=forecast_data.get("error"),
        )

    except Exception as exc:
        logger.exception("Weather Agent failed during execution")

        return WeatherResult(
            status=AgentStatus.FAILED,
            data=None,
            source="OpenWeather API",
            error=str(exc),
        )
