"""Deterministic budget calculation and reconciliation service."""

import math
from typing import List, Optional
from backend.api.schemas.travel import (
    BudgetBreakdown,
    DailyItinerary,
    FlightInformation,
    HotelInformation,
    TravelStyle,
)
from backend.utils.logger import logger

# Baseline per-person daily expense heuristics when specific itemized costs are absent
DAILY_STYLE_ESTIMATES = {
    TravelStyle.BUDGET: {"hotel": 50.0, "food": 25.0, "transport": 10.0, "activity": 15.0},
    TravelStyle.STANDARD: {"hotel": 120.0, "food": 55.0, "transport": 20.0, "activity": 35.0},
    TravelStyle.LUXURY: {"hotel": 350.0, "food": 150.0, "transport": 70.0, "activity": 100.0},
    TravelStyle.ADVENTURE: {"hotel": 80.0, "food": 35.0, "transport": 25.0, "activity": 60.0},
    TravelStyle.FAMILY: {"hotel": 160.0, "food": 60.0, "transport": 30.0, "activity": 40.0},
    TravelStyle.ROMANTIC: {"hotel": 200.0, "food": 90.0, "transport": 35.0, "activity": 60.0},
    TravelStyle.CULTURAL: {"hotel": 110.0, "food": 50.0, "transport": 20.0, "activity": 45.0},
}


def calculate_budget_breakdown(
    user_budget: float,
    currency: str,
    duration_days: int,
    travellers: int,
    travel_style: TravelStyle,
    hotels: Optional[List[HotelInformation]] = None,
    itinerary_days: Optional[List[DailyItinerary]] = None,
    flights: Optional[List[FlightInformation]] = None,
) -> BudgetBreakdown:
    """Calculate deterministic budget projections using strict Python arithmetic.

    Does not rely on LLM arithmetic to guarantee accurate financial totals and comparisons.

    Args:
        user_budget: Total spending ceiling provided by traveler.
        currency: Base currency string.
        duration_days: Total length of travel in days.
        travellers: Count of travelers.
        travel_style: Category style (Budget, Standard, Luxury, etc.).
        hotels: Recommended hotels list.
        itinerary_days: Day-by-day plan with individual activity allocations.
        flights: Retrieved flight information.

    Returns:
        Structured BudgetBreakdown with totals, overrun checks, and explicit calculation notes.
    """
    notes: List[str] = []
    nights = max(1, duration_days - 1)
    rooms = max(1, math.ceil(travellers / 2))
    style_defaults = DAILY_STYLE_ESTIMATES.get(travel_style, DAILY_STYLE_ESTIMATES[TravelStyle.STANDARD])

    # 1. Flight Cost Calculation
    flight_cost: Optional[float] = None
    if flights:
        verified_prices = [f.price for f in flights if f.price is not None and f.is_verified_price]
        if verified_prices:
            # Average verified one-way/round-trip price multiplied by travelers
            flight_cost = round(sum(verified_prices) / len(verified_prices) * travellers, 2)
            notes.append(f"Flight estimate based on {len(verified_prices)} verified flight schedules.")
        else:
            notes.append("Flight prices are unverified from the public aviation feed and excluded from confirmed total.")
    else:
        notes.append("No flight routes retrieved; flight cost not factored into confirmed total.")

    # 2. Hotel Cost Calculation
    hotel_cost: float = 0.0
    valid_hotel_rates = [
        h.estimated_price_per_night for h in (hotels or [])
        if h.estimated_price_per_night is not None and h.estimated_price_per_night > 0
    ]
    if valid_hotel_rates:
        avg_nightly_rate = sum(valid_hotel_rates) / len(valid_hotel_rates)
        hotel_cost = round(avg_nightly_rate * nights * rooms, 2)
        notes.append(f"Lodging estimated at ~{avg_nightly_rate:.2f} {currency}/night for {rooms} room(s) across {nights} night(s).")
    else:
        # Fallback to style default per room
        hotel_cost = round(style_defaults["hotel"] * nights * rooms, 2)
        notes.append(f"Lodging estimated using {travel_style.value} baseline (~{style_defaults['hotel']:.0f} {currency}/night/room).")

    # 3. Itinerary Daily Costs (Food, Transport, Activities)
    food_total: float = 0.0
    transport_total: float = 0.0
    activities_total: float = 0.0

    if itinerary_days and len(itinerary_days) > 0:
        for day in itinerary_days:
            food_total += day.estimated_food_cost
            transport_total += day.estimated_transport_cost
            activities_total += day.estimated_activity_cost

        # If itinerary costs were left at zero by synthesis, use baselines
        if food_total == 0.0:
            food_total = round(style_defaults["food"] * duration_days * travellers, 2)
        if transport_total == 0.0:
            transport_total = round(style_defaults["transport"] * duration_days * travellers, 2)
        if activities_total == 0.0:
            activities_total = round(style_defaults["activity"] * duration_days * travellers, 2)
    else:
        food_total = round(style_defaults["food"] * duration_days * travellers, 2)
        transport_total = round(style_defaults["transport"] * duration_days * travellers, 2)
        activities_total = round(style_defaults["activity"] * duration_days * travellers, 2)

    notes.append(f"Dining estimate: {food_total:.2f} {currency} ({duration_days} days, {travellers} traveler(s)).")
    notes.append(f"Local transit estimate: {transport_total:.2f} {currency}.")
    notes.append(f"Sightseeing & tickets estimate: {activities_total:.2f} {currency}.")

    # 4. Total Calculation
    total_components = [hotel_cost, food_total, transport_total, activities_total]
    if flight_cost is not None:
        total_components.append(flight_cost)

    total_estimated = round(sum(total_components), 2)
    is_within = total_estimated <= user_budget
    overrun = round(max(0.0, total_estimated - user_budget), 2)

    if not is_within:
        notes.append(f"WARNING: Estimated total expenses exceed specified budget by {overrun:.2f} {currency}.")
    else:
        savings = user_budget - total_estimated
        notes.append(f"Estimated budget buffer remaining: {savings:.2f} {currency}.")

    logger.info(
        "Deterministic budget computed: user_budget=%.2f %s, total_est=%.2f, within=%s",
        user_budget,
        currency,
        total_estimated,
        is_within,
    )

    return BudgetBreakdown(
        user_budget=user_budget,
        currency=currency,
        flight_estimate=flight_cost,
        hotel_estimate=hotel_cost,
        food_estimate=food_total,
        transport_estimate=transport_total,
        activities_estimate=activities_total,
        total_estimated_cost=total_estimated,
        is_within_budget=is_within,
        overrun_amount=overrun,
        calculation_notes=notes,
    )

