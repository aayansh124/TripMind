"""LangGraph state definition and reducer annotations."""

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from langchain_core.messages import AnyMessage


def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer to merge dictionary state updates safely across parallel nodes."""
    res = dict(a) if a else {}
    if b:
        res.update(b)
    return res


class TravelState(TypedDict, total=False):
    """Shared state for multi-agent travel planning and chat interactions."""

    # Thread and conversation identifiers
    messages: Annotated[List[AnyMessage], operator.add]
    thread_id: str
    trip_id: str

    # Core Travel Parameters
    origin: str
    destination: str
    departure_date: str
    return_date: str
    duration_days: int
    travellers: int
    budget: float
    currency: str
    travel_style: str
    travel_preferences: Optional[str]
    accommodation_preference: Optional[str]

    # Specialist Agent Outputs (Independently owned fields for parallel safety)
    destination_results: Optional[Dict[str, Any]]
    flight_results: Optional[Dict[str, Any]]
    hotel_results: Optional[Dict[str, Any]]
    weather_results: Optional[Dict[str, Any]]
    itinerary_results: Optional[Dict[str, Any]]

    # Consolidated Travel Plan
    final_plan: Optional[Dict[str, Any]]

    # Observability and Error Tracking
    errors: Annotated[List[str], operator.add]
    execution_status: Annotated[Dict[str, str], merge_dicts]

