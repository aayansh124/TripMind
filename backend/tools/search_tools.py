"""Tavily search tools for destination and general travel queries."""

from typing import Any, Dict, List, Optional
from tavily import TavilyClient

from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.utils.logger import logger

settings = get_settings()


def search_travel_web(query: str, max_results: int = 5, cache_ttl: Optional[int] = None) -> List[Dict[str, Any]]:
    """Execute a web search using Tavily API with caching and resilient error handling.

    Args:
        query: Search query string.
        max_results: Maximum number of search results to return.
        cache_ttl: Optional cache TTL in seconds. Defaults to CACHE_TTL_DESTINATION.

    Returns:
        List of result dictionaries containing 'title', 'content', 'url'.
    """
    if not settings.is_tavily_configured:
        logger.warning("Tavily API key not configured. Web search unavailable for query: %s", query)
        return []

    # 1. Check Redis Cache
    cache_key = f"search:{query.lower().strip()}:{max_results}"
    cached = redis_client.get(cache_key)
    if cached is not None and isinstance(cached, list):
        logger.info("Retrieved search results from cache for: %s", query)
        return cached

    # 2. Call Tavily API
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
        )

        results: List[Dict[str, Any]] = []
        raw_results = response.get("results", [])
        for item in raw_results:
            results.append({
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "url": item.get("url", ""),
            })

        # Cache the results
        ttl = cache_ttl or settings.CACHE_TTL_DESTINATION
        redis_client.set(cache_key, results, ttl_seconds=ttl)
        logger.info("Successfully fetched %d web results for: %s", len(results), query)
        return results
    except Exception as e:
        logger.error("Tavily search error for query '%s': %s", query, e)
        return []

