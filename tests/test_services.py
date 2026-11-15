
"""Unit tests for deterministic budget calculation and currency safety."""

from backend.api.schemas.travel import (
    DailyItinerary,
    FlightInformation,
    HotelInformation,
    TravelStyle,
)
from backend.services.budget_service import calculate_budget_breakdown


def test_inr_fallback_estimates():
    """Verify INR fallback estimates are applied without inventing flight costs."""

    breakdown = calculate_budget_breakdown(
        user_budget=30000.0,
        currency="INR",
        duration_days=2,
        travellers=2,
        travel_style=TravelStyle.STANDARD,
    )

    assert breakdown.hotel_estimate == 3500.0
    assert breakdown.food_estimate == 4000.0
    assert breakdown.transport_estimate == 2800.0
    assert breakdown.activities_estimate == 2800.0

    # No verified flight price was supplied.
    assert breakdown.flight_estimate is None
    assert breakdown.comparison_available is False
    assert breakdown.is_within_budget is None
    assert breakdown.overrun_amount is None


def test_usd_does_not_use_inr_fallbacks():
    """Verify foreign currency estimates never use INR fallback values."""

    breakdown = calculate_budget_breakdown(
        user_budget=5000.0,
        currency="USD",
        duration_days=5,
        travellers=2,
        travel_style=TravelStyle.STANDARD,
    )

    assert breakdown.currency == "USD"
    assert breakdown.flight_estimate is None
    assert breakdown.hotel_estimate is None
    assert breakdown.food_estimate is None
    assert breakdown.transport_estimate is None
    assert breakdown.activities_estimate is None

    assert breakdown.total_estimated_cost == 0.0
    assert breakdown.comparison_available is False
    assert breakdown.is_within_budget is None
    assert breakdown.overrun_amount is None


def test_complete_budget_with_verified_prices():
    """Verify complete matching-currency expenses allow budget comparison."""

    hotel = HotelInformation(
        hotel_name="Test Hotel",
        location="Goa, India",
        description="Test accommodation",
        estimated_price_per_night=3000.0,
        currency="INR",
    )

    itinerary = [
        DailyItinerary(
            day=1,
            estimated_food_cost=1000.0,
            estimated_transport_cost=500.0,
            estimated_activity_cost=500.0,
        )
    ]

    flights = [
        FlightInformation(
            airline="Test Airline",
            price=2000.0,
            currency="INR",
            is_verified_price=True,
        )
    ]

    breakdown = calculate_budget_breakdown(
        user_budget=10000.0,
        currency="INR",
        duration_days=2,
        travellers=2,
        travel_style=TravelStyle.STANDARD,
        hotels=[hotel],
        itinerary_days=itinerary,
        flights=flights,
    )

    # Hotel: 3000 x 1 night x 1 room = 3000
    # Flight: 2000 x 2 travellers = 4000
    # Itinerary: 1000 + 500 + 500 = 2000
    # Total: 9000 INR
    assert breakdown.hotel_estimate == 3000.0
    assert breakdown.flight_estimate == 4000.0
    assert breakdown.food_estimate == 1000.0
    assert breakdown.transport_estimate == 500.0
    assert breakdown.activities_estimate == 500.0

    assert breakdown.total_estimated_cost == 9000.0
    assert breakdown.comparison_available is True
    assert breakdown.is_within_budget is True
    assert breakdown.overrun_amount == 0.0


def test_budget_overrun_with_complete_costs():
    """Verify overrun is calculated only when all expense categories are available."""

    hotel = HotelInformation(
        hotel_name="Test Hotel",
        location="Goa, India",
        description="Test accommodation",
        estimated_price_per_night=3000.0,
        currency="INR",
    )

    itinerary = [
        DailyItinerary(
            day=1,
            estimated_food_cost=1000.0,
            estimated_transport_cost=500.0,
            estimated_activity_cost=500.0,
        )
    ]

    flights = [
        FlightInformation(
            airline="Test Airline",
            price=2000.0,
            currency="INR",
            is_verified_price=True,
        )
    ]

    breakdown = calculate_budget_breakdown(
        user_budget=8000.0,
        currency="INR",
        duration_days=2,
        travellers=2,
        travel_style=TravelStyle.STANDARD,
        hotels=[hotel],
        itinerary_days=itinerary,
        flights=flights,
    )

    assert breakdown.comparison_available is True
    assert breakdown.total_estimated_cost == 9000.0
    assert breakdown.is_within_budget is False
    assert breakdown.overrun_amount == 1000.0


def test_custom_hotel_and_itinerary_costs():
    """Verify supplied hotel and itinerary costs are used."""

    hotel = HotelInformation(
        hotel_name="Grand Parisian Hotel",
        location="Paris, France",
        description="Luxury boutique hotel",
        estimated_price_per_night=250.0,
        currency="USD",
    )

    itinerary = [
        DailyItinerary(
            day=1,
            morning=["Louvre Tour"],
            afternoon=["Cafe lunch"],
            evening=["Seine Cruise"],
            estimated_transport_cost=20.0,
            estimated_food_cost=60.0,
            estimated_activity_cost=50.0,
            daily_total=130.0,
        )
    ]

    breakdown = calculate_budget_breakdown(
        user_budget=3000.0,
        currency="USD",
        duration_days=3,
        travellers=1,
        travel_style=TravelStyle.STANDARD,
        hotels=[hotel],
        itinerary_days=itinerary,
    )

    assert breakdown.hotel_estimate == 500.0
    assert breakdown.food_estimate == 60.0
    assert breakdown.transport_estimate == 20.0
    assert breakdown.activities_estimate == 50.0

    # Flight cost is missing, so the full comparison remains incomplete.
    assert breakdown.flight_estimate is None
    assert breakdown.comparison_available is False
    assert breakdown.is_within_budget is None
