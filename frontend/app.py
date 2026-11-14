"""Streamlit Application Main Dashboard."""

import streamlit as st

from frontend.components.chat_interface import render_chat_interface
from frontend.components.flight_view import render_flight_view
from frontend.components.header import render_header
from frontend.components.hotel_view import render_hotel_view
from frontend.components.itinerary_view import render_itinerary_view
from frontend.components.sidebar import render_sidebar
from frontend.components.trip_form import render_trip_form
from frontend.components.weather_view import render_weather_view
from frontend.services.api_client import api_client
from frontend.utils.session import (
    clear_current_trip,
    init_session_state,
    set_current_trip,
)

# Page configuration
st.set_page_config(
    page_title="AI Multi-Agent Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()

# Render Brand Header & Sidebar Navigation
render_header()
selected_page = render_sidebar()


# --- View Handlers ---

if selected_page == "✨ New Trip":
    current_plan = st.session_state.get("current_trip")

    if not current_plan:
        render_trip_form()
    else:
        # Action Bar
        col_title, col_btn = st.columns([4, 1])
        with col_title:
            st.markdown(
                f"## 🌟 Journey to {current_plan.get('destination')} "
                f"<small style='font-size: 1rem; color: #94A3B8;'>({current_plan.get('departure_date')} → {current_plan.get('return_date')}, {current_plan.get('duration_days')} Days)</small>",
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("🔄 Plan New Trip"):
                clear_current_trip()
                st.rerun()

        # Destination Overview Block
        dest_data = current_plan.get("destination_overview", {})
        if dest_data:
            with st.container():
                st.markdown("### 🏛️ Destination Overview")
                st.markdown(dest_data.get("overview", ""))
                highlights = dest_data.get("highlights", [])
                if highlights:
                    st.markdown("**Top Highlights:**")
                    cols = st.columns(min(3, len(highlights)))
                    for i, hl in enumerate(highlights[:3]):
                        cols[i % len(cols)].info(f"✨ {hl}")

        # Tabbed Workspace
        t_itin, t_flights, t_hotels, t_weather, t_chat = st.tabs([
            "📅 Itinerary & Budget",
            "🛫 Flights",
            "🏨 Hotels",
            "🌤️ Weather",
            "💬 Chat Assistant",
        ])

        with t_itin:
            render_itinerary_view(current_plan)

        with t_flights:
            render_flight_view(current_plan)

        with t_hotels:
            render_hotel_view(current_plan)

        with t_weather:
            render_weather_view(current_plan)

        with t_chat:
            render_chat_interface(trip_id=current_plan.get("trip_id"))

        # Practical Travel Tips & Sourced References
        st.divider()
        c_tips, c_src = st.columns(2)
        with c_tips:
            st.markdown("#### 💡 Travel Tips & Etiquette")
            for tip in current_plan.get("travel_tips", []):
                st.markdown(f"- {tip}")

        with c_src:
            st.markdown("#### 🔗 Information Sources & Audits")
            for src in current_plan.get("sources", []):
                st.markdown(f"- `{src}`")
            for warn in current_plan.get("warnings", []):
                st.caption(f"⚠️ {warn}")


elif selected_page == "🗂️ My Trips":
    current_plan = st.session_state.get("current_trip")
    if current_plan:
        st.markdown(f"### Currently Active Plan: **{current_plan.get('destination')}**")
        st.json(current_plan, expanded=False)
    else:
        st.info("No active trip selected. Create one under '✨ New Trip' or load from '📜 Travel History'.")


elif selected_page == "📜 Travel History":
    st.markdown("### 📜 Saved Travel Plans")
    trips = api_client.get_trips()

    if not trips:
        st.info("No saved travel history found. Generate your first plan to start tracking trips!")
    else:
        for t in trips:
            t_id = t.get("trip_id")
            dest = t.get("destination", "Trip")
            orig = t.get("origin", "")
            dep = t.get("departure_date", "")
            ret = t.get("return_date", "")
            budget = t.get("budget", 0)
            curr = t.get("currency", "USD")

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{dest}** (from {orig}) • `{dep}` to `{ret}`")
                    st.caption(f"Budget: {budget:,.2f} {curr} • ID: `{t_id}`")
                with col2:
                    if st.button("Open Trip", key=f"open_{t_id}"):
                        full_trip = api_client.get_trip(t_id)
                        if full_trip:
                            set_current_trip(full_trip)
                            st.session_state["current_page"] = "✨ New Trip"
                            st.rerun()
                with col3:
                    if st.button("Delete", key=f"del_{t_id}"):
                        if api_client.delete_trip(t_id):
                            st.success(f"Deleted trip {dest}")
                            st.rerun()


elif selected_page == "💬 Chat Assistant":
    current_trip_id = st.session_state.get("current_trip_id")
    render_chat_interface(trip_id=current_trip_id)

