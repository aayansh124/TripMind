"""Streamlit session state management utilities."""

import uuid
from typing import Any, Dict, List, Optional
import streamlit as st


def init_session_state() -> None:
    """Initialize default keys and objects in Streamlit session state."""
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())

    if "current_trip" not in st.session_state:
        st.session_state["current_trip"] = None

    if "current_trip_id" not in st.session_state:
        st.session_state["current_trip_id"] = None

    if "active_thread_id" not in st.session_state:
        st.session_state["active_thread_id"] = f"thread_{str(uuid.uuid4())[:8]}"

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "New Trip"

    if "saved_trips" not in st.session_state:
        st.session_state["saved_trips"] = []


def set_current_trip(trip_data: Dict[str, Any]) -> None:
    """Update active trip in session state and update conversation thread ID."""
    st.session_state["current_trip"] = trip_data
    trip_id = trip_data.get("trip_id")
    st.session_state["current_trip_id"] = trip_id
    if trip_id:
        st.session_state["active_thread_id"] = f"trip_{trip_id}"


def clear_current_trip() -> None:
    """Clear active trip from session state."""
    st.session_state["current_trip"] = None
    st.session_state["current_trip_id"] = None
    st.session_state["active_thread_id"] = f"thread_{str(uuid.uuid4())[:8]}"
    st.session_state["chat_messages"] = []


def add_chat_message(role: str, content: str) -> None:
    """Append a message to conversation history in session state."""
    st.session_state["chat_messages"].append({"role": role, "content": content})

