"""Daily itinerary view with itemized schedules and budget breakdown."""

from typing import Any, Dict, List
import streamlit as st


def render_itinerary_view(trip_plan: Dict[str, Any]) -> None:
    """Render day-wise schedule cards and financial reconciliation.

    Args:
        trip_plan: Dictionary representing consolidated TravelPlan.
    """
    st.markdown("### 📅 Day-by-Day Itinerary")

    itinerary_days: List[Dict[str, Any]] = trip_plan.get("itinerary", [])
    currency = trip_plan.get("budget", {}).get("currency", "USD")

    if not itinerary_days:
        st.info("No detailed daily itinerary items available for this trip.")
        return

    # Tabs for each travel day
    tab_labels = [f"Day {d.get('day', i+1)}" for i, d in enumerate(itinerary_days)]
    tabs = st.tabs(tab_labels)

    for idx, (tab, day) in enumerate(zip(tabs, itinerary_days)):
        with tab:
            day_num = day.get("day", idx + 1)
            cal_date = day.get("date")
            date_str = f" ({cal_date})" if cal_date else ""

            st.markdown(f"#### Day {day_num}{date_str}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**🌅 Morning**")
                morning_items = day.get("morning", [])
                if morning_items:
                    for item in morning_items:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("*Morning arrival or leisure exploration.*")

            with col2:
                st.markdown("**☀️ Afternoon**")
                afternoon_items = day.get("afternoon", [])
                if afternoon_items:
                    for item in afternoon_items:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("*Afternoon cultural activities and dining.*")

            with col3:
                st.markdown("**🌙 Evening**")
                evening_items = day.get("evening", [])
                if evening_items:
                    for item in evening_items:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("*Evening dining and night walk.*")

            st.divider()

            # Highlights & Daily Budget Estimate
            bcol1, bcol2 = st.columns([2, 1])

            with bcol1:
                places = day.get("places_to_visit", [])
                if places:
                    st.markdown(f"**📍 Key Locations:** {', '.join(places)}")

            with bcol2:
                daily_tot = day.get("daily_total", 0.0)
                st.metric(
                    label="Estimated Daily Cost",
                    value=f"{daily_tot:,.2f} {currency}",
                )

    # Deterministic Budget Breakdown Section
    st.divider()
    st.markdown("### 💰 Financial Breakdown & Budget Audit")

    bb = trip_plan.get("budget_breakdown", {})
    if bb:
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.metric("Allocated Budget", f"{bb.get('user_budget', 0):,.2f} {currency}")
        with mcol2:
            st.metric("Total Estimated Cost", f"{bb.get('total_estimated_cost', 0):,.2f} {currency}")
        with mcol3:
            st.metric("Lodging Estimate", f"{bb.get('hotel_estimate', 0):,.2f} {currency}")
        with mcol4:
            st.metric("Food & Transit", f"{(bb.get('food_estimate', 0) + bb.get('transport_estimate', 0)):,.2f} {currency}")

        if bb.get("is_within_budget"):
            st.success("✅ Projected expenses are within your target budget!")
        else:
            overrun = bb.get("overrun_amount", 0)
            st.warning(f"⚠️ Projected expenses exceed target budget by **{overrun:,.2f} {currency}**. Review luxury activities or lodging to reduce costs.")

        with st.expander("🔍 Detailed Calculation Assumptions"):
            for note in bb.get("calculation_notes", []):
                st.markdown(f"- {note}")

