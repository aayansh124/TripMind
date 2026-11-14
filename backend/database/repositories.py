"""Database repository layer for trips and conversations."""

import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.models import ConversationModel, TripModel
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import logger


class TripRepository:
    """Handle database operations for saved trips."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        trip_id: str,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        travellers: int,
        budget: float,
        currency: str,
        preferences: str | None,
        travel_plan_json: dict[str, Any],
    ) -> TripModel:
        """Create and persist a trip."""
        try:
            trip = TripModel(
                id=trip_id,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                travellers=travellers,
                budget=budget,
                currency=currency,
                preferences=preferences,
                travel_plan_json=travel_plan_json,
            )

            self.db.add(trip)
            self.db.commit()
            self.db.refresh(trip)

            logger.info("Trip persisted successfully: %s", trip_id)
            return trip

        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to create trip: %s", trip_id)
            raise DatabaseError("Failed to persist trip.") from exc

    def get_by_id(self, trip_id: str) -> TripModel | None:
        """Retrieve a trip by its ID."""
        try:
            return (
                self.db.query(TripModel)
                .filter(TripModel.id == trip_id)
                .first()
            )
        except SQLAlchemyError as exc:
            logger.exception("Failed to retrieve trip: %s", trip_id)
            raise DatabaseError("Failed to retrieve trip.") from exc

    def get_all(self, limit: int = 100) -> list[TripModel]:
        """Retrieve saved trips, newest first."""
        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        try:
            return (
                self.db.query(TripModel)
                .order_by(TripModel.created_at.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:
            logger.exception("Failed to retrieve trips.")
            raise DatabaseError("Failed to list trips.") from exc

    def update(
        self,
        trip_id: str,
        travel_plan_json: dict[str, Any],
    ) -> TripModel | None:
        """Update the generated travel plan for a trip."""
        try:
            trip = self.get_by_id(trip_id)

            if trip is None:
                return None

            trip.travel_plan_json = travel_plan_json
            self.db.commit()
            self.db.refresh(trip)

            return trip

        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to update trip: %s", trip_id)
            raise DatabaseError("Failed to update trip.") from exc

    def delete(self, trip_id: str) -> bool:
        """Delete a trip by its ID."""
        try:
            trip = self.get_by_id(trip_id)

            if trip is None:
                return False

            self.db.delete(trip)
            self.db.commit()

            logger.info("Trip deleted successfully: %s", trip_id)
            return True

        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to delete trip: %s", trip_id)
            raise DatabaseError("Failed to delete trip.") from exc


class ConversationRepository:
    """Handle database operations for conversation threads."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        thread_id: str,
        trip_id: str | None = None,
    ) -> ConversationModel:
        """Register a conversation thread if it does not exist."""
        try:
            existing = self.get_by_thread_id(thread_id)

            if existing is not None:
                return existing

            conversation = ConversationModel(
                id=str(uuid.uuid4()),
                thread_id=thread_id,
                trip_id=trip_id,
            )

            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

            return conversation

        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception(
                "Failed to register conversation: %s",
                thread_id,
            )
            raise DatabaseError("Failed to register conversation.") from exc

    def get_by_thread_id(
        self,
        thread_id: str,
    ) -> ConversationModel | None:
        """Retrieve a conversation using its thread ID."""
        try:
            return (
                self.db.query(ConversationModel)
                .filter(ConversationModel.thread_id == thread_id)
                .first()
            )
        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to retrieve conversation: %s",
                thread_id,
            )
            raise DatabaseError("Failed to retrieve conversation.") from exc