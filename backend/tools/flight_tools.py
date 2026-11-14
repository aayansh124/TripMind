
"""AviationStack flight intelligence tool."""

from typing import Any, Optional

import httpx

from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.utils.logger import logger


settings = get_settings()

AVIATIONSTACK_BASE_URL = "http://api.aviationstack.com/v1/flights"


def search_flights(
    origin: str,
    destination: str,
    departure_date: Optional[str] = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Retrieve flight schedule information from AviationStack."""

    result: dict[str, Any] = {
        "flights": [],
        "source": "AviationStack API",
        "limitations": (
            "AviationStack provides flight schedule and status information. "
            "It does not provide verified ticket prices or booking inventory."
        ),
        "error": None,
    }

    if not settings.is_aviationstack_configured:
        result["error"] = (
            "AviationStack API key is not configured in the environment."
        )

        logger.warning("AviationStack API key is not configured.")

        return result

    origin = origin.strip().upper()
    destination = destination.strip().upper()

    cache_key = (
        f"flights:{origin}:{destination}:"
        f"{departure_date or 'any'}:{limit}"
    )

    cached = redis_client.get(cache_key)

    if isinstance(cached, dict):
        logger.info(
            "Retrieved flight data from cache for %s -> %s",
            origin,
            destination,
        )
        return cached

    params: dict[str, Any] = {
        "access_key": settings.AVIATIONSTACK_API_KEY,
        "limit": limit,
    }

    # Apply the departure date when provided.
    if departure_date:
        params["flight_date"] = departure_date

    # Apply airport filters when IATA codes are provided.
    if len(origin) == 3 and origin.isalpha():
        params["dep_iata"] = origin

    if len(destination) == 3 and destination.isalpha():
        params["arr_iata"] = destination

    try:
        with httpx.Client(
            timeout=settings.EXTERNAL_API_TIMEOUT
        ) as client:
            response = client.get(
                AVIATIONSTACK_BASE_URL,
                params=params,
            )

        if response.status_code != 200:
            result["error"] = (
                f"AviationStack HTTP error: {response.status_code}"
            )

            logger.warning(
                "AviationStack returned HTTP status %s",
                response.status_code,
            )

            return result

        data = response.json()

        if data.get("error"):
            error_message = data["error"].get(
                "message",
                "Unknown AviationStack API error.",
            )

            result["error"] = error_message

            logger.warning(
                "AviationStack API error: %s",
                error_message,
            )

            return result

        raw_flights = data.get("data", [])
        parsed_flights = []

        for item in raw_flights:
            flight_info = item.get("flight", {})
            departure = item.get("departure", {})
            arrival = item.get("arrival", {})
            airline = item.get("airline", {})

            parsed_flights.append(
                {
                    "airline": airline.get("name"),
                    "flight_number": (
                        flight_info.get("iata")
                        or flight_info.get("number")
                    ),
                    "departure_airport": (
                        departure.get("airport")
                        or departure.get("iata")
                    ),
                    "arrival_airport": (
                        arrival.get("airport")
                        or arrival.get("iata")
                    ),
                    "departure_time": departure.get("scheduled"),
                    "arrival_time": arrival.get("scheduled"),
                    "flight_status": item.get(
                        "flight_status",
                        "scheduled",
                    ),
                    "price": None,
                    "currency": None,
                    "is_verified_price": False,
                    "source": "AviationStack API",
                    "note": (
                        "Flight timetable retrieved from AviationStack. "
                        "Ticket price is not provided by this result."
                    ),
                }
            )

        result["flights"] = parsed_flights

        redis_client.set(
            cache_key,
            result,
            ttl_seconds=settings.CACHE_TTL_HOTEL,
        )

        logger.info(
            "Retrieved %d flight records for %s -> %s",
            len(parsed_flights),
            origin,
            destination,
        )

        return result

    except httpx.TimeoutException:
        result["error"] = "AviationStack request timed out."
        logger.exception("AviationStack request timed out.")

        return result

    except Exception as exc:
        result["error"] = str(exc)

        logger.exception(
            "AviationStack request failed for %s -> %s",
            origin,
            destination,
        )

        return result
