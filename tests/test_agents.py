"""Unit tests for specialist agents and fallback behaviors."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.destination_agent import run_destination_agent
from backend.agents.flight_agent import run_flight_agent
from backend.agents.hotel_agent import run_hotel_agent
from backend.agents.weather_agent import run_weather_agent
from backend.agents.itinerary_agent import run_itinerary_agent
from backend.agents.response_agent import run_response_agent
from backend.api.schemas.travel import (
    AgentStatus,
    DestinationOverview,
    FlightInformation,
    HotelInformation,
    TravelRequest,
    TravelStyle,
    WeatherInformation,
)


@pytest.mark.asyncio
async def test_destination_agent_fallback_on_llm_error():
    """Verify destination agent returns structured partial results when LLM fails."""
    with patch("backend.agents.destination_agent.get_structured_llm", side_effect=Exception("LLM Quota Exceeded")):
        result = await run_destination_agent(
            origin="New York",
            destination="Rome",
            departure_date="2026-07-01",
            return_date="2026-07-07",
            duration_days=7,
            travellers=2,
            travel_style="Cultural",
        )

        assert result.status == AgentStatus.PARTIAL
        assert result.data is not None
        assert "Rome" in result.data.overview
        assert len(result.data.highlights) > 0


@pytest.mark.asyncio
async def test_flight_agent_with_mocked_results():
    """Verify flight agent formats AviationStack schedules correctly without inventing prices."""
    mock_flight_data = {
        "flights": [
            {
                "airline": "British Airways",
                "flight_number": "BA117",
                "departure_airport": "JFK",
                "arrival_airport": "LHR",
                "departure_time": "2026-08-10T18:00:00",
                "arrival_time": "2026-08-11T06:00:00",
                "flight_status": "scheduled",
                "price": None,
                "is_verified_price": False,
                "note": "Scheduled flight",
            }
        ],
        "source": "AviationStack API",
        "limitations": "Live prices unsupported.",
        "error": None,
    }

    with patch("backend.agents.flight_agent.search_flights", return_value=mock_flight_data):
        result = await run_flight_agent(
            origin="JFK",
            destination="LHR",
            departure_date="2026-08-10",
            return_date="2026-08-17",
        )

        assert result.status == AgentStatus.SUCCESS
        assert len(result.data) == 1
        assert result.data[0].airline == "British Airways"
        assert result.data[0].price is None
        assert result.data[0].is_verified_price is False


@pytest.mark.asyncio
async def test_weather_agent_with_mocked_observation():
    """Verify weather agent handles current weather and generates practical packing advice."""
    mock_current = {
        "temperature_celsius": 22.5,
        "condition": "Partly Cloudy",
        "humidity": 55,
        "wind_speed_mps": 3.2,
        "city": "Tokyo",
        "source": "OpenWeather API",
    }

    with patch("backend.agents.weather_agent.get_current_weather", return_value=mock_current):
        result = await run_weather_agent(
            destination="Tokyo",
            departure_date="2026-09-01",
            return_date="2026-09-07",
        )

        assert result.status == AgentStatus.SUCCESS
        assert result.data is not None
        assert result.data.temperature_celsius == 22.5
        assert result.data.condition == "Partly Cloudy"
        assert len(result.data.considerations) > 0


@pytest.mark.asyncio
async def test_response_agent_consolidation():
    """Verify response agent aggregates all components, generates warnings, and calculates budget."""
    request = TravelRequest(
        origin="San Francisco",
        destination="Tokyo",
        departure_date="2026-10-01",
        return_date="2026-10-05",
        travellers=2,
        budget=4000.0,
        currency="USD",
        travel_style=TravelStyle.STANDARD,
    )

    plan = await run_response_agent(
        trip_id="test-trip-123",
        request=request,
        duration_days=5,
    )

    assert plan.trip_id == "test-trip-123"
    assert plan.origin == "San Francisco"
    assert plan.destination == "Tokyo"
    assert plan.duration_days == 5
    assert plan.budget_breakdown is not None
    assert plan.budget_breakdown.user_budget == 4000.0
    assert len(plan.travel_tips) > 0
    assert len(plan.sources) > 0

