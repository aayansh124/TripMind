
"""Flight intelligence and timetable schedule display component."""

import html
from typing import Any

import streamlit as st


def render_flight_view(trip_plan: dict[str, Any]) -> None:
    """Render flight options and timetable information."""

    st.markdown("### Flight Information & Schedules")

    flights = trip_plan.get("flights") or []

    if not flights:
        st.info(
            "Flight schedules were not retrieved for this route. "
            "Check Google Flights or Skyscanner for available options."
        )
        return

    st.caption("Flight schedule data sourced via AviationStack API.")

    for flight in flights:
        airline = html.escape(str(flight.get("airline") or "Commercial Airline"))
        flight_num = html.escape(str(flight.get("flight_number") or "Scheduled Route"))
        dep_apt = html.escape(str(flight.get("departure_airport") or "Origin Airport"))
        arr_apt = html.escape(str(flight.get("arrival_airport") or "Destination Airport"))
        dep_time = html.escape(str(flight.get("departure_time") or "Scheduled"))
        arr_time = html.escape(str(flight.get("arrival_time") or "Scheduled"))
        status = html.escape(
            str(flight.get("flight_status") or "Scheduled").title()
        )

        price = flight.get("price")
        currency = html.escape(str(flight.get("currency") or "USD"))

        if price is not None and flight.get("is_verified_price"):
            try:
                price_display = f"{float(price):,.2f} {currency}"
            except (TypeError, ValueError):
                price_display = "Unverified (Check Airline)"
        else:
            price_display = "Unverified (Check Airline)"

        price_display = html.escape(price_display)
        source = html.escape(str(flight.get("source") or "AviationStack"))

        st.markdown(
            f"""
            <div style="
                background: #1E293B;
                padding: 1.25rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                border: 1px solid #334155;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 0.75rem;
                ">
                    <span style="
                        font-size: 1.15rem;
                        font-weight: 700;
                        color: #F8FAFC;
                    ">{airline} ({flight_num})</span>

                    <span style="
                        background: #0284C7;
                        color: white;
                        padding: 0.2rem 0.6rem;
                        border-radius: 4px;
                        font-size: 0.8rem;
                    ">{status}</span>
                </div>

                <div style="
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 1rem;
                    color: #CBD5E1;
                    font-size: 0.95rem;
                ">
                    <div>
                        <strong>Departure:</strong><br>
                        {dep_apt}<br>
                        <small style="color: #94A3B8;">{dep_time}</small>
                    </div>

                    <div>
                        <strong>Arrival:</strong><br>
                        {arr_apt}<br>
                        <small style="color: #94A3B8;">{arr_time}</small>
                    </div>

                    <div>
                        <strong>Fare Rate:</strong><br>
                        <span style="
                            color: #38BDF8;
                            font-weight: 600;
                        ">{price_display}</span><br>
                        <small style="color: #94A3B8;">
                            Source: {source}
                        </small>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        "AviationStack provides timetable information. "
        "Confirm ticket prices and seat availability directly with the airline."
    )
