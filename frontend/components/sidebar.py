"""Sidebar navigation and system observability panel."""

import os
from dotenv import load_dotenv
import streamlit as st
from frontend.services.api_client import api_client
from frontend.utils.session import clear_current_trip

# Ensure .env variables are loaded
load_dotenv()


def render_sidebar() -> str:
    """Render application sidebar with navigation and live infrastructure status.

    Returns:
        Selected page navigation string.
    """
    with st.sidebar:
        st.markdown("### 🧭 Navigation")

        pages = [
            "✨ New Trip",
            "🗂️ My Trips",
            "📜 Travel History",
            "💬 Chat Assistant",
        ]

        current = st.session_state.get("current_page", "✨ New Trip")
        idx = pages.index(current) if current in pages else 0

        selected_page = st.radio(
            "Select View",
            options=pages,
            index=idx,
            label_visibility="collapsed",
        )
        st.session_state["current_page"] = selected_page

        st.divider()

        # Quick Actions
        if st.session_state.get("current_trip"):
            active_dest = st.session_state["current_trip"].get("destination", "Current Trip")
            st.markdown(f"**Active Plan:** `{active_dest}`")
            if st.button("➕ Plan Another Trip", use_container_width=True):
                clear_current_trip()
                st.session_state["current_page"] = "✨ New Trip"
                st.rerun()

        st.divider()

        # Infrastructure Health Monitor
        st.markdown("### ⚡ System Status")
        health = api_client.check_backend_health()

        b_status = health.get("backend", "offline")
        d_status = health.get("database", "offline")
        r_status = health.get("redis", "offline")
        llm_model = health.get("model") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"

        # Color codes
        def get_badge(stat: str) -> str:
            if stat.startswith("connected") or stat in ["operational"]:
                return f"<span style='color: #10B981; font-weight: 600;'>● {stat.title()}</span>"
            elif stat in ["degraded", "disconnected"]:
                return f"<span style='color: #F59E0B; font-weight: 600;'>● {stat.title()}</span>"
            return f"<span style='color: #EF4444; font-weight: 600;'>● {stat.title()}</span>"

        def get_cache_badge(stat: str) -> str:
            if stat == "connected":
                return "<span style='color: #10B981; font-weight: 600;'>● Connected (Redis)</span>"
            return "<span style='color: #94A3B8; font-weight: 500;'>○ Direct Mode (No Cache)</span>"

        db_label = "Database (SQLite)" if "sqlite" in os.getenv("DATABASE_URL", "").lower() else "Database"

        st.markdown(
            f"""
            <div style='font-size: 0.85rem; line-height: 1.8;'>
                <div>Backend: {get_badge(b_status)}</div>
                <div>{db_label}: {get_badge(d_status)}</div>
                <div>Cache: {get_cache_badge(r_status)}</div>
                <div>LLM: <span style='color: #10B981; font-weight: 600;'>● {llm_model}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("AI-Powered Multi-Agent Architecture v1.0")

    return selected_page

