
"""Hotel specialist agent."""

import asyncio
import time
from typing import Optional

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from backend.api.schemas.travel import (
    AgentStatus,
    HotelInformation,
    HotelResult,
)
from backend.clients.llm_client import get_structured_llm
from backend.prompts.agent_prompts import HOTEL_AGENT_PROMPT
from backend.tools.hotel_tools import search_accommodations
from backend.utils.logger import logger


class HotelExtractionList(BaseModel):
    """Structured output schema for hotel recommendations."""

    hotels: list[HotelInformation] = Field(default_factory=list)


async def run_hotel_agent(
    destination: str,
    budget: float,
    currency: str,
    travellers: int,
    travel_style: str,
    accommodation_preference: Optional[str] = None,
    departure_date: Optional[str] = None,
    return_date: Optional[str] = None,
) -> HotelResult:
    """Discover and structure accommodation recommendations."""

    start_time = time.perf_counter()

    logger.info(
        "Hotel Agent started for %s (budget: %.2f %s)",
        destination,
        budget,
        currency,
    )

    raw_results = []

    # Discover accommodation options through Tavily.
    try:
        raw_results = await asyncio.to_thread(
            search_accommodations,
            destination=destination,
            travel_style=travel_style,
            accommodation_preference=accommodation_preference,
            budget=budget,
            currency=currency,
        )

    except Exception:
        logger.exception("Hotel search failed for %s", destination)

    hotels_list: list[HotelInformation] = []

    # Extract structured hotel details using Gemini.
    if raw_results:
        try:
            context_blocks = []

            for result in raw_results:
                context_blocks.append(
                    f"Title: {result.get('title', '')}\n"
                    f"URL: {result.get('url', '')}\n"
                    f"Content: {result.get('content', '')}"
                )

            search_context = "\n---\n".join(context_blocks)

            formatted_prompt = HOTEL_AGENT_PROMPT.format(
                destination=destination,
                budget=budget,
                currency=currency,
                travellers=travellers,
                travel_style=travel_style,
                accommodation_preference=(
                    accommodation_preference or "Hotel / Boutique stay"
                ),
                departure_date=departure_date or "Flexible",
                return_date=return_date or "Flexible",
                search_context=search_context,
            )

            structured_llm = get_structured_llm(HotelExtractionList)

            extraction: HotelExtractionList = await structured_llm.ainvoke(
                [
                    SystemMessage(content=formatted_prompt),
                    HumanMessage(
                        content=(
                            f"Extract 3-5 accommodation recommendations "
                            f"in {destination} matching {travel_style} style. "
                            "Only use details supported by the search results. "
                            "Do not invent prices, ratings, or availability."
                        )
                    ),
                ]
            )

            hotels_list = extraction.hotels

        except Exception:
            logger.exception(
                "Hotel extraction failed for %s; using raw search results",
                destination,
            )

            # Preserve discovered options when structured extraction fails.
            for result in raw_results[:4]:
                url = result.get("url")

                if not url:
                    continue

                hotels_list.append(
                    HotelInformation(
                        hotel_name=result.get(
                            "title",
                            f"Accommodation in {destination}",
                        )[:80],
                        location=destination,
                        description=result.get(
                            "content",
                            "Accommodation discovered through web search.",
                        )[:250],
                        estimated_price_per_night=None,
                        currency=currency,
                        rating=None,
                        website=url,
                        source_url=url,
                        is_verified_availability=False,
                    )
                )

    elapsed = time.perf_counter() - start_time

    logger.info(
        "Hotel Agent completed in %.2f seconds with %d recommendations",
        elapsed,
        len(hotels_list),
    )

    if hotels_list:
        return HotelResult(
            status=AgentStatus.SUCCESS,
            data=hotels_list,
            source="Tavily Web Search / Discovery",
        )

    return HotelResult(
        status=AgentStatus.UNAVAILABLE,
        data=[],
        source="Tavily Web Search / Discovery",
        error="No accommodation recommendations could be retrieved.",
        limitations=(
            "Hotel search results were unavailable. "
            "Check the Tavily API configuration and try again."
        ),
    )
