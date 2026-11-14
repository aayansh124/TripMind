
"""Pydantic schemas for chat requests and responses."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class ChatMessage(BaseModel):
    """Represent a single conversation message."""

    role: str = Field(
        ...,
        description="Message role: user, assistant, or system.",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Text content of the message.",
    )
    timestamp: str = Field(default_factory=utc_now_iso)


class ChatRequest(BaseModel):
    """Validate incoming chat requests."""

    thread_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="LangGraph conversation thread ID.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query or follow-up question.",
    )
    trip_id: str | None = Field(
        None,
        description="Optional associated travel plan ID.",
    )


class ChatResponse(BaseModel):
    """Structure the assistant's chat response."""

    thread_id: str = Field(
        ...,
        description="Conversation continuity ID.",
    )
    trip_id: str | None = Field(
        None,
        description="Associated travel plan ID.",
    )
    assistant_response: str = Field(
        ...,
        description="Assistant's response.",
    )
    structured_info: dict[str, Any] | None = Field(
        None,
        description="Optional structured information.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Referenced web or API sources.",
    )
    created_at: str = Field(default_factory=utc_now_iso)
