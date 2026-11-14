"""Conversational chat assistant interface maintaining LangGraph thread continuity."""

from typing import Optional
import streamlit as st

from frontend.services.api_client import api_client
from frontend.utils.session import add_chat_message


def render_chat_interface(trip_id: Optional[str] = None) -> None:
    """Render conversational assistant view with persistent history and LangGraph thread state.

    Args:
        trip_id: Optional active Trip ID context.
    """
    st.markdown("### 💬 Chat with Your Travel Assistant")
    st.markdown("Ask follow-up questions regarding activities, packing advice, transit options, or budget adjustments.")

    thread_id = st.session_state.get("active_thread_id", "default_thread")
    st.caption(f"Connected Conversation Thread: `{thread_id}`")

    # Display conversation history
    messages = st.session_state.get("chat_messages", [])
    if not messages:
        st.info("👋 Hello! I am your AI Travel Assistant. How can I help refine your travel plans today?")

    for msg in messages:
        role = msg.get("role", "user")
        with st.chat_message(role):
            st.markdown(msg.get("content", ""))

    # Chat Input
    user_prompt = st.chat_input("Ask a question about your trip...")
    if user_prompt:
        # 1. Display user message immediately
        add_chat_message("user", user_prompt)
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # 2. Call backend conversational agent
        with st.chat_message("assistant"):
            with st.spinner("Assistant is thinking..."):
                response = api_client.send_chat_message(
                    thread_id=thread_id,
                    message=user_prompt,
                    trip_id=trip_id,
                )

            if "error" in response:
                err_msg = f"⚠️ {response['error']}"
                st.error(err_msg)
                add_chat_message("assistant", err_msg)
            else:
                assistant_reply = response.get("assistant_response", "I have received your message.")
                st.markdown(assistant_reply)
                add_chat_message("assistant", assistant_reply)

