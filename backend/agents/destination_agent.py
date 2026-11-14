
"""Destination specialist agent."""

import asyncio
import time
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from backend.api.schemas.travel import (
    AgentStatus,
    DestinationOverview,
    DestinationResult,
)
from backend.clients.llm_client import get_structured_llm
from backend.prompts.agent_prompts import DESTINATION_AGENT_PROMPT
from backend.tools.search_tools import search_travel_web
from backend.utils.logger import logger


async def run_destination_agent(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    duration_days: int,
    travellers: int,
    travel_style: str,
    preferences: Optional[str] = None,
) -> DestinationResult:
    """Generate destination insights using web search and Gemini."""

    start_time = time.perf_counter()

    logger.info(
        "Destination Agent started for %s (style: %s)",
        destination,
        travel_style,
    )

    search_context = ""
    sources: list[str] = []

    # Retrieve recent destination information from Tavily.
    try:
        query = (
            f"top attractions travel guide {destination} "
            f"{travel_style} must see places"
        )

        search_results = await asyncio.to_thread(
            search_travel_web,
            query,
            max_results=4,
        )

        if search_results:
            context_blocks = []

            for item in search_results:
                title = item.get("title", "")
                snippet = item.get("content", "")
                url = item.get("url", "")

                if url:
                    sources.append(url)

                context_blocks.append(
                    f"Title: {title}\nSnippet: {snippet}"
                )

            search_context = "\n---\n".join(context_blocks)

    except Exception:
        logger.exception(
            "Destination web search failed for %s",
            destination,
        )

    # Generate structured destination insights using Gemini.
    try:
        formatted_prompt = DESTINATION_AGENT_PROMPT.format(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            duration_days=duration_days,
            travellers=travellers,
            travel_style=travel_style,
            preferences=preferences or "None specified",
            search_context=(
                search_context
                or "No real-time web results available. Using baseline knowledge."
            ),
        )

        structured_llm = get_structured_llm(DestinationOverview)

        overview: DestinationOverview = await structured_llm.ainvoke(
            [
                SystemMessage(content=formatted_prompt),
                HumanMessage(
                    content=(
                        f"Please provide detailed destination insights "
                        f"and attractions for {destination}."
                    )
                ),
            ]
        )

        elapsed = time.perf_counter() - start_time

        logger.info(
            "Destination Agent completed in %.2f seconds",
            elapsed,
        )

        return DestinationResult(
            status=AgentStatus.SUCCESS,
            data=overview,
            source=["Gemini AI"] + sources,
        )

    except Exception as exc:
        logger.exception(
            "Destination Agent failed during Gemini inference"
        )

        # Provide baseline destination information when Gemini fails.
        fallback_overview = DestinationOverview(
            overview=(
                f"Explore the historic sights, cultural vibrant quarters, "
                f"and scenic locations of {destination}."
            ),
            highlights=[
                f"Downtown and historic center of {destination}",
                "Major cultural landmarks and city museums",
                "Scenic viewpoints and waterfront promenades",
            ],
            activities=[
                f"Walking tour around the key districts of {destination}",
                "Sample regional cuisine at local eateries",
                f"Visit renowned cultural sights tailored to {travel_style} travel",
            ],
            cultural_tips=[
                "Carry local currency for smaller vendors.",
                "Verify standard tipping etiquette and transit ticketing.",
            ],
            potential_constraints=[
                "Check seasonal operating hours for local monuments.",
            ],
        )

        return DestinationResult(
            status=AgentStatus.PARTIAL,
            data=fallback_overview,
            source=["Fallback Knowledge"] + sources,
            error=str(exc),
        )
