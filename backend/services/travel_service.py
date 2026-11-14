
"""Travel service coordinating plan generation, persistence, and chat."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.api.schemas.chat import ChatRequest, ChatResponse
from backend.api.schemas.travel import (
    AgentStatus,
    TravelPlan,
    TravelRequest,
    TravelResponse,
)
from backend.database.repositories import TripRepository
from backend.utils.exceptions import ResourceNotFoundError
from backend.utils.logger import logger
from backend.utils.validators import validate_travel_dates


class TravelService:
    """Coordinate travel planning, database persistence, and chat."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.trip_repository = TripRepository(db)

    async def create_travel_plan(
        self,
        request: TravelRequest,
    ) -> TravelResponse:
        """Generate a travel plan and persist it in PostgreSQL."""

        _, _, duration_days = validate_travel_dates(
            request.departure_date,
            request.return_date,
        )

        trip_id = str(uuid.uuid4())
        thread_id = f"trip_{trip_id}"

        logger.info(
            "Generating travel plan: trip_id=%s, destination=%s",
            trip_id,
            request.destination,
        )

        from backend.graph.runner import run_travel_workflow

        plan, execution_status, errors = await run_travel_workflow(
            trip_id=trip_id,
            thread_id=thread_id,
            request=request,
            duration_days=duration_days,
        )

        if plan is not None:
            self._save_trip(trip_id, plan, request)

        response_status = (
            AgentStatus.SUCCESS if plan else AgentStatus.FAILED
        )

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
        """Retrieve a saved travel plan from PostgreSQL."""

        trip = self.trip_repository.get_by_id(trip_id)

        if not trip or not trip.travel_plan_json:
            raise ResourceNotFoundError("Trip", trip_id)

        return TravelPlan.model_validate(trip.travel_plan_json)

    def get_all_trips(self) -> list[dict[str, Any]]:
        """Retrieve saved trip summaries from PostgreSQL."""

        trips = self.trip_repository.get_all()

        return [
            {
                "trip_id": trip.id,
                "origin": trip.origin,
                "destination": trip.destination,
                "departure_date": trip.departure_date,
                "return_date": trip.return_date,
                "travellers": trip.travellers,
                "budget": trip.budget,
                "currency": trip.currency,
                "created_at": (
                    trip.created_at.isoformat()
                    if trip.created_at
                    else None
                ),
            }
            for trip in trips
        ]

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a saved trip from PostgreSQL."""

        deleted = self.trip_repository.delete(trip_id)

        if not deleted:
            raise ResourceNotFoundError("Trip", trip_id)

        return True

    async def handle_chat_message(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """Process a conversational query with optional trip context."""

        trip_context = None

        if request.trip_id:
            trip_context = self.get_trip(request.trip_id)

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

    def _save_trip(
        self,
        trip_id: str,
        plan: TravelPlan,
        request: TravelRequest,
    ) -> None:
        """Persist the generated travel plan in PostgreSQL."""

        plan_data = plan.model_dump(mode="json")

        self.trip_repository.create(
            trip_id=trip_id,
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            travellers=request.travellers,
            budget=request.budget,
            currency=request.currency,
            preferences=request.travel_preferences,
            travel_plan_json=plan_data,
        )

        logger.info("Travel plan persisted: trip_id=%s", trip_id)
