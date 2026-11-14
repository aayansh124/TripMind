
"""Main Streamlit dashboard for the AI Travel Planner."""

from typing import Any

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


def format_amount(value: Any) -> float:
    """Convert a value to a numeric amount safely."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


st.set_page_config(
    page_title="AI Multi-Agent Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()

render_header()
selected_page = render_sidebar()


if selected_page == "✨ New Trip":
    current_plan = st.session_state.get("current_trip")

    if not current_plan:
        render_trip_form()

    else:
        col_title, col_button = st.columns([4, 1])

        with col_title:
            destination = current_plan.get("destination", "Unknown")
            departure = current_plan.get("departure_date", "")
            return_date = current_plan.get("return_date", "")
            duration = current_plan.get("duration_days", 0)

            st.title(f"Journey to {destination}")
            st.caption(
                f"{departure} → {return_date} | {duration} Days"
            )

        with col_button:
            if st.button("Plan New Trip"):
                clear_current_trip()
                st.rerun()

        destination_data = current_plan.get("destination_overview") or {}

        if destination_data:
            st.markdown("### Destination Overview")
            st.write(destination_data.get("overview", ""))

            highlights = destination_data.get("highlights") or []

            if highlights:
                st.markdown("**Top Highlights**")
                columns = st.columns(min(3, len(highlights)))

                for index, highlight in enumerate(highlights[:3]):
                    columns[index].info(str(highlight))

        itinerary_tab, flight_tab, hotel_tab, weather_tab, chat_tab = (
            st.tabs(
                [
                    "Itinerary & Budget",
                    "Flights",
                    "Hotels",
                    "Weather",
                    "Chat Assistant",
                ]
            )
        )

        with itinerary_tab:
            render_itinerary_view(current_plan)

        with flight_tab:
            render_flight_view(current_plan)

        with hotel_tab:
            render_hotel_view(current_plan)

        with weather_tab:
            render_weather_view(current_plan)

        with chat_tab:
            render_chat_interface(
                trip_id=current_plan.get("trip_id")
            )

        st.divider()

        tips_column, sources_column = st.columns(2)

        with tips_column:
            st.markdown("#### Travel Tips & Etiquette")

            for tip in current_plan.get("travel_tips") or []:
                st.write(f"- {tip}")

        with sources_column:
            st.markdown("#### Information Sources & Audits")

            for source in current_plan.get("sources") or []:
                st.code(str(source), language=None)

            for warning in current_plan.get("warnings") or []:
                st.caption(f"Warning: {warning}")


elif selected_page == "🗂️ My Trips":
    current_plan = st.session_state.get("current_trip")

    if current_plan:
        st.markdown(
            f"### Currently Active Plan: "
            f"{current_plan.get('destination', 'Unknown')}"
        )
        st.json(current_plan, expanded=False)

    else:
        st.info(
            "No active trip selected. Create a trip or load one "
            "from Travel History."
        )


elif selected_page == "📜 Travel History":
    st.markdown("### Saved Travel Plans")

    trips = api_client.get_trips()

    if not trips:
        st.info(
            "No saved travel history found. "
            "Generate your first travel plan to get started."
        )

    else:
        for trip in trips:
            trip_id = trip.get("trip_id")
            destination = trip.get("destination", "Trip")
            origin = trip.get("origin", "")
            departure = trip.get("departure_date", "")
            return_date = trip.get("return_date", "")
            budget = format_amount(trip.get("budget"))
            currency = trip.get("currency", "USD")

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{destination}** (from {origin})")
                    st.caption(
                        f"{departure} to {return_date}"
                    )
                    st.caption(
                        f"Budget: {budget:,.2f} {currency} | "
                        f"ID: {trip_id}"
                    )

                with col2:
                    if st.button(
                        "Open Trip",
                        key=f"open_{trip_id}",
                    ):
                        full_trip = api_client.get_trip(trip_id)

                        if full_trip:
                            set_current_trip(full_trip)
                            st.session_state["current_page"] = "✨ New Trip"
                            st.rerun()
                        else:
                            st.error("Unable to load this trip.")

                with col3:
                    if st.button(
                        "Delete",
                        key=f"delete_{trip_id}",
                    ):
                        if api_client.delete_trip(trip_id):
                            st.success("Trip deleted successfully.")
                            st.rerun()
                        else:
                            st.error("Unable to delete this trip.")


elif selected_page == "💬 Chat Assistant":
    current_trip_id = st.session_state.get("current_trip_id")
    render_chat_interface(trip_id=current_trip_id)
