"""Flight intelligence and timetable schedule display component."""

from typing import Any, Dict, List
import streamlit as st


def render_flight_view(trip_plan: Dict[str, Any]) -> None:
    """Render verified flight options and API schedule feeds.

    Args:
        trip_plan: Dictionary representing consolidated TravelPlan.
    """
    st.markdown("### 🛫 Flight Information & Schedules")

    flights: List[Dict[str, Any]] = trip_plan.get("flights", [])

    if not flights:
        st.info(
            "ℹ️ Live scheduled flight tracking was not retrieved for this route via AviationStack. "
            "Please check airline aggregators (Google Flights, Skyscanner) using the designated airport codes."
        )
        return

    st.caption("Flight data sourced via AviationStack API (Timetable Status Feed).")

    for idx, f in enumerate(flights):
        with st.container():
            airline = f.get("airline") or "Commercial Airline"
            flight_num = f.get("flight_number") or "Scheduled Route"
            dep_apt = f.get("departure_airport") or "Origin Airport"
            arr_apt = f.get("arrival_airport") or "Destination Airport"
            dep_time = f.get("departure_time") or "Scheduled"
            arr_time = f.get("arrival_time") or "Scheduled"
            status = f.get("flight_status", "Scheduled").title()

            price_val = f.get("price")
            currency = f.get("currency") or "USD"
            price_display = f"{price_val:,.2f} {currency}" if (price_val and f.get("is_verified_price")) else "Unverified (Check Airline)"

            st.markdown(
                f"""
                <div style='background: #1E293B; padding: 1.25rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #334155;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;'>
                        <span style='font-size: 1.15rem; font-weight: 700; color: #F8FAFC;'>✈️ {airline} ({flight_num})</span>
                        <span style='background: #0284C7; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem;'>{status}</span>
                    </div>
                    <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; color: #CBD5E1; font-size: 0.95rem;'>
                        <div><strong>Departure:</strong><br>{dep_apt}<br><small style='color: #94A3B8;'>{dep_time}</small></div>
                        <div><strong>Arrival:</strong><br>{arr_apt}<br><small style='color: #94A3B8;'>{arr_time}</small></div>
                        <div><strong>Fare Rate:</strong><br><span style='color: #38BDF8; font-weight: 600;'>{price_display}</span><br><small style='color: #94A3B8;'>Source: {f.get('source', 'AviationStack')}</small></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.info("⚠️ AviationStack provides timetable schedules. Final ticket prices and seat availability must be purchased directly via carrier sites.")

