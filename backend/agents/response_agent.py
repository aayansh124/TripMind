
"""Response synthesizer agent."""

import time

from backend.api.schemas.travel import (
    AgentStatus,
    BudgetBreakdown,
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
    DailyItinerary,
)
from backend.services.budget_service import calculate_budget_breakdown
from backend.utils.logger import logger


async def run_response_agent(
    trip_id: str,
    request: TravelRequest,
    duration_days: int,
    destination_res: DestinationResult | None = None,
    flight_res: FlightResult | None = None,
    hotel_res: HotelResult | None = None,
    weather_res: WeatherResult | None = None,
    itinerary_days: list[DailyItinerary] | None = None,
    itinerary_status: AgentStatus | None = None,
) -> TravelPlan:
    """Consolidate agent results and generate the final travel plan."""

    start_time = time.perf_counter()

    logger.info(
        "Response Agent started for trip_id: %s",
        trip_id,
    )

    sources = ["Multi-Agent Travel Planner"]
    warnings = []

    # Process destination information.
    destination_overview = DestinationOverview(
        overview=(
            f"Basic destination information for {request.destination}. "
            "Detailed destination research was unavailable."
        ),
        highlights=[],
        activities=[],
        cultural_tips=[],
        potential_constraints=[],
    )

    if destination_res and destination_res.data:
        destination_overview = destination_res.data
        sources.extend(destination_res.source)

        if destination_res.status != AgentStatus.SUCCESS:
            warnings.append(
                "Destination information is partially available."
            )
    else:
        warnings.append("Destination research was unavailable.")

    # Process flight information.
    flights_data: list[FlightInformation] = []

    if flight_res and flight_res.data:
        flights_data = flight_res.data
        sources.append(flight_res.source)

    if not flight_res or flight_res.status != AgentStatus.SUCCESS:
        warnings.append(
            "Flight information is incomplete or unavailable. "
            "Verify schedules and ticket prices directly with airlines."
        )

    if flight_res and flight_res.limitations:
        warnings.append(flight_res.limitations)

    # Process accommodation information.
    hotels_data: list[HotelInformation] = []

    if hotel_res and hotel_res.data:
        hotels_data = hotel_res.data
        sources.append(hotel_res.source)

        warnings.append(
            "Hotel recommendations are based on web discovery. "
            "Confirm prices and room availability with the property "
            "or booking provider."
        )
    else:
        warnings.append(
            "No accommodation recommendations were retrieved. "
            "Check hotel options directly before traveling."
        )

    if hotel_res and hotel_res.limitations:
        warnings.append(hotel_res.limitations)

    # Process weather information.
    weather_info: WeatherInformation | None = None

    if weather_res and weather_res.data:
        weather_info = weather_res.data
        sources.append(weather_res.source)

        if not weather_info.forecast_available:
            warnings.append(
                "A live forecast for the requested travel dates "
                "is not currently available."
            )
    else:
        warnings.append(
            "Weather information is unavailable for the destination."
        )

    # Process generated itinerary.
    itinerary = itinerary_days or []

    if not itinerary:
        warnings.append(
            "A detailed day-by-day itinerary could not be generated."
        )

    if itinerary_status != AgentStatus.SUCCESS:
        warnings.append(
            "Itinerary generation was partial or unavailable. "
            "Review the daily plan before traveling."
        )

    # Calculate the overall budget using deterministic Python arithmetic.
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

    # Handle complete and incomplete budget comparisons separately.
    if not budget_breakdown.comparison_available:
        warnings.append(
            "The budget estimate is incomplete because some expense "
            "categories are unavailable. The total should not be treated "
            "as a complete comparison against your allocated budget."
        )
    elif budget_breakdown.is_within_budget is False:
        warnings.append(
            f"Estimated expenses exceed the allocated budget by "
            f"{budget_breakdown.overrun_amount:.2f} "
            f"{request.currency}."
        )

    # Compile practical travel tips.
    travel_tips = [
        (
            f"Keep digital and physical copies of travel documents "
            f"when traveling to {request.destination}."
        ),
        "Review your travel arrangements before departure.",
        (
            "Confirm accommodation bookings and transport schedules "
            "directly with the respective providers."
        ),
    ]

    if weather_info and weather_info.considerations:
        travel_tips.extend(weather_info.considerations)

    if destination_overview.cultural_tips:
        travel_tips.extend(destination_overview.cultural_tips[:3])

    # Remove duplicate sources and warnings while preserving their order.
    unique_sources = list(dict.fromkeys(sources))
    unique_warnings = list(dict.fromkeys(warnings))

    # Determine overall execution status.
    agent_statuses = [
        destination_res.status if destination_res else AgentStatus.UNAVAILABLE,
        flight_res.status if flight_res else AgentStatus.UNAVAILABLE,
        hotel_res.status if hotel_res else AgentStatus.UNAVAILABLE,
        weather_res.status if weather_res else AgentStatus.UNAVAILABLE,
        itinerary_status or AgentStatus.UNAVAILABLE,
    ]

    if (
        all(status == AgentStatus.SUCCESS for status in agent_statuses)
        and not unique_warnings
    ):
        execution_status = AgentStatus.SUCCESS
    else:
        execution_status = AgentStatus.PARTIAL

    # Assemble the final travel plan.
    plan = TravelPlan(
        trip_id=trip_id,
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
        duration_days=duration_days,
        travellers=request.travellers,
        budget={
            "amount": request.budget,
            "currency": request.currency,
        },
        travel_style=request.travel_style.value,
        destination_overview=destination_overview,
        flights=flights_data,
        hotels=hotels_data,
        weather=weather_info,
        itinerary=itinerary,
        budget_breakdown=budget_breakdown,
        travel_tips=travel_tips,
        sources=unique_sources,
        warnings=unique_warnings,
        execution_status=execution_status,
    )

    elapsed = time.perf_counter() - start_time

    logger.info(
        "Response Agent completed in %.2f seconds for trip_id: %s",
        elapsed,
        trip_id,
    )

    return plan
