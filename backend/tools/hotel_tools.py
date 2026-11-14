
"""Hotel and accommodation discovery tool using Tavily search."""

from typing import Any

from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.tools.search_tools import search_travel_web
from backend.utils.logger import logger

settings = get_settings()


def search_accommodations(
    destination: str,
    travel_style: str = "Standard",
    accommodation_preference: str | None = None,
    budget: float | None = None,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Discover accommodation options matching traveler criteria."""

    destination = destination.strip()
    travel_style = travel_style.strip()
    pref_term = (accommodation_preference or "hotels").strip()
    currency = currency.strip().upper()

    query = (
        f"best {travel_style.lower()} {pref_term} in {destination} "
        "accommodation recommendations with booking links"
    )

    if budget is not None:
        query += (
            f". Traveler's overall trip budget is "
            f"{budget} {currency}; prioritize affordable options."
        )

    cache_key = (
        f"hotels:{destination.lower()}:{travel_style.lower()}:"
        f"{pref_term.lower()}:{budget}:{currency}"
    )

    cached = redis_client.get(cache_key)
    if isinstance(cached, list):
        logger.info(
            "Retrieved accommodation results from cache for %s",
            destination,
        )
        return cached

    logger.info(
        "Searching accommodations for %s (%s, %s)",
        destination,
        travel_style,
        pref_term,
    )

    results = search_travel_web(
        query=query,
        max_results=6,
        cache_ttl=settings.CACHE_TTL_HOTEL,
    )

    if results:
        redis_client.set(
            cache_key,
            results,
            ttl_seconds=settings.CACHE_TTL_HOTEL,
        )

    return results
