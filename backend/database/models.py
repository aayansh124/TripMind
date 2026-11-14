"""SQLAlchemy database models for trips and conversation threads."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship

from backend.clients.database import Base


def utc_now() -> datetime:
    """Current UTC datetime."""
    return datetime.now(timezone.utc)


class TripModel(Base):
    """SQLAlchemy model representing a saved trip and its generated travel plan."""

    __tablename__ = "trips"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    departure_date = Column(String(20), nullable=False)
    return_date = Column(String(20), nullable=False)
    travellers = Column(Integer, nullable=False, default=1)
    budget = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    preferences = Column(Text, nullable=True)
    travel_plan_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now())

    # Relationship to conversation threads
    conversations = relationship("ConversationModel", back_populates="trip", cascade="all, delete-orphan")


class ConversationModel(Base):
    """SQLAlchemy model linking LangGraph conversation thread IDs to trips."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(100), unique=True, index=True, nullable=False)
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now())

    # Relationship to parent trip
    trip = relationship("TripModel", back_populates="conversations")

