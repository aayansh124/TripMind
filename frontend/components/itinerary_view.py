
"""Daily itinerary view with itemized schedules and budget breakdown."""

from typing import Any

import streamlit as st


def _safe_number(value: Any) -> float:
    """Convert a value to a number with a safe default."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def render_itinerary_view(trip_plan: dict[str, Any]) -> None:
    """Render day-wise schedules and budget information."""

    st.markdown("### Day-by-Day Itinerary")

    itinerary_days = trip_plan.get("itinerary") or []
    budget = trip_plan.get("budget") or {}
    currency = str(budget.get("currency") or "USD")

    if not itinerary_days:
        st.info("No detailed daily itinerary items available for this trip.")
        return

    tab_labels = [
        f"Day {day.get('day', index + 1)}"
        for index, day in enumerate(itinerary_days)
    ]
    tabs = st.tabs(tab_labels)

    for idx, (tab, day) in enumerate(zip(tabs, itinerary_days)):
        with tab:
            day_num = day.get("day", idx + 1)
            cal_date = day.get("date")

            st.markdown(f"#### Day {day_num}")
            if cal_date:
                st.caption(str(cal_date))

            col1, col2, col3 = st.columns(3)

            time_periods = [
                ("Morning", "morning", col1, "Morning arrival or leisure exploration."),
                ("Afternoon", "afternoon", col2, "Afternoon cultural activities and dining."),
                ("Evening", "evening", col3, "Evening dining and night walk."),
            ]

            for title, key, column, fallback in time_periods:
                with column:
                    st.markdown(f"**{title}**")
                    activities = day.get(key) or []

                    if activities:
                        for activity in activities:
                            st.write(f"- {activity}")
                    else:
                        st.caption(fallback)

            st.divider()

            budget_col, locations_col = st.columns([1, 2])

            with locations_col:
                places = day.get("places_to_visit") or []
                if places:
                    st.markdown("**Key Locations**")
                    st.write(", ".join(str(place) for place in places))

            with budget_col:
                daily_total = _safe_number(day.get("daily_total"))
                st.metric(
                    label="Estimated Daily Cost",
                    value=f"{daily_total:,.2f} {currency}",
                )

    st.divider()
    st.markdown("### Financial Breakdown & Budget Audit")

    breakdown = trip_plan.get("budget_breakdown") or {}

    if not breakdown:
        st.info("Detailed budget breakdown is not available.")
        return

    user_budget = _safe_number(breakdown.get("user_budget"))
    total_cost = _safe_number(breakdown.get("total_estimated_cost"))
    hotel_cost = _safe_number(breakdown.get("hotel_estimate"))
    food_cost = _safe_number(breakdown.get("food_estimate"))
    transport_cost = _safe_number(breakdown.get("transport_estimate"))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Allocated Budget", f"{user_budget:,.2f} {currency}")

    with col2:
        st.metric("Total Estimated Cost", f"{total_cost:,.2f} {currency}")

    with col3:
        st.metric("Lodging Estimate", f"{hotel_cost:,.2f} {currency}")

    with col4:
        st.metric(
            "Food & Transit",
            f"{food_cost + transport_cost:,.2f} {currency}",
        )

    if breakdown.get("is_within_budget"):
        st.success("Projected expenses are within your target budget!")
    else:
        overrun = _safe_number(breakdown.get("overrun_amount"))
        st.warning(
            f"Projected expenses exceed the target budget by "
            f"{overrun:,.2f} {currency}. Consider adjusting activities or lodging."
        )

    with st.expander("Detailed Calculation Assumptions"):
        notes = breakdown.get("calculation_notes") or []

        if notes:
            for note in notes:
                st.write(f"- {note}")
        else:
            st.caption("No calculation notes available.")
