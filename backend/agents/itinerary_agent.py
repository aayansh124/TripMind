"""Itinerary Specialist Agent."""

import time
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from backend.api.schemas.travel import (
    AgentStatus,
    DailyItinerary,
    DestinationResult,
    FlightResult,
    HotelResult,
    ItineraryResult,
    WeatherResult,
)
from backend.clients.llm_client import get_structured_llm
from backend.prompts.agent_prompts import ITINERARY_AGENT_PROMPT
from backend.utils.logger import logger


class ItineraryWrapper(BaseModel):
    """Pydantic model for structured itinerary output from LLM."""
    days: List[DailyItinerary] = Field(default_factory=list)


async def run_itinerary_agent(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    duration_days: int,
    travellers: int,
    budget: float,
    currency: str,
    travel_style: str,
    destination_res: Optional[DestinationResult] = None,
    flight_res: Optional[FlightResult] = None,
    hotel_res: Optional[HotelResult] = None,
    weather_res: Optional[WeatherResult] = None,
) -> ItineraryResult:
    """Synthesize upstream agent research into a daily itinerary.

    Returns:
        Structured ItineraryResult.
    """
    start_time = time.time()
    logger.info("Itinerary Agent started for %d days in %s", duration_days, destination)

    # 1. Summarize upstream inputs
    dest_summary = "Explore historical centers, regional cuisine, and top monuments."
    if destination_res and destination_res.data:
        dest_summary = f"Overview: {destination_res.data.overview}\nHighlights: {', '.join(destination_res.data.highlights[:5])}"

    hotel_summary = "Accommodations in central city area."
    if hotel_res and hotel_res.data:
        hotel_names = [h.hotel_name for h in hotel_res.data[:3]]
        hotel_summary = f"Suggested bases: {', '.join(hotel_names)}"

    weather_summary = "Standard seasonal conditions."
    if weather_res and weather_res.data:
        weather_summary = f"Temp: {weather_res.data.temperature_celsius}°C, Condition: {weather_res.data.condition}"

    flight_summary = "Flight timetable scheduled."
    if flight_res and flight_res.data:
        flight_summary = f"{len(flight_res.data)} flight schedules available from {origin} to {destination}."

    # 2. Invoke Gemini for day-wise itinerary generation
    try:
        formatted_prompt = ITINERARY_AGENT_PROMPT.format(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            duration_days=duration_days,
            travellers=travellers,
            budget=budget,
            currency=currency,
            travel_style=travel_style,
            destination_summary=dest_summary,
            hotel_summary=hotel_summary,
            weather_summary=weather_summary,
            flight_summary=flight_summary,
        )

        structured_llm = get_structured_llm(ItineraryWrapper)
        result: ItineraryWrapper = await structured_llm.ainvoke([
            SystemMessage(content=formatted_prompt),
            HumanMessage(content=f"Create a balanced {duration_days}-day itinerary for {destination}."),
        ])

        days = result.days

        # Ensure daily total consistency
        for d in days:
            if d.daily_total == 0.0:
                d.daily_total = round(
                    d.estimated_transport_cost + d.estimated_food_cost + d.estimated_activity_cost, 2
                )

        elapsed = time.time() - start_time
        logger.info("Itinerary Agent completed in %.2fs with %d days planned", elapsed, len(days))

        return ItineraryResult(
            status=AgentStatus.SUCCESS,
            data=days,
            source="Gemini Itinerary Synthesis",
        )

    except Exception as e:
        logger.warning("Itinerary Agent LLM call encountered error: %s. Generating robust procedural fallback.", e)
        # Fallback procedural generation if LLM is unavailable or unconfigured
        fallback_days = []
        for i in range(1, duration_days + 1):
            day_cost = round((budget * 0.4) / duration_days, 2)
            fallback_days.append(
                DailyItinerary(
                    day=i,
                    date=None,
                    morning=[
                        f"Day {i} Morning: Explore key landmarks and architectural walking tour in central {destination}."
                    ],
                    afternoon=[
                        f"Day {i} Afternoon: Visit primary cultural district, museum, or market followed by regional lunch."
                    ],
                    evening=[
                        f"Day {i} Evening: Leisure walk along prominent avenue, scenic dinner, and local relaxation."
                    ],
                    places_to_visit=[f"District {i} Highlights", f"{destination} Scenic Center"],
                    estimated_transport_cost=round(day_cost * 0.2, 2),
                    estimated_food_cost=round(day_cost * 0.5, 2),
                    estimated_activity_cost=round(day_cost * 0.3, 2),
                    daily_total=day_cost,
                )
            )

        return ItineraryResult(
            status=AgentStatus.PARTIAL,
            data=fallback_days,
            source="Procedural Itinerary Synthesis",
            error=str(e),
        )

