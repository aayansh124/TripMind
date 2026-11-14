
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


# Baseline daily expenses per person, with hotel cost per room.
DAILY_STYLE_ESTIMATES = {
    TravelStyle.BUDGET: {
        "hotel": 50.0,
        "food": 25.0,
        "transport": 10.0,
        "activity": 15.0,
    },
    TravelStyle.STANDARD: {
        "hotel": 120.0,
        "food": 55.0,
        "transport": 20.0,
        "activity": 35.0,
    },
    TravelStyle.LUXURY: {
        "hotel": 350.0,
        "food": 150.0,
        "transport": 70.0,
        "activity": 100.0,
    },
    TravelStyle.ADVENTURE: {
        "hotel": 80.0,
        "food": 35.0,
        "transport": 25.0,
        "activity": 60.0,
    },
    TravelStyle.FAMILY: {
        "hotel": 160.0,
        "food": 60.0,
        "transport": 30.0,
        "activity": 40.0,
    },
    TravelStyle.ROMANTIC: {
        "hotel": 200.0,
        "food": 90.0,
        "transport": 35.0,
        "activity": 60.0,
    },
    TravelStyle.CULTURAL: {
        "hotel": 110.0,
        "food": 50.0,
        "transport": 20.0,
        "activity": 45.0,
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
    """Calculate estimated trip expenses and compare them with the user budget."""

    if user_budget <= 0:
        raise ValueError("User budget must be greater than zero.")

    if duration_days <= 0:
        raise ValueError("Trip duration must be greater than zero.")

    if travellers <= 0:
        raise ValueError("Number of travellers must be greater than zero.")

    notes: list[str] = []

    nights = max(1, duration_days - 1)
    rooms = max(1, math.ceil(travellers / 2))

    style_defaults = DAILY_STYLE_ESTIMATES.get(
        travel_style,
        DAILY_STYLE_ESTIMATES[TravelStyle.STANDARD],
    )

    # Calculate flight expenses using verified prices only.
    flight_cost = None

    verified_flights = [
        flight
        for flight in (flights or [])
        if (
            flight.price is not None
            and flight.price > 0
            and flight.is_verified_price
            and flight.currency
            and flight.currency.upper() == currency.upper()
        )
    ]

    if verified_flights:
        average_flight_price = (
            sum(flight.price for flight in verified_flights)
            / len(verified_flights)
        )

        flight_cost = round(
            average_flight_price * travellers,
            2,
        )

        notes.append(
            f"Flight estimate uses {len(verified_flights)} "
            f"verified flight price(s)."
        )
    else:
        notes.append(
            "No verified flight prices in the selected currency were "
            "available. Flight expenses are excluded from the total."
        )

    # Calculate accommodation expenses.
    hotel_rates = [
        hotel.estimated_price_per_night
        for hotel in (hotels or [])
        if (
            hotel.estimated_price_per_night is not None
            and hotel.estimated_price_per_night > 0
            and hotel.currency
            and hotel.currency.upper() == currency.upper()
        )
    ]

    if hotel_rates:
        average_nightly_rate = sum(hotel_rates) / len(hotel_rates)

        hotel_cost = round(
            average_nightly_rate * nights * rooms,
            2,
        )

        notes.append(
            f"Accommodation estimate: {average_nightly_rate:.2f} "
            f"{currency} per night for {rooms} room(s) "
            f"across {nights} night(s)."
        )
    else:
        hotel_cost = round(
            style_defaults["hotel"] * nights * rooms,
            2,
        )

        notes.append(
            f"Accommodation estimate uses the {travel_style.value} "
            f"baseline of {style_defaults['hotel']:.2f} "
            f"{currency} per room per night."
        )

    # Calculate food, transport, and activity expenses.
    food_total = 0.0
    transport_total = 0.0
    activities_total = 0.0

    if itinerary_days:
        food_total = sum(
            day.estimated_food_cost for day in itinerary_days
        )

        transport_total = sum(
            day.estimated_transport_cost for day in itinerary_days
        )

        activities_total = sum(
            day.estimated_activity_cost for day in itinerary_days
        )

    # Apply baseline estimates when itinerary costs are unavailable.
    if food_total == 0:
        food_total = (
            style_defaults["food"] * duration_days * travellers
        )

    if transport_total == 0:
        transport_total = (
            style_defaults["transport"] * duration_days * travellers
        )

    if activities_total == 0:
        activities_total = (
            style_defaults["activity"] * duration_days * travellers
        )

    food_total = round(food_total, 2)
    transport_total = round(transport_total, 2)
    activities_total = round(activities_total, 2)

    notes.extend(
        [
            f"Food estimate: {food_total:.2f} {currency}.",
            f"Local transport estimate: {transport_total:.2f} {currency}.",
            f"Activities estimate: {activities_total:.2f} {currency}.",
        ]
    )

    # Calculate the total estimated trip cost.
    total_components = [
        hotel_cost,
        food_total,
        transport_total,
        activities_total,
    ]

    if flight_cost is not None:
        total_components.append(flight_cost)

    total_estimated = round(sum(total_components), 2)

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
            f"Estimated budget remaining: {remaining_budget:.2f} {currency}."
        )
    else:
        notes.append(
            f"Estimated expenses exceed the budget by "
            f"{overrun_amount:.2f} {currency}."
        )

    logger.info(
        "Budget calculated: allocated=%.2f %s, estimated=%.2f, within_budget=%s",
        user_budget,
        currency,
        total_estimated,
        is_within_budget,
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
        is_within_budget=is_within_budget,
        overrun_amount=overrun_amount,
        calculation_notes=notes,
    )
