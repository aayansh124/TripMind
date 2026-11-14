"""Unit and integration tests for LangGraph multi-agent workflow and checkpointing."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.api.schemas.travel import (
    AgentStatus,
    DestinationOverview,
    DestinationResult,
    FlightInformation,
    FlightResult,
    HotelInformation,
    HotelResult,
    TravelPlan,
    TravelRequest,
    TravelStyle,
    WeatherInformation,
    WeatherResult,
)
from backend.graph.runner import run_chat_turn, run_travel_workflow


@pytest.mark.asyncio
async def test_full_graph_execution_success():
    """Verify that the StateGraph executes all nodes and produces a structured TravelPlan."""
    request = TravelRequest(
        origin="Chicago",
        destination="Madrid",
        departure_date="2026-11-01",
        return_date="2026-11-06",
        travellers=2,
        budget=3500.0,
        currency="USD",
        travel_style=TravelStyle.CULTURAL,
    )

    # Mock agent calls to avoid live network requests in unit test
    mock_dest = DestinationResult(
        status=AgentStatus.SUCCESS,
        data=DestinationOverview(
            overview="Madrid is the historic capital of Spain.",
            highlights=["Prado Museum", "Royal Palace", "Retiro Park"],
            activities=["Tapas tasting in La Latina", "Flamenco show"],
            cultural_tips=["Dinner starts late, around 9:30 PM."],
            potential_constraints=["Hot midday temperatures in summer."],
        ),
        source=["Gemini"],
    )

    mock_flight = FlightResult(
        status=AgentStatus.SUCCESS,
        data=[
            FlightInformation(
                airline="Iberia",
                flight_number="IB6274",
                departure_airport="ORD",
                arrival_airport="MAD",
                departure_time="2026-11-01T16:30:00",
                arrival_time="2026-11-02T07:15:00",
                flight_status="scheduled",
                price=None,
                is_verified_price=False,
                source="AviationStack API",
            )
        ],
        source="AviationStack API",
    )

    mock_hotel = HotelResult(
        status=AgentStatus.SUCCESS,
        data=[
            HotelInformation(
                hotel_name="Hotel Palacio del Retiro",
                location="Retiro, Madrid",
                description="Boutique hotel near Prado Museum",
                estimated_price_per_night=180.0,
                currency="USD",
            )
        ],
        source="Tavily Discovery",
    )

    mock_weather = WeatherResult(
        status=AgentStatus.SUCCESS,
        data=WeatherInformation(
            temperature_celsius=18.0,
            condition="Sunny",
            humidity=50,
            wind_speed_mps=2.5,
            forecast_summary="Mild and sunny autumn days.",
            forecast_available=True,
            considerations=["Comfortable walking shoes."],
            source="OpenWeather API",
        ),
        source="OpenWeather API",
    )

    with patch("backend.agents.destination_agent.run_destination_agent", return_value=mock_dest), \
         patch("backend.agents.flight_agent.run_flight_agent", return_value=mock_flight), \
         patch("backend.agents.hotel_agent.run_hotel_agent", return_value=mock_hotel), \
         patch("backend.agents.weather_agent.run_weather_agent", return_value=mock_weather):

        plan, exec_status, errors = await run_travel_workflow(
            trip_id="test-workflow-trip",
            thread_id="test-thread-001",
            request=request,
            duration_days=6,
        )

        assert plan is not None
        assert plan.trip_id == "test-workflow-trip"
        assert plan.destination == "Madrid"
        assert plan.duration_days == 6
        assert len(plan.itinerary) > 0
        assert plan.budget_breakdown is not None
        assert "destination_agent" in exec_status
        assert "flight_agent" in exec_status
        assert "hotel_agent" in exec_status
        assert "weather_agent" in exec_status
        assert "itinerary_agent" in exec_status
        assert "response_agent" in exec_status


@pytest.mark.asyncio
async def test_workflow_partial_recovery_on_agent_failure():
    """Verify that when one agent fails, the workflow gracefully completes with partial data."""
    request = TravelRequest(
        origin="Boston",
        destination="Dublin",
        departure_date="2026-12-10",
        return_date="2026-12-15",
        travellers=1,
        budget=2000.0,
        currency="USD",
        travel_style=TravelStyle.STANDARD,
    )

    # Simulate flight agent failure by patching the function used in nodes.py
    with patch("backend.graph.nodes.run_flight_agent", side_effect=Exception("AviationStack connection timeout")):
        plan, exec_status, errors = await run_travel_workflow(
            trip_id="test-failure-trip",
            thread_id="test-thread-002",
            request=request,
            duration_days=6,
        )

        # Plan should still successfully be generated from other agents
        assert plan is not None
        assert plan.destination == "Dublin"
        assert exec_status["flight_agent"] == "failed"
        assert len(errors) > 0


@pytest.mark.asyncio
async def test_chat_turn_execution():
    """Verify conversational turn execution and continuity."""
    thread_id = "test-chat-thread-101"
    message = "What should I pack for the trip?"

    with patch("backend.graph.nodes.get_gemini_client") as mock_gemini:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(
            return_value=MagicMock(content="Pack comfortable walking shoes, light layers, and a travel adapter.")
        )
        mock_gemini.return_value = mock_instance

        reply, structured_info, sources = await run_chat_turn(
            thread_id=thread_id,
            user_message=message,
        )

        assert "Pack comfortable" in reply
