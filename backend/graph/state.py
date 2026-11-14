
"""Define shared LangGraph state and reducer functions."""

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage


def merge_dicts(
    existing: dict[str, Any],
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Merge dictionary updates while preserving existing entries."""

    merged = dict(existing) if existing else {}

    if updates:
        merged.update(updates)

    return merged


class TravelState(TypedDict, total=False):
    """Shared state for travel planning and conversational workflows."""

    # Conversation identifiers and messages
    messages: Annotated[list[AnyMessage], operator.add]
    thread_id: str
    trip_id: str

    # Travel request information
    origin: str
    destination: str
    departure_date: str
    return_date: str
    duration_days: int
    travellers: int
    budget: float
    currency: str
    travel_style: str
    travel_preferences: str | None
    accommodation_preference: str | None

    # Specialist agent outputs
    destination_results: dict[str, Any] | None
    flight_results: dict[str, Any] | None
    hotel_results: dict[str, Any] | None
    weather_results: dict[str, Any] | None
    itinerary_results: dict[str, Any] | None

    # Consolidated travel plan
    final_plan: dict[str, Any] | None

    # Workflow errors and execution status
    errors: Annotated[list[str], operator.add]
    execution_status: Annotated[dict[str, str], merge_dicts]
