"""Trip parameters input form with client-side validation."""

from datetime import date, timedelta
from typing import Any, Dict, Optional
import streamlit as st

from frontend.services.api_client import api_client
from frontend.utils.session import set_current_trip


def render_trip_form() -> Optional[Dict[str, Any]]:
    """Render the travel planning input form with validation and submit handler.

    Returns:
        Generated TravelPlan dictionary if created, else None.
    """
    st.markdown("### 🗺️ Plan Your Next Journey")
    st.markdown("Specify your travel parameters. Our specialist agents will research flights, hotels, weather, and synthesize a personalized itinerary.")

    with st.form("travel_request_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            origin = st.text_input(
                "Starting City or Airport *",
                value="New York",
                placeholder="e.g. New York, JFK, London, Mumbai",
                help="City or IATA code where your journey starts.",
            )
            default_dep = date.today() + timedelta(days=14)
            departure_date = st.date_input(
                "Departure Date *",
                value=default_dep,
                min_value=date.today(),
            )
            travellers = st.number_input(
                "Number of Travelers *",
                min_value=1,
                max_value=30,
                value=2,
                step=1,
            )
            travel_style = st.selectbox(
                "Travel Style *",
                options=[
                    "Standard",
                    "Budget",
                    "Luxury",
                    "Adventure",
                    "Family",
                    "Romantic",
                    "Cultural",
                ],
                index=0,
            )

        with col2:
            destination = st.text_input(
                "Destination City or Country *",
                value="Tokyo",
                placeholder="e.g. Tokyo, Paris, Rome, Costa Rica",
                help="Target city or region you want to visit.",
            )
            default_ret = default_dep + timedelta(days=6)
            return_date = st.date_input(
                "Return Date *",
                value=default_ret,
                min_value=default_dep,
            )
            b_col1, b_col2 = st.columns([2, 1])
            with b_col1:
                budget = st.number_input(
                    "Total Budget *",
                    min_value=100.0,
                    max_value=1000000.0,
                    value=4500.0,
                    step=100.0,
                )
            with b_col2:
                currency = st.selectbox(
                    "Currency",
                    options=["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD"],
                    index=0,
                )

            accommodation_pref = st.text_input(
                "Accommodation Preference",
                value="Boutique Hotel or 4-Star Central",
                placeholder="e.g. Boutique Hotel, Resort, Hostel, Airbnb",
            )

        preferences = st.text_area(
            "Special Interests or Preferences",
            placeholder="e.g., Foodie tour, historical museums, hiking, quiet neighborhoods, vegetarian options...",
            help="Any dietary requirements, pacing preferences, or specific must-see attractions.",
        )

        submitted = st.form_submit_button("🚀 Generate Multi-Agent Travel Plan", use_container_width=True)

    if submitted:
        # Form Validation
        if not origin.strip():
            st.error("Please provide a valid starting city.")
            return None
        if not destination.strip():
            st.error("Please provide a valid destination city.")
            return None
        if return_date < departure_date:
            st.error("Return date must be on or after departure date.")
            return None
        if budget <= 0:
            st.error("Budget must be a positive number.")
            return None

        # Build payload
        payload = {
            "origin": origin.strip(),
            "destination": destination.strip(),
            "departure_date": departure_date.strftime("%Y-%m-%d"),
            "return_date": return_date.strftime("%Y-%m-%d"),
            "travellers": int(travellers),
            "budget": float(budget),
            "currency": currency,
            "travel_style": travel_style,
            "travel_preferences": preferences.strip() if preferences else None,
            "accommodation_preference": accommodation_pref.strip() if accommodation_pref else None,
        }

        with st.spinner("🤖 Coordinating agents: Researching destination, querying flight schedules, scanning accommodations, checking weather, and synthesizing daily itinerary..."):
            response = api_client.create_trip(payload)

        if "error" in response:
            st.error(f"❌ Planning Error: {response['error']}")
            return None

        plan = response.get("travel_plan")
        if plan:
            set_current_trip(plan)
            st.success("🎉 Travel plan generated successfully!")
            st.rerun()

    return None

