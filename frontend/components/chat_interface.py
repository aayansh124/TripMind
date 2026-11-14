
"""Conversational chat assistant interface with LangGraph thread continuity."""

import streamlit as st

from frontend.services.api_client import api_client
from frontend.utils.session import add_chat_message


def render_chat_interface(trip_id: str | None = None) -> None:
    """Render the travel assistant chat interface."""

    st.markdown("### Chat with Your Travel Assistant")
    st.markdown(
        "Ask questions about activities, packing advice, transport, "
        "or adjustments to your travel budget."
    )

    thread_id = st.session_state.get("active_thread_id")

    if not thread_id:
        st.error("Conversation thread is not initialized.")
        return

    st.caption(f"Conversation Thread: `{thread_id}`")

    messages = st.session_state.get("chat_messages", [])

    if not messages:
        st.info(
            "Hello! Ask me anything about your travel plans."
        )

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        if role not in ("user", "assistant"):
            continue

        with st.chat_message(role):
            st.markdown(content)

    user_prompt = st.chat_input(
        "Ask a question about your trip..."
    )

    if not user_prompt or not user_prompt.strip():
        return

    user_prompt = user_prompt.strip()

    add_chat_message("user", user_prompt)

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Assistant is thinking..."):
            response = api_client.send_chat_message(
                thread_id=thread_id,
                message=user_prompt,
                trip_id=trip_id,
            )

        if "error" in response:
            assistant_reply = (
                f"Unable to process your request: {response['error']}"
            )
            st.error(assistant_reply)
        else:
            assistant_reply = response.get(
                "assistant_response",
                "I have received your message.",
            )
            st.markdown(assistant_reply)

        add_chat_message("assistant", assistant_reply)
