"""Unit tests for deterministic budget service and business logic."""

import pytest
from backend.api.schemas.travel import (
    DailyItinerary,
    HotelInformation,
    TravelStyle,
)
from backend.services.budget_service import calculate_budget_breakdown


def test_budget_within_limit():
    """Verify budget calculation succeeds and flags within budget when total is below limit."""
    budget = 5000.0
    currency = "USD"
    duration = 5
    travellers = 2

    breakdown = calculate_budget_breakdown(
        user_budget=budget,
        currency=currency,
        duration_days=duration,
        travellers=travellers,
        travel_style=TravelStyle.STANDARD,
    )

    assert breakdown.user_budget == 5000.0
    assert breakdown.currency == "USD"
    assert breakdown.total_estimated_cost > 0
    assert breakdown.is_within_budget is True
    assert breakdown.overrun_amount == 0.0
    assert len(breakdown.calculation_notes) > 0


def test_budget_overrun_detection():
    """Verify that small budget correctly triggers overrun flag and calculates exact difference."""
    user_budget = 100.0  # Unrealistically low for 7 days luxury travel
    currency = "EUR"
    duration = 7
    travellers = 2

    breakdown = calculate_budget_breakdown(
        user_budget=user_budget,
        currency=currency,
        duration_days=duration,
        travellers=travellers,
        travel_style=TravelStyle.LUXURY,
    )

    assert breakdown.is_within_budget is False
    assert breakdown.overrun_amount > 0.0
    expected_overrun = round(breakdown.total_estimated_cost - user_budget, 2)
    assert breakdown.overrun_amount == expected_overrun
    assert any("WARNING" in note for note in breakdown.calculation_notes)


def test_budget_with_custom_hotel_and_itinerary():
    """Verify budget calculations correctly incorporate explicit hotel nightly rates and itinerary items."""
    hotel = HotelInformation(
        hotel_name="Grand Parisian Hotel",
        location="Paris, France",
        description="Luxury boutique hotel",
        estimated_price_per_night=250.0,
        currency="USD",
    )

    day1 = DailyItinerary(
        day=1,
        morning=["Louvre Tour"],
        afternoon=["Café lunch"],
        evening=["Seine Cruise"],
        estimated_transport_cost=20.0,
        estimated_food_cost=60.0,
        estimated_activity_cost=50.0,
        daily_total=130.0,
    )

    breakdown = calculate_budget_breakdown(
        user_budget=3000.0,
        currency="USD",
        duration_days=3,
        travellers=1,
        travel_style=TravelStyle.STANDARD,
        hotels=[hotel],
        itinerary_days=[day1],
    )

    # 3 days = 2 nights * $250 = $500 lodging
    assert breakdown.hotel_estimate == 500.0
def test_recommendation_service_ranking():
    """Verify that attractions are prioritized based on travel style keywords."""
    from backend.services.recommendation_service import RecommendationService

    attractions = [
        "Modern Shopping Mall",
        "Ancient Historic Palace",
        "Theme Amusement Park",
        "Fine Art Museum",
    ]

    ranked = RecommendationService.rank_attractions_by_style(
        attractions=attractions,
        travel_style=TravelStyle.CULTURAL,
    )

    # Cultural items ("Palace", "Museum") should be ranked first
    assert "Palace" in ranked[0] or "Museum" in ranked[0]
    assert "Palace" in ranked[1] or "Museum" in ranked[1]
