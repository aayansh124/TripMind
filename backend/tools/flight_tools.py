"""AviationStack flight intelligence tool."""

from typing import Any, Dict, List, Optional
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
) -> Dict[str, Any]:
    """Retrieve live flight data via AviationStack API with caching.

    Args:
        origin: Origin city or IATA airport code.
        destination: Destination city or IATA airport code.
        departure_date: Travel date (YYYY-MM-DD).
        limit: Max flights to retrieve.

    Returns:
        Dict with keys: 'flights' (list), 'source', 'limitations', 'error'.
    """
    result: Dict[str, Any] = {
        "flights": [],
        "source": "AviationStack API",
        "limitations": "AviationStack provides flight schedule status and timetable tracking. It does not provide real-time booking prices or inventory availability.",
        "error": None,
    }

    if not settings.is_aviationstack_configured:
        result["error"] = "AviationStack API key is not configured in .env."
        logger.warning("AviationStack API key not configured. Flight query skipped.")
        return result

    cache_key = f"flights:{origin.lower()}:{destination.lower()}:{departure_date or 'any'}"
    cached = redis_client.get(cache_key)
    if cached is not None and isinstance(cached, dict):
        logger.info("Retrieved flight data from cache for: %s -> %s", origin, destination)
        return cached

    params: Dict[str, Any] = {
        "access_key": settings.AVIATIONSTACK_API_KEY,
        "limit": limit,
    }

    # If 3-letter IATA code, filter by airport code, otherwise search
    if len(origin.strip()) == 3 and origin.strip().isalpha():
        params["dep_iata"] = origin.strip().upper()
    if len(destination.strip()) == 3 and destination.strip().isalpha():
        params["arr_iata"] = destination.strip().upper()

    try:
        with httpx.Client(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
            response = client.get(AVIATIONSTACK_BASE_URL, params=params)

        if response.status_code != 200:
            result["error"] = f"AviationStack HTTP error {response.status_code}: {response.text[:200]}"
            logger.warning("AviationStack error: %s", result["error"])
            return result

        data = response.json()
        if "error" in data:
            error_info = data["error"].get("message", "Unknown AviationStack error")
            result["error"] = error_info
            logger.warning("AviationStack returned API error: %s", error_info)
            return result

        raw_flights = data.get("data", [])
        parsed_flights: List[Dict[str, Any]] = []

        for item in raw_flights:
            flight_info = item.get("flight", {})
            departure = item.get("departure", {})
            arrival = item.get("arrival", {})
            airline = item.get("airline", {})

            parsed_flights.append({
                "airline": airline.get("name"),
                "flight_number": flight_info.get("iata") or flight_info.get("number"),
                "departure_airport": departure.get("airport") or departure.get("iata"),
                "arrival_airport": arrival.get("airport") or arrival.get("iata"),
                "departure_time": departure.get("scheduled"),
                "arrival_time": arrival.get("scheduled"),
                "flight_status": item.get("flight_status", "scheduled"),
                "price": None,  # AviationStack does not provide verified fare pricing
                "currency": None,
                "is_verified_price": False,
                "source": "AviationStack API",
                "note": "Timetable schedule retrieved via AviationStack.",
            })

        result["flights"] = parsed_flights
        redis_client.set(cache_key, result, ttl_seconds=settings.CACHE_TTL_HOTEL)
        logger.info("Successfully fetched %d flights from AviationStack", len(parsed_flights))
        return result
    except Exception as e:
        logger.error("Exception querying AviationStack for %s -> %s: %s", origin, destination, e)
        result["error"] = str(e)
        return result

