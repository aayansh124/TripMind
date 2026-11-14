"""Travel service coordinating plan generation, persistence, and chat interactions."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.api.schemas.chat import ChatRequest, ChatResponse
from backend.api.schemas.travel import (
    AgentStatus,
    TravelPlan,
    TravelRequest,
    TravelResponse,
)
from backend.utils.exceptions import ResourceNotFoundError, ValidationError
from backend.utils.logger import logger
from backend.utils.validators import validate_travel_dates

# In-memory storage fallback when PostgreSQL is not connected
_in_memory_trips: Dict[str, Dict[str, Any]] = {}


class TravelService:
    """Service layer for travel plan generation and conversational follow-ups."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    async def create_travel_plan(self, request: TravelRequest) -> TravelResponse:
        """Process travel request, execute LangGraph multi-agent workflow, and persist result."""
        # 1. Validate dates and input
        dep_date, ret_date, duration_days = validate_travel_dates(
            request.departure_date, request.return_date
        )

        trip_id = str(uuid.uuid4())
        thread_id = f"trip_{trip_id}"
        logger.info(
            "Initiating travel plan generation: trip_id=%s, origin=%s, destination=%s, duration=%d days",
            trip_id,
            request.origin,
            request.destination,
            duration_days,
        )

        # 2. Invoke LangGraph multi-agent workflow runner
        from backend.graph.runner import run_travel_workflow

        plan, execution_status, errors = await run_travel_workflow(
            trip_id=trip_id,
            thread_id=thread_id,
            request=request,
            duration_days=duration_days,
        )

        # 3. Persist trip to database if available, else in-memory fallback
        self._save_trip(trip_id, plan, request)

        response_status = AgentStatus.SUCCESS if plan else AgentStatus.FAILED
        if errors and plan:
            response_status = AgentStatus.PARTIAL

        return TravelResponse(
            trip_id=trip_id,
            status=response_status,
            travel_plan=plan,
            agent_execution_status=execution_status,
            errors=errors,
        )

    def get_trip(self, trip_id: str) -> TravelPlan:
        """Retrieve a specific travel plan by trip_id."""
        if self.db is not None:
            try:
                from backend.database.repositories import TripRepository
                repo = TripRepository(self.db)
                trip = repo.get_by_id(trip_id)
                if trip and trip.travel_plan_json:
                    return TravelPlan.model_validate(trip.travel_plan_json)
            except Exception as e:
                logger.warning("Database lookup failed for trip_id '%s': %s", trip_id, e)

        # In-memory fallback
        if trip_id in _in_memory_trips:
            return TravelPlan.model_validate(_in_memory_trips[trip_id])

        raise ResourceNotFoundError("Trip", trip_id)

    def get_all_trips(self) -> List[Dict[str, Any]]:
        """Retrieve all saved travel plans."""
        trips_list: List[Dict[str, Any]] = []

        if self.db is not None:
            try:
                from backend.database.repositories import TripRepository
                repo = TripRepository(self.db)
                db_trips = repo.get_all()
                for t in db_trips:
                    trips_list.append({
                        "trip_id": t.id,
                        "origin": t.origin,
                        "destination": t.destination,
                        "departure_date": t.departure_date,
                        "return_date": t.return_date,
                        "travellers": t.travellers,
                        "budget": t.budget,
                        "currency": t.currency,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                    })
                return trips_list
            except Exception as e:
                logger.warning("Database retrieval failed for trips list: %s", e)

        # In-memory fallback
        for t_id, data in _in_memory_trips.items():
            trips_list.append({
                "trip_id": t_id,
                "origin": data.get("origin"),
                "destination": data.get("destination"),
                "departure_date": data.get("departure_date"),
                "return_date": data.get("return_date"),
                "travellers": data.get("travellers"),
                "budget": data.get("budget", {}).get("amount"),
                "currency": data.get("budget", {}).get("currency"),
                "created_at": data.get("created_at"),
            })

        return trips_list

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a travel plan by ID."""
        deleted = False

        if self.db is not None:
            try:
                from backend.database.repositories import TripRepository
                repo = TripRepository(self.db)
                deleted = repo.delete(trip_id)
            except Exception as e:
                logger.warning("Database deletion failed for trip_id '%s': %s", trip_id, e)

        if trip_id in _in_memory_trips:
            del _in_memory_trips[trip_id]
            deleted = True

        if not deleted:
            raise ResourceNotFoundError("Trip", trip_id)

        return True

    async def handle_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Process a follow-up conversational query with continuity."""
        # 1. If trip_id is provided, verify trip existence
        trip_context: Optional[TravelPlan] = None
        if request.trip_id:
            try:
                trip_context = self.get_trip(request.trip_id)
            except ResourceNotFoundError:
                logger.warning("Referenced trip_id '%s' not found for chat", request.trip_id)

        # 2. Invoke chat workflow runner
        from backend.graph.runner import run_chat_turn

        reply, structured_info, sources = await run_chat_turn(
            thread_id=request.thread_id,
            user_message=request.message,
            trip_context=trip_context,
        )

        return ChatResponse(
            thread_id=request.thread_id,
            trip_id=request.trip_id,
            assistant_response=reply,
            structured_info=structured_info,
            sources=sources,
        )

    def _save_trip(self, trip_id: str, plan: Optional[TravelPlan], request: TravelRequest) -> None:
        """Internal helper to persist trip to DB or in-memory dictionary."""
        if not plan:
            return

        plan_dict = plan.model_dump()
        _in_memory_trips[trip_id] = plan_dict

        if self.db is not None:
            try:
                from backend.database.repositories import TripRepository
                repo = TripRepository(self.db)
                repo.create(
                    trip_id=trip_id,
                    origin=request.origin,
                    destination=request.destination,
                    departure_date=request.departure_date,
                    return_date=request.return_date,
                    travellers=request.travellers,
                    budget=request.budget,
                    currency=request.currency,
                    preferences=request.travel_preferences,
                    travel_plan_json=plan_dict,
                )
                logger.info("Persisted trip '%s' to PostgreSQL database.", trip_id)
            except Exception as e:
                logger.warning("Could not persist trip '%s' to database: %s", trip_id, e)

