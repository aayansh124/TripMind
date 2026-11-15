
"""Sidebar navigation and system status panel."""

import html
import os

import streamlit as st

from frontend.services.api_client import api_client
from frontend.utils.session import clear_current_trip


def render_sidebar() -> str:
    """Render navigation and backend infrastructure status."""

    with st.sidebar:
        st.markdown("### Navigation")

        pages = [
            "✨ New Trip",
            "🗂️ My Trips",
            "📜 Travel History",
            "💬 Chat Assistant",
        ]

        if "navigation_page" not in st.session_state:
            st.session_state["navigation_page"] = st.session_state.get(
                "current_page",
                "✨ New Trip",
            )

        selected_page = st.radio(
            "Select View",
            options=pages,
            key="navigation_page",
            label_visibility="collapsed",
        )

        st.session_state["current_page"] = selected_page

        st.divider()

        current_trip = st.session_state.get("current_trip")

        if current_trip:
            active_destination = current_trip.get(
                "destination",
                "Current Trip",
            )

            st.markdown(f"**Active Plan:** `{active_destination}`")

            if st.button(
                "Plan Another Trip",
                use_container_width=True,
            ):
                clear_current_trip()
                st.session_state["navigation_page"] = "✨ New Trip"
                st.session_state["current_page"] = "✨ New Trip"
                st.rerun()

        st.divider()

        st.markdown("### System Status")

        health = api_client.check_backend_health()

        backend_status = str(health.get("backend", "offline"))
        database_status = str(health.get("database", "offline"))
        redis_status = str(health.get("redis", "offline"))

        llm_model = str(
            health.get("model")
            or os.getenv("GEMINI_MODEL")
            or "gemini-2.5-flash"
        )

        def get_status_badge(status: str) -> str:
            """Return HTML badge for infrastructure status."""

            if status.startswith("connected") or status == "operational":
                color = "#10B981"
            elif status in ("degraded", "disconnected"):
                color = "#F59E0B"
            else:
                color = "#EF4444"

            safe_status = html.escape(status.title())

            return (
                f"<span style='color:{color};font-weight:600;'>"
                f"● {safe_status}</span>"
            )

        def get_cache_badge(status: str) -> str:
            """Return the Redis cache status badge."""

            if status == "connected":
                return (
                    "<span style='color:#10B981;font-weight:600;'>"
                    "● Connected (Redis)</span>"
                )

            return (
                "<span style='color:#94A3B8;font-weight:500;'>"
                "○ Direct Mode (No Cache)</span>"
            )

        safe_llm_model = html.escape(llm_model)

        st.markdown(
            f"""
            <div style="font-size:0.85rem;line-height:1.8;">
                <div>Backend: {get_status_badge(backend_status)}</div>
                <div>Database (PostgreSQL): {get_status_badge(database_status)}</div>
                <div>Cache: {get_cache_badge(redis_status)}</div>
                <div>LLM: {safe_llm_model}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("AI Multi-Agent Travel Planner")

    return selected_page
