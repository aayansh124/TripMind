
"""Trip parameters input form with client-side validation."""

from datetime import date, timedelta
from typing import Any

import streamlit as st

from frontend.services.api_client import api_client
from frontend.utils.session import set_current_trip


def render_trip_form() -> dict[str, Any] | None:
    """Render the travel planning form and submit trip requirements."""

    st.markdown("### Plan Your Next Journey")
    st.markdown(
        "Specify your travel requirements. Specialist agents will research "
        "destinations, flights, hotels, weather, and create an itinerary."
    )

    today = date.today()
    default_departure = today + timedelta(days=14)
    default_return = default_departure + timedelta(days=6)

    with st.form("travel_request_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            origin = st.text_input(
                "Starting City or Airport *",
                placeholder="e.g. Delhi, Mumbai, London",
                help="City or IATA airport code where the journey starts.",
            )

            departure_date = st.date_input(
                "Departure Date *",
                value=default_departure,
                min_value=today,
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
            )

        with col2:
            destination = st.text_input(
                "Destination City or Country *",
                placeholder="e.g. Goa, Paris, Tokyo",
            )

            return_date = st.date_input(
                "Return Date *",
                value=default_return,
                min_value=today,
            )

            budget_col, currency_col = st.columns([2, 1])

            with budget_col:
                budget = st.number_input(
                    "Total Budget *",
                    min_value=100.0,
                    max_value=1_000_000.0,
                    value=4500.0,
                    step=100.0,
                )

            with currency_col:
                currency = st.selectbox(
                    "Currency",
                    options=["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD"],
                    index=0,
                )

            accommodation_pref = st.text_input(
                "Accommodation Preference",
                placeholder="e.g. Boutique Hotel, Resort, Hostel",
            )

        preferences = st.text_area(
            "Special Interests or Preferences",
            placeholder=(
                "e.g. Food tours, historical museums, hiking, "
                "vegetarian food, quiet neighborhoods..."
            ),
            help="Include dietary requirements, preferred activities, "
            "and places you want to visit.",
        )

        submitted = st.form_submit_button(
            "Generate Travel Plan",
            use_container_width=True,
        )

    if not submitted:
        return None

    if not origin.strip():
        st.error("Please provide a starting city.")
        return None

    if not destination.strip():
        st.error("Please provide a destination.")
        return None

    if return_date < departure_date:
        st.error("Return date must be on or after departure date.")
        return None

    if budget <= 0:
        st.error("Budget must be positive.")
        return None

    payload = {
        "origin": origin.strip(),
        "destination": destination.strip(),
        "departure_date": departure_date.strftime("%Y-%m-%d"),
        "return_date": return_date.strftime("%Y-%m-%d"),
        "travellers": int(travellers),
        "budget": float(budget),
        "currency": currency,
        "travel_style": travel_style,
        "travel_preferences": preferences.strip() or None,
        "accommodation_preference": accommodation_pref.strip() or None,
    }

    with st.spinner(
        "Researching your destination, flights, hotels, weather, "
        "and daily itinerary..."
    ):
        response = api_client.create_trip(payload)

    if "error" in response:
        st.error(f"Planning Error: {response['error']}")
        return None

    plan = response.get("travel_plan")

    if not plan:
        st.error("The backend did not return a travel plan.")
        return None

    set_current_trip(plan)
    st.success("Travel plan generated successfully!")
    st.rerun()

    return plan
