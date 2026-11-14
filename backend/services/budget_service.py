
"""Deterministic budget calculation and reconciliation service."""

import math

from backend.api.schemas.travel import (
    BudgetBreakdown,
    DailyItinerary,
    FlightInformation,
    HotelInformation,
    TravelStyle,
)
from backend.utils.logger import logger


# Approximate INR fallback estimates for domestic Indian travel.
# Hotel cost is per room per night; other costs are per person per day.
DAILY_STYLE_ESTIMATES = {
    TravelStyle.BUDGET: {
        "hotel": 1500.0,
        "food": 500.0,
        "transport": 300.0,
        "activity": 300.0,
    },
    TravelStyle.STANDARD: {
        "hotel": 3500.0,
        "food": 1000.0,
        "transport": 700.0,
        "activity": 700.0,
    },
    TravelStyle.LUXURY: {
        "hotel": 10000.0,
        "food": 2500.0,
        "transport": 1800.0,
        "activity": 2500.0,
    },
    TravelStyle.ADVENTURE: {
        "hotel": 2500.0,
        "food": 700.0,
        "transport": 600.0,
        "activity": 1200.0,
    },
    TravelStyle.FAMILY: {
        "hotel": 4500.0,
        "food": 1200.0,
        "transport": 900.0,
        "activity": 1000.0,
    },
    TravelStyle.ROMANTIC: {
        "hotel": 6000.0,
        "food": 1500.0,
        "transport": 800.0,
        "activity": 1200.0,
    },
    TravelStyle.CULTURAL: {
        "hotel": 3000.0,
        "food": 900.0,
        "transport": 500.0,
        "activity": 900.0,
    },
}


def calculate_budget_breakdown(
    user_budget: float,
    currency: str,
    duration_days: int,
    travellers: int,
    travel_style: TravelStyle,
    hotels: list[HotelInformation] | None = None,
    itinerary_days: list[DailyItinerary] | None = None,
    flights: list[FlightInformation] | None = None,
) -> BudgetBreakdown:
    """Calculate trip expenses without mixing different currencies."""

    if user_budget <= 0:
        raise ValueError("User budget must be greater than zero.")

    if duration_days <= 0:
        raise ValueError("Trip duration must be greater than zero.")

    if travellers <= 0:
        raise ValueError("Number of travellers must be greater than zero.")

    currency = currency.strip().upper()
    use_inr_fallbacks = currency == "INR"
    notes: list[str] = []

    nights = max(1, duration_days - 1)
    rooms = max(1, math.ceil(travellers / 2))

    style_defaults = DAILY_STYLE_ESTIMATES.get(
        travel_style,
        DAILY_STYLE_ESTIMATES[TravelStyle.STANDARD],
    )

    # Include verified flight prices in the requested currency only.
    verified_flights = [
        flight
        for flight in (flights or [])
        if (
            flight.price is not None
            and flight.price > 0
            and flight.is_verified_price
            and flight.currency
            and flight.currency.strip().upper() == currency
        )
    ]

    flight_cost = None

    if verified_flights:
        average_flight_price = (
            sum(flight.price for flight in verified_flights)
            / len(verified_flights)
        )
        flight_cost = round(average_flight_price * travellers, 2)

        notes.append(
            f"Flight estimate uses {len(verified_flights)} "
            f"verified flight price(s)."
        )
    else:
        notes.append(
            f"No verified flight prices in {currency} were available. "
            "Flight expenses are excluded from the estimate."
        )

    # Calculate accommodation using matching-currency prices.
    hotel_rates = [
        hotel.estimated_price_per_night
        for hotel in (hotels or [])
        if (
            hotel.estimated_price_per_night is not None
            and hotel.estimated_price_per_night > 0
            and hotel.currency
            and hotel.currency.strip().upper() == currency
        )
    ]

    if hotel_rates:
        average_nightly_rate = sum(hotel_rates) / len(hotel_rates)
        hotel_cost = round(average_nightly_rate * nights * rooms, 2)

        notes.append(
            f"Accommodation estimate: {average_nightly_rate:.2f} "
            f"{currency} per room per night for {rooms} room(s) "
            f"across {nights} night(s)."
        )
    elif use_inr_fallbacks:
        hotel_cost = round(
            style_defaults["hotel"] * nights * rooms,
            2,
        )

        notes.append(
            f"Accommodation uses the approximate {travel_style.value} "
            f"INR baseline of {style_defaults['hotel']:.2f} "
            "per room per night."
        )
    else:
        hotel_cost = None
        notes.append(
            f"No matching-currency accommodation prices were available "
            f"for {currency}. No INR fallback was applied."
        )

    # Read itinerary expenses when available.
    food_total = None
    transport_total = None
    activities_total = None

    if itinerary_days:
        food_value = sum(
            day.estimated_food_cost for day in itinerary_days
        )
        transport_value = sum(
            day.estimated_transport_cost for day in itinerary_days
        )
        activities_value = sum(
            day.estimated_activity_cost for day in itinerary_days
        )

        if food_value > 0:
            food_total = round(food_value, 2)

        if transport_value > 0:
            transport_total = round(transport_value, 2)

        if activities_value > 0:
            activities_total = round(activities_value, 2)

    # Apply INR fallbacks only when itinerary costs are unavailable.
    if use_inr_fallbacks:
        if food_total is None:
            food_total = round(
                style_defaults["food"] * duration_days * travellers,
                2,
            )
            notes.append("Food cost uses an approximate INR baseline.")

        if transport_total is None:
            transport_total = round(
                style_defaults["transport"] * duration_days * travellers,
                2,
            )
            notes.append(
                "Local transport cost uses an approximate INR baseline."
            )

        if activities_total is None:
            activities_total = round(
                style_defaults["activity"] * duration_days * travellers,
                2,
            )
            notes.append(
                "Activity cost uses an approximate INR baseline."
            )

    if food_total is None:
        notes.append(f"Food estimate is unavailable in {currency}.")
    else:
        notes.append(f"Food estimate: {food_total:.2f} {currency}.")

    if transport_total is None:
        notes.append(f"Transport estimate is unavailable in {currency}.")
    else:
        notes.append(
            f"Local transport estimate: {transport_total:.2f} {currency}."
        )

    if activities_total is None:
        notes.append(f"Activity estimate is unavailable in {currency}.")
    else:
        notes.append(
            f"Activities estimate: {activities_total:.2f} {currency}."
        )

    # Sum only known expenses; mark the comparison incomplete if any
    # required expense category is unavailable.
    expense_components = [
        hotel_cost,
        food_total,
        transport_total,
        activities_total,
        flight_cost,
    ]

    comparison_available = all(
        component is not None for component in expense_components
    )

    total_estimated = round(
        sum(
            component
            for component in expense_components
            if component is not None
        ),
        2,
    )

    if comparison_available:
        is_within_budget = total_estimated <= user_budget
        overrun_amount = round(
            max(0.0, total_estimated - user_budget),
            2,
        )

        if is_within_budget:
            remaining_budget = round(
                user_budget - total_estimated,
                2,
            )
            notes.append(
                f"Estimated budget remaining: {remaining_budget:.2f} "
                f"{currency}."
            )
        else:
            notes.append(
                f"Estimated expenses exceed the budget by "
                f"{overrun_amount:.2f} {currency}."
            )
    else:
        is_within_budget = None
        overrun_amount = None
        notes.append(
            "Budget comparison is incomplete because one or more "
            "expense categories are unavailable."
        )

    logger.info(
        "Budget calculated: allocated=%.2f %s, estimated=%.2f, "
        "comparison_available=%s",
        user_budget,
        currency,
        total_estimated,
        comparison_available,
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
        comparison_available=comparison_available,
        is_within_budget=is_within_budget,
        overrun_amount=overrun_amount,
        calculation_notes=notes,
    )
