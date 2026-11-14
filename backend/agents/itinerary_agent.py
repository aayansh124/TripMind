
"""Itinerary specialist agent."""

import time

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

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
    """Structured output schema for daily itinerary generation."""

    days: list[DailyItinerary] = Field(default_factory=list)


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
    destination_res: DestinationResult | None = None,
    flight_res: FlightResult | None = None,
    hotel_res: HotelResult | None = None,
    weather_res: WeatherResult | None = None,
) -> ItineraryResult:
    """Generate a daily itinerary using specialist agent research."""

    start_time = time.perf_counter()

    logger.info(
        "Itinerary Agent started for %d days in %s",
        duration_days,
        destination,
    )

    # Prepare destination research summary.
    destination_summary = (
        "Explore historical centers, regional cuisine, and major monuments."
    )

    if destination_res and destination_res.data:
        destination_summary = (
            f"Overview: {destination_res.data.overview}\n"
            f"Highlights: {', '.join(destination_res.data.highlights[:5])}"
        )

    # Prepare accommodation summary.
    hotel_summary = "Accommodation options in the central city area."

    if hotel_res and hotel_res.data:
        hotel_names = [
            hotel.hotel_name
            for hotel in hotel_res.data[:3]
        ]
        hotel_summary = f"Suggested accommodation: {', '.join(hotel_names)}"

    # Prepare weather summary.
    weather_summary = "No verified weather information available."

    if weather_res and weather_res.data:
        weather_summary = (
            f"Temperature: {weather_res.data.temperature_celsius}°C, "
            f"Condition: {weather_res.data.condition}, "
            f"Forecast: {weather_res.data.forecast_summary}"
        )

    # Prepare flight summary.
    flight_summary = "No verified flight schedule information available."

    if flight_res and flight_res.data:
        flight_summary = (
            f"{len(flight_res.data)} flight schedules retrieved "
            f"for {origin} to {destination}."
        )

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
            destination_summary=destination_summary,
            hotel_summary=hotel_summary,
            weather_summary=weather_summary,
            flight_summary=flight_summary,
        )

        structured_llm = get_structured_llm(ItineraryWrapper)

        result: ItineraryWrapper = await structured_llm.ainvoke(
            [
                SystemMessage(content=formatted_prompt),
                HumanMessage(
                    content=(
                        f"Create a balanced {duration_days}-day itinerary "
                        f"for {destination}. Provide realistic activity cost "
                        f"estimates in {currency}. Cost estimates must cover "
                        f"all {travellers} traveler(s) combined. "
                        "Do not invent confirmed prices."
                    )
                ),
            ]
        )

        days = result.days

        # Ensure the generated itinerary covers the requested duration.
        if len(days) != duration_days:
            raise ValueError(
                f"Expected {duration_days} itinerary days, "
                f"but Gemini returned {len(days)}."
            )

        # Recalculate daily totals using deterministic arithmetic.
        for day in days:
            day.daily_total = round(
                day.estimated_transport_cost
                + day.estimated_food_cost
                + day.estimated_activity_cost,
                2,
            )

        elapsed = time.perf_counter() - start_time

        logger.info(
            "Itinerary Agent completed in %.2f seconds with %d days",
            elapsed,
            len(days),
        )

        return ItineraryResult(
            status=AgentStatus.SUCCESS,
            data=days,
            source="Gemini Itinerary Synthesis",
        )

    except Exception as exc:
        logger.exception(
            "Itinerary generation failed; using procedural fallback"
        )

        # Generate a basic itinerary when structured generation fails.
        fallback_days = []

        for day_number in range(1, duration_days + 1):
            fallback_days.append(
                DailyItinerary(
                    day=day_number,
                    date=None,
                    morning=[
                        f"Explore important landmarks in central {destination}."
                    ],
                    afternoon=[
                        f"Visit a cultural district or local market in {destination}.",
                        "Enjoy regional cuisine.",
                    ],
                    evening=[
                        f"Explore a scenic area of {destination} and enjoy dinner."
                    ],
                    places_to_visit=[
                        f"Major landmarks in {destination}",
                        f"Local attractions in {destination}",
                    ],
                    estimated_transport_cost=0.0,
                    estimated_food_cost=0.0,
                    estimated_activity_cost=0.0,
                    daily_total=0.0,
                )
            )

        elapsed = time.perf_counter() - start_time

        logger.warning(
            "Procedural itinerary generated in %.2f seconds",
            elapsed,
        )

        return ItineraryResult(
            status=AgentStatus.PARTIAL,
            data=fallback_days,
            source="Procedural Itinerary Synthesis",
            error=str(exc),
        )
