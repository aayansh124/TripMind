"""Response Synthesizer Agent."""

import time
from typing import Any, Dict, List, Optional

from backend.api.schemas.travel import (
    AgentStatus,
    BudgetBreakdown,
    DailyItinerary,
    DestinationOverview,
    DestinationResult,
    FlightInformation,
    FlightResult,
    HotelInformation,
    HotelResult,
    TravelPlan,
    TravelRequest,
    WeatherInformation,
    WeatherResult,
)
from backend.services.budget_service import calculate_budget_breakdown
from backend.utils.logger import logger


async def run_response_agent(
    trip_id: str,
    request: TravelRequest,
    duration_days: int,
    destination_res: Optional[DestinationResult] = None,
    flight_res: Optional[FlightResult] = None,
    hotel_res: Optional[HotelResult] = None,
    weather_res: Optional[WeatherResult] = None,
    itinerary_days: Optional[List[DailyItinerary]] = None,
) -> TravelPlan:
    """Consolidate research findings, run deterministic budget checks, and synthesize final plan.

    Returns:
        Consolidated TravelPlan.
    """
    start_time = time.time()
    logger.info("Response Agent consolidating final plan for trip_id: %s", trip_id)

    # 1. Aggregate sources and warnings
    sources: List[str] = ["Antigravity Multi-Agent Orchestrator"]
    warnings: List[str] = []

    # Process Destination
    dest_overview = DestinationOverview(
        overview=f"Welcome to {request.destination}! An exciting journey awaits.",
        highlights=[f"Historic central {request.destination}"],
        activities=["Sightseeing walking tours", "Regional dining"],
        cultural_tips=["Follow standard local etiquette and currency exchange guidance."],
        potential_constraints=["Verify opening hours of seasonal monuments."],
    )
    if destination_res and destination_res.data:
        dest_overview = destination_res.data
        if destination_res.source:
            sources.extend(destination_res.source)
    else:
        warnings.append("Destination overview generated from base geographical knowledge.")

    # Process Flights
    flights_data: List[FlightInformation] = []
    if flight_res and flight_res.data:
        flights_data = flight_res.data
        sources.append("AviationStack API")
        if flight_res.limitations:
            warnings.append(f"Flight status note: {flight_res.limitations}")
    else:
        warnings.append("Real-time flight pricing is unverified. Consult airlines for live booking tickets.")

    # Process Hotels
    hotels_data: List[HotelInformation] = []
    if hotel_res and hotel_res.data:
        hotels_data = hotel_res.data
        sources.append("Tavily Web Search")
        warnings.append("Hotel prices and room availability are web discovery estimates and require direct confirmation.")
    else:
        warnings.append("Accommodation recommendations were generated using general area knowledge.")

    # Process Weather
    weather_info: Optional[WeatherInformation] = None
    if weather_res and weather_res.data:
        weather_info = weather_res.data
        sources.append("OpenWeather API")
        if not weather_info.forecast_available:
            warnings.append("Travel dates exceed the 5-day live forecast window. Historical weather trends applied.")
    else:
        warnings.append("Weather service observation unavailable for destination.")

    # Process Itinerary
    itinerary = itinerary_days or []

    # 2. Run Deterministic Budget Service
    budget_breakdown: BudgetBreakdown = calculate_budget_breakdown(
        user_budget=request.budget,
        currency=request.currency,
        duration_days=duration_days,
        travellers=request.travellers,
        travel_style=request.travel_style,
        hotels=hotels_data,
        itinerary_days=itinerary,
        flights=flights_data,
    )

    if not budget_breakdown.is_within_budget:
        warnings.append(
            f"Budget alert: Total estimated cost ({budget_breakdown.total_estimated_cost:.2f} {request.currency}) "
            f"exceeds user budget by {budget_breakdown.overrun_amount:.2f} {request.currency}."
        )

    # 3. Compile Travel Tips
    travel_tips: List[str] = [
        f"Keep digital and physical copies of travel IDs when traveling to {request.destination}.",
        f"Recommended travel style is {request.travel_style.value}. Adjust daily pacing accordingly.",
        f"Carry a payment card with zero foreign transaction fees in {request.currency}.",
    ]
    if weather_info and weather_info.considerations:
        travel_tips.extend(weather_info.considerations)
    if dest_overview.cultural_tips:
        travel_tips.extend(dest_overview.cultural_tips[:3])

    # Deduplicate sources preserving order
    unique_sources = list(dict.fromkeys(sources))

    plan = TravelPlan(
        trip_id=trip_id,
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
        duration_days=duration_days,
        travellers=request.travellers,
        budget={"amount": request.budget, "currency": request.currency},
        travel_style=request.travel_style.value,
        destination_overview=dest_overview,
        flights=flights_data,
        hotels=hotels_data,
        weather=weather_info,
        itinerary=itinerary,
        budget_breakdown=budget_breakdown,
        travel_tips=travel_tips,
        sources=unique_sources,
        warnings=warnings,
        execution_status=AgentStatus.SUCCESS if len(warnings) < 3 else AgentStatus.PARTIAL,
    )

    elapsed = time.time() - start_time
    logger.info("Response Agent finished plan assembly in %.2fs", elapsed)

    return plan

