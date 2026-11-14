"""Database repository layer for managing Trips and Conversations."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.models import ConversationModel, TripModel
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import logger


class TripRepository:
    """Repository managing Trip persistence operations."""

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
        preferences: Optional[str],
        travel_plan_json: Dict[str, Any],
    ) -> TripModel:
        """Create and persist a new trip record."""
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
            logger.info("Successfully persisted trip with id: %s", trip.id)
            return trip
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create trip record %s: %s", trip_id, e)
            raise DatabaseError(f"Failed to persist trip: {str(e)}")

    def get_by_id(self, trip_id: str) -> Optional[TripModel]:
        """Fetch trip record by unique ID."""
        try:
            return self.db.query(TripModel).filter(TripModel.id == trip_id).first()
        except SQLAlchemyError as e:
            logger.error("Database query failed for trip %s: %s", trip_id, e)
            raise DatabaseError(f"Error retrieving trip: {str(e)}")

    def get_all(self, limit: int = 100) -> List[TripModel]:
        """Fetch all saved trips ordered by latest creation."""
        try:
            return (
                self.db.query(TripModel)
                .order_by(TripModel.created_at.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error("Database query failed for listing trips: %s", e)
            raise DatabaseError(f"Error listing trips: {str(e)}")

    def update(self, trip_id: str, travel_plan_json: Dict[str, Any]) -> Optional[TripModel]:
        """Update existing trip's travel plan JSON."""
        try:
            trip = self.get_by_id(trip_id)
            if not trip:
                return None
            trip.travel_plan_json = travel_plan_json
            self.db.commit()
            self.db.refresh(trip)
            return trip
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database update failed for trip %s: %s", trip_id, e)
            raise DatabaseError(f"Error updating trip: {str(e)}")

    def delete(self, trip_id: str) -> bool:
        """Delete a trip by unique ID."""
        try:
            trip = self.get_by_id(trip_id)
            if not trip:
                return False
            self.db.delete(trip)
            self.db.commit()
            logger.info("Successfully deleted trip with id: %s", trip_id)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database deletion failed for trip %s: %s", trip_id, e)
            raise DatabaseError(f"Error deleting trip: {str(e)}")


class ConversationRepository:
    """Repository managing Conversation thread mapping."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, thread_id: str, trip_id: Optional[str] = None) -> ConversationModel:
        """Create or register a conversation thread."""
        try:
            existing = self.get_by_thread_id(thread_id)
            if existing:
                return existing

            conv = ConversationModel(
                id=str(uuid.uuid4()),
                thread_id=thread_id,
                trip_id=trip_id,
            )
            self.db.add(conv)
            self.db.commit()
            self.db.refresh(conv)
            return conv
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to register conversation thread %s: %s", thread_id, e)
            raise DatabaseError(f"Error registering conversation: {str(e)}")

    def get_by_thread_id(self, thread_id: str) -> Optional[ConversationModel]:
        """Fetch conversation record by thread ID."""
        try:
            return self.db.query(ConversationModel).filter(ConversationModel.thread_id == thread_id).first()
        except SQLAlchemyError as e:
            logger.error("Database query failed for conversation %s: %s", thread_id, e)
            raise DatabaseError(f"Error retrieving conversation: {str(e)}")

