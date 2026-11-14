
"""Pydantic schemas for travel requests, agent results, and travel plans."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class TravelStyle(str, Enum):
    """Supported travel styles."""

    BUDGET = "Budget"
    STANDARD = "Standard"
    LUXURY = "Luxury"
    ADVENTURE = "Adventure"
    FAMILY = "Family"
    ROMANTIC = "Romantic"
    CULTURAL = "Cultural"


class AgentStatus(str, Enum):
    """Execution status for individual agents and workflows."""

    SUCCESS = "success"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class DestinationOverview(BaseModel):
    """Detailed destination overview and attraction recommendations."""

    overview: str = Field(..., description="High-level summary of the destination.")
    highlights: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    cultural_tips: list[str] = Field(default_factory=list)
    potential_constraints: list[str] = Field(default_factory=list)


class DestinationResult(BaseModel):
    """Structured response from the destination agent."""

    status: AgentStatus = AgentStatus.SUCCESS
    data: DestinationOverview | None = None
    source: list[str] = Field(default_factory=lambda: ["Gemini", "Tavily Search"])
    error: str | None = None
    retrieved_at: str = Field(default_factory=utc_now_iso)


class FlightInformation(BaseModel):
    """Structured flight detail."""

    airline: str | None = None
    flight_number: str | None = None
    departure_airport: str | None = None
    arrival_airport: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    flight_status: str | None = None
    price: float | None = None
    currency: str | None = None
    is_verified_price: bool = False
    source: str = "AviationStack API"
    note: str | None = None


class FlightResult(BaseModel):
    """Structured response from the flight agent."""

    status: AgentStatus = AgentStatus.SUCCESS
    data: list[FlightInformation] = Field(default_factory=list)
    source: str = "AviationStack API"
    error: str | None = None
    limitations: str | None = None
    retrieved_at: str = Field(default_factory=utc_now_iso)


class HotelInformation(BaseModel):
    """Structured hotel recommendation."""

    hotel_name: str
    location: str
    description: str
    estimated_price_per_night: float | None = None
    currency: str | None = "USD"
    rating: float | None = None
    website: str | None = None
    source_url: str | None = None
    is_verified_availability: bool = False


class HotelResult(BaseModel):
    """Structured response from the hotel agent."""

    status: AgentStatus = AgentStatus.SUCCESS
    data: list[HotelInformation] = Field(default_factory=list)
    source: str = "Tavily Search / Web Discovery"
    error: str | None = None
    limitations: str | None = None
    disclaimer: str = (
        "Hotel recommendations are sourced from web discovery and do not "
        "represent guaranteed real-time inventory or final booking rates."
    )
    retrieved_at: str = Field(default_factory=utc_now_iso)


class WeatherInformation(BaseModel):
    """Structured weather report for a destination."""

    temperature_celsius: float | None = None
    condition: str | None = None
    humidity: int | None = None
    wind_speed_mps: float | None = None
    forecast_summary: str | None = None
    forecast_available: bool = False
    considerations: list[str] = Field(default_factory=list)
    source: str = "OpenWeather API"


class WeatherResult(BaseModel):
    """Structured response from the weather agent."""

    status: AgentStatus = AgentStatus.SUCCESS
    data: WeatherInformation | None = None
    source: str = "OpenWeather API"
    error: str | None = None
    retrieved_at: str = Field(default_factory=utc_now_iso)


class DailyItinerary(BaseModel):
    """Detailed plan for a single travel day."""

    day: int
    date: str | None = None
    morning: list[str] = Field(default_factory=list)
    afternoon: list[str] = Field(default_factory=list)
    evening: list[str] = Field(default_factory=list)
    places_to_visit: list[str] = Field(default_factory=list)
    estimated_transport_cost: float = 0.0
    estimated_food_cost: float = 0.0
    estimated_activity_cost: float = 0.0
    daily_total: float = 0.0


class ItineraryResult(BaseModel):
    """Structured response from the itinerary agent."""

    status: AgentStatus = AgentStatus.SUCCESS
    data: list[DailyItinerary] = Field(default_factory=list)
    source: str = "Gemini Itinerary Synthesis"
    error: str | None = None
    retrieved_at: str = Field(default_factory=utc_now_iso)


class BudgetBreakdown(BaseModel):
    """Budget calculation and comparison against the user's budget."""

    user_budget: float
    currency: str = "INR"
    flight_estimate: float | None = None
    hotel_estimate: float | None = None
    food_estimate: float | None = None
    transport_estimate: float | None = None
    activities_estimate: float | None = None
    total_estimated_cost: float = 0.0
    comparison_available: bool = True
    is_within_budget: bool | None = True
    overrun_amount: float | None = 0.0
    calculation_notes: list[str] = Field(default_factory=list)


class TravelRequest(BaseModel):
    """User input for generating a travel plan."""

    origin: str = Field(..., min_length=2, max_length=100)
    destination: str = Field(..., min_length=2, max_length=100)
    departure_date: str
    return_date: str
    travellers: int = Field(1, ge=1, le=50)
    budget: float = Field(..., gt=0)
    currency: str = Field("INR", min_length=3, max_length=3)
    travel_preferences: str | None = Field(None, max_length=500)
    accommodation_preference: str | None = Field(None, max_length=200)
    travel_style: TravelStyle = TravelStyle.STANDARD

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize the currency code to uppercase."""
        return value.strip().upper()


class TravelPlan(BaseModel):
    """Complete travel plan generated by the multi-agent system."""

    trip_id: str
    origin: str
    destination: str
    departure_date: str
    return_date: str
    duration_days: int
    travellers: int
    budget: dict[str, Any]
    travel_style: str
    destination_overview: DestinationOverview
    flights: list[FlightInformation] = Field(default_factory=list)
    hotels: list[HotelInformation] = Field(default_factory=list)
    weather: WeatherInformation | None = None
    itinerary: list[DailyItinerary] = Field(default_factory=list)
    budget_breakdown: BudgetBreakdown
    travel_tips: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    execution_status: AgentStatus = AgentStatus.SUCCESS
    created_at: str = Field(default_factory=utc_now_iso)


class TravelResponse(BaseModel):
    """API response for travel planning requests."""

    trip_id: str
    status: AgentStatus
    travel_plan: TravelPlan | None = None
    agent_execution_status: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
