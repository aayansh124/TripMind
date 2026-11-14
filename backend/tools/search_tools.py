
"""Tavily search tools for destination and general travel queries."""

from typing import Any

from tavily import TavilyClient

from backend.clients.redis_client import redis_client
from backend.config.settings import get_settings
from backend.utils.logger import logger

settings = get_settings()


def search_travel_web(
    query: str,
    max_results: int = 5,
    cache_ttl: int | None = None,
) -> list[dict[str, Any]]:
    """Execute a Tavily web search with Redis caching."""

    query = " ".join(query.split())

    if not query:
        logger.warning("Web search skipped because the query is empty.")
        return []

    if max_results < 1:
        logger.warning("Web search skipped because max_results must be positive.")
        return []

    if not settings.is_tavily_configured:
        logger.warning(
            "Tavily API key is not configured. Search unavailable for: %s",
            query,
        )
        return []

    cache_key = f"search:{query.lower()}:{max_results}"

    cached = redis_client.get(cache_key)
    if isinstance(cached, list):
        logger.info("Retrieved search results from cache for: %s", query)
        return cached

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
        )

        results: list[dict[str, Any]] = []

        for item in response.get("results", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                }
            )

        ttl = (
            cache_ttl
            if cache_ttl is not None and cache_ttl > 0
            else settings.CACHE_TTL_DESTINATION
        )

        redis_client.set(
            cache_key,
            results,
            ttl_seconds=ttl,
        )

        logger.info(
            "Successfully fetched %d web results for: %s",
            len(results),
            query,
        )

        return results

    except Exception:
        logger.exception("Tavily search failed for query: %s", query)
        return []
