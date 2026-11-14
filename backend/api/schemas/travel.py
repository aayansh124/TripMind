"""Pydantic schemas for Travel Planning requests, agent results, and travel plans."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


def utc_now_iso() -> str:
    """Return ISO format string of current UTC time."""
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


# --- Specialist Agent Output Models ---

class DestinationOverview(BaseModel):
    """Detailed destination overview and attraction recommendations."""
    overview: str = Field(..., description="High-level summary of the destination.")
    highlights: List[str] = Field(default_factory=list, description="Top attractions and key highlights.")
    activities: List[str] = Field(default_factory=list, description="Recommended activities based on travel style.")
    cultural_tips: List[str] = Field(default_factory=list, description="Local customs, etiquette, and tips.")
    potential_constraints: List[str] = Field(default_factory=list, description="Seasonal constraints, travel advisories.")


class DestinationResult(BaseModel):
    """Structured response from Destination Agent."""
    status: AgentStatus = AgentStatus.SUCCESS
    data: Optional[DestinationOverview] = None
    source: List[str] = Field(default_factory=lambda: ["Gemini", "Tavily Search"])
    error: Optional[str] = None
    retrieved_at: str = Field(default_factory=utc_now_iso)


class FlightInformation(BaseModel):
    """Structured flight detail item."""
    airline: Optional[str] = Field(None, description="Airline name.")
    flight_number: Optional[str] = Field(None, description="Flight number code.")
    departure_airport: Optional[str] = Field(None, description="Origin airport code or name.")
    arrival_airport: Optional[str] = Field(None, description="Destination airport code or name.")
    departure_time: Optional[str] = Field(None, description="Scheduled departure time.")
    arrival_time: Optional[str] = Field(None, description="Scheduled arrival time.")
    flight_status: Optional[str] = Field(None, description="Scheduled / Active / Landed status.")
    price: Optional[float] = Field(None, description="Verified price if available; null otherwise.")
    currency: Optional[str] = Field(None, description="Price currency if verified.")
    is_verified_price: bool = Field(False, description="Whether price was confirmed by official booking source.")
    source: str = Field("AviationStack API", description="Data provider.")
    note: Optional[str] = Field(None, description="Notes regarding schedule or booking.")


class FlightResult(BaseModel):
    """Structured response from Flight Agent."""
    status: AgentStatus = AgentStatus.SUCCESS
    data: List[FlightInformation] = Field(default_factory=list)
    source: str = "AviationStack API"
    error: Optional[str] = None
    limitations: Optional[str] = Field(
        None,
        description="Explicit notice regarding live prices or timetable coverage."
    )
    retrieved_at: str = Field(default_factory=utc_now_iso)


class HotelInformation(BaseModel):
    """Structured hotel recommendation."""
    hotel_name: str = Field(..., description="Hotel or accommodation property name.")
    location: str = Field(..., description="Area, neighborhood, or city address.")
    description: str = Field(..., description="Overview of amenities and appeal.")
    estimated_price_per_night: Optional[float] = Field(None, description="Sourced price estimate per night.")
    currency: Optional[str] = Field("USD", description="Currency of price estimate.")
    rating: Optional[float] = Field(None, description="User or star rating if sourced.")
    website: Optional[str] = Field(None, description="Official or booking website link.")
    source_url: Optional[str] = Field(None, description="Reference URL where discovered.")
    is_verified_availability: bool = Field(False, description="Always False for web discovery results.")


class HotelResult(BaseModel):
    """Structured response from Hotel Agent."""
    status: AgentStatus = AgentStatus.SUCCESS
    data: List[HotelInformation] = Field(default_factory=list)
    source: str = "Tavily Search / Web Discovery"
    error: Optional[str] = None
    disclaimer: str = Field(
        "Hotel recommendations are sourced from web discovery and do not represent guaranteed real-time inventory or final booking rates.",
        description="Booking inventory disclaimer."
    )
    retrieved_at: str = Field(default_factory=utc_now_iso)


class WeatherInformation(BaseModel):
    """Structured weather report for destination."""
    temperature_celsius: Optional[float] = Field(None, description="Current or forecast temperature in Celsius.")
    condition: Optional[str] = Field(None, description="Weather description (e.g. Sunny, Rain).")
    humidity: Optional[int] = Field(None, description="Relative humidity percentage.")
    wind_speed_mps: Optional[float] = Field(None, description="Wind speed in meters per second.")
    forecast_summary: Optional[str] = Field(None, description="Forecast breakdown for travel dates.")
    forecast_available: bool = Field(False, description="Whether travel dates fall inside API forecast horizon.")
    considerations: List[str] = Field(default_factory=list, description="Weather-specific packing/travel tips.")
    source: str = Field("OpenWeather API", description="Weather data provider.")


class WeatherResult(BaseModel):
    """Structured response from Weather Agent."""
    status: AgentStatus = AgentStatus.SUCCESS
    data: Optional[WeatherInformation] = None
    source: str = "OpenWeather API"
    error: Optional[str] = None
    retrieved_at: str = Field(default_factory=utc_now_iso)


class DailyItinerary(BaseModel):
    """Detailed plan for a single travel day."""
    day: int = Field(..., description="Day number (1, 2, ...).")
    date: Optional[str] = Field(None, description="Calendar date YYYY-MM-DD.")
    morning: List[str] = Field(default_factory=list, description="Morning activities and visits.")
    afternoon: List[str] = Field(default_factory=list, description="Afternoon activities and meals.")
    evening: List[str] = Field(default_factory=list, description="Evening activities and nightlife.")
    places_to_visit: List[str] = Field(default_factory=list, description="Key monuments, venues, or areas.")
    estimated_transport_cost: float = Field(0.0, description="Estimated local transport cost.")
    estimated_food_cost: float = Field(0.0, description="Estimated food and dining cost.")
    estimated_activity_cost: float = Field(0.0, description="Estimated entry fees and tickets.")
    daily_total: float = Field(0.0, description="Sum of daily estimated expenses.")


class ItineraryResult(BaseModel):
    """Structured response from Itinerary Agent."""
    status: AgentStatus = AgentStatus.SUCCESS
    data: List[DailyItinerary] = Field(default_factory=list)
    source: str = "Gemini Itinerary Synthesis"
    error: Optional[str] = None
    retrieved_at: str = Field(default_factory=utc_now_iso)


class BudgetBreakdown(BaseModel):
    """Deterministic budget calculation and comparison against user budget."""
    user_budget: float = Field(..., description="User's allocated total budget.")
    currency: str = Field("USD", description="Travel currency.")
    flight_estimate: Optional[float] = Field(None, description="Total flight expense estimate.")
    hotel_estimate: Optional[float] = Field(None, description="Total hotel lodging estimate.")
    food_estimate: float = Field(0.0, description="Total dining/food estimate.")
    transport_estimate: float = Field(0.0, description="Total local transport estimate.")
    activities_estimate: float = Field(0.0, description="Total attractions/activity fees estimate.")
    total_estimated_cost: float = Field(0.0, description="Sum of all estimated expenses.")
    is_within_budget: bool = Field(True, description="True if total estimated cost <= user budget.")
    overrun_amount: float = Field(0.0, description="Amount by which estimate exceeds budget, if any.")
    calculation_notes: List[str] = Field(default_factory=list, description="Explicit notes on estimation assumptions.")


# --- Request and Overall Response Schemas ---

class TravelRequest(BaseModel):
    """User input form submission for generating a travel plan."""
    origin: str = Field(..., min_length=2, max_length=100, description="Starting city or airport.")
    destination: str = Field(..., min_length=2, max_length=100, description="Destination city or country.")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format.")
    return_date: str = Field(..., description="Return date in YYYY-MM-DD format.")
    travellers: int = Field(1, ge=1, le=50, description="Number of travelers.")
    budget: float = Field(..., gt=0, description="Total allocated budget.")
    currency: str = Field("USD", min_length=3, max_length=3, description="3-letter currency code.")
    travel_preferences: Optional[str] = Field(None, max_length=500, description="Custom preferences, dietary needs, interests.")
    accommodation_preference: Optional[str] = Field(None, max_length=200, description="Hotel, Hostel, Resort, Apartment, etc.")
    travel_style: TravelStyle = Field(TravelStyle.STANDARD, description="Travel style preference.")

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        return v.strip().upper()


class TravelPlan(BaseModel):
    """Complete consolidated travel plan generated by the multi-agent system."""
    trip_id: str = Field(..., description="Unique trip identifier.")
    origin: str
    destination: str
    departure_date: str
    return_date: str
    duration_days: int
    travellers: int
    budget: Dict[str, Any]
    travel_style: str
    destination_overview: DestinationOverview
    flights: List[FlightInformation] = Field(default_factory=list)
    hotels: List[HotelInformation] = Field(default_factory=list)
    weather: Optional[WeatherInformation] = None
    itinerary: List[DailyItinerary] = Field(default_factory=list)
    budget_breakdown: BudgetBreakdown
    travel_tips: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_status: AgentStatus = AgentStatus.SUCCESS
    created_at: str = Field(default_factory=utc_now_iso)


class TravelResponse(BaseModel):
    """FastAPI response model for travel planning requests."""
    trip_id: str
    status: AgentStatus
    travel_plan: Optional[TravelPlan] = None
    agent_execution_status: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
