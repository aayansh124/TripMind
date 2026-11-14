"""Pydantic schemas for chat interactions and conversation continuity."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """Return ISO format string of current UTC time."""
    return datetime.now(timezone.utc).isoformat()


class ChatMessage(BaseModel):
    """Single chat message model."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'.")
    content: str = Field(..., description="Text content of the message.")
    timestamp: str = Field(default_factory=utc_now_iso)


class ChatRequest(BaseModel):
    """User conversational query request."""
    thread_id: str = Field(..., min_length=1, max_length=100, description="LangGraph conversation thread ID.")
    message: str = Field(..., min_length=1, max_length=2000, description="User's query or follow-up question.")
    trip_id: Optional[str] = Field(None, description="Optional associated Trip ID for context.")


class ChatResponse(BaseModel):
    """Assistant chat response."""
    thread_id: str = Field(..., description="Continuity thread ID.")
    trip_id: Optional[str] = Field(None, description="Associated Trip ID if referenced.")
    assistant_response: str = Field(..., description="Assistant's synthesized reply.")
    structured_info: Optional[Dict[str, Any]] = Field(None, description="Optional structured items extracted.")
    sources: List[str] = Field(default_factory=list, description="Referenced web or API sources.")
    created_at: str = Field(default_factory=utc_now_iso)
