
"""Streamlit session state management utilities."""

import uuid
from typing import Any

import streamlit as st


def init_session_state() -> None:
    """Initialize default values in Streamlit session state."""

    defaults = {
        "session_id": str(uuid.uuid4()),
        "current_trip": None,
        "current_trip_id": None,
        "active_thread_id": f"thread_{str(uuid.uuid4())[:8]}",
        "chat_messages": [],
        "current_page": "New Trip",
        "saved_trips": [],
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def set_current_trip(trip_data: dict[str, Any]) -> None:
    """Set the active trip and its conversation thread."""

    st.session_state["current_trip"] = trip_data

    trip_id = trip_data.get("trip_id")
    st.session_state["current_trip_id"] = trip_id

    if trip_id:
        st.session_state["active_thread_id"] = f"trip_{trip_id}"


def clear_current_trip() -> None:
    """Clear the active trip and reset its conversation state."""

    st.session_state["current_trip"] = None
    st.session_state["current_trip_id"] = None

    st.session_state["active_thread_id"] = (
        f"thread_{str(uuid.uuid4())[:8]}"
    )

    st.session_state["chat_messages"] = []


def add_chat_message(role: str, content: str) -> None:
    """Append a message to the current conversation history."""

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    st.session_state["chat_messages"].append(
        {
            "role": role,
            "content": content,
        }
    )
