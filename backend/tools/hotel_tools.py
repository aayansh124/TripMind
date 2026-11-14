"""Hotel and accommodation discovery tool using Tavily search."""

from typing import Any, Dict, List, Optional
from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.tools.search_tools import search_travel_web
from backend.utils.logger import logger

settings = get_settings()


def search_accommodations(
    destination: str,
    travel_style: str = "Standard",
    accommodation_preference: Optional[str] = None,
    budget: Optional[float] = None,
    currency: str = "USD",
) -> List[Dict[str, Any]]:
    """Discover hotels and lodging options matching traveler criteria.

    Args:
        destination: City or region.
        travel_style: Style (Budget, Luxury, Family, Romantic, etc.).
        accommodation_preference: Hotel, Boutique, Resort, Hostel, etc.
        budget: Overall trip budget.
        currency: Currency code.

    Returns:
        List of accommodation raw search findings with URLs and snippets.
    """
    pref_term = accommodation_preference or "hotels"
    query = f"best {travel_style.lower()} {pref_term} in {destination} accommodations booking recommendations"

    cache_key = f"hotels:{destination.lower()}:{travel_style.lower()}:{pref_term.lower()}"
    cached = redis_client.get(cache_key)
    if cached is not None and isinstance(cached, list):
        logger.info("Retrieved accommodation search results from cache for %s", destination)
        return cached

    logger.info("Searching accommodations for %s (%s, %s)", destination, travel_style, pref_term)
    results = search_travel_web(query=query, max_results=6, cache_ttl=settings.CACHE_TTL_HOTEL)

    if results:
        redis_client.set(cache_key, results, ttl_seconds=settings.CACHE_TTL_HOTEL)

    return results

