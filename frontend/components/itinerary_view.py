
"""Daily itinerary view with itemized schedules and budget breakdown."""

from typing import Any

import streamlit as st


def _safe_number(value: Any) -> float | None:
    """Convert a value to a number while preserving unavailable values."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_cost(value: Any, currency: str) -> str:
    """Format a cost or show that it is unavailable."""
    number = _safe_number(value)

    if number is None:
        return "Not available"

    return f"{number:,.2f} {currency}"


def render_itinerary_view(trip_plan: dict[str, Any]) -> None:
    """Render day-wise schedules and budget information."""

    st.markdown("### Day-by-Day Itinerary")

    itinerary_days = trip_plan.get("itinerary") or []
    budget = trip_plan.get("budget") or {}
    currency = str(budget.get("currency") or "INR")

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
                st.metric(
                    label="Estimated Daily Cost",
                    value=_format_cost(day.get("daily_total"), currency),
                )

    st.divider()
    st.markdown("### Financial Breakdown & Budget Audit")

    breakdown = trip_plan.get("budget_breakdown") or {}

    if not breakdown:
        st.info("Detailed budget breakdown is not available.")
        return

    comparison_available = breakdown.get("comparison_available", True)

    user_budget = breakdown.get("user_budget")
    total_cost = breakdown.get("total_estimated_cost")
    hotel_cost = breakdown.get("hotel_estimate")
    food_cost = breakdown.get("food_estimate")
    transport_cost = breakdown.get("transport_estimate")
    activities_cost = breakdown.get("activities_estimate")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Allocated Budget",
            _format_cost(user_budget, currency),
        )

    with col2:
        st.metric(
            "Total Estimated Cost",
            _format_cost(total_cost, currency),
        )

    with col3:
        st.metric(
            "Lodging Estimate",
            _format_cost(hotel_cost, currency),
        )

    with col4:
        if food_cost is not None and transport_cost is not None:
            combined_cost = (
                _safe_number(food_cost) + _safe_number(transport_cost)
            )
            combined_display = _format_cost(combined_cost, currency)
        else:
            combined_display = "Not available"

        st.metric("Food & Transit", combined_display)

    st.metric(
        "Activities Estimate",
        _format_cost(activities_cost, currency),
    )

    if not comparison_available:
        st.warning(
            "This is a partial budget estimate. Some expense categories "
            "are unavailable, so the total cannot be reliably compared "
            "with your allocated budget."
        )
    elif breakdown.get("is_within_budget") is True:
        st.success("Projected expenses are within your target budget!")
    elif breakdown.get("is_within_budget") is False:
        overrun = breakdown.get("overrun_amount")

        st.warning(
            f"Projected expenses exceed the target budget by "
            f"{_format_cost(overrun, currency)}. "
            "Consider adjusting activities or lodging."
        )
    else:
        st.info("Budget comparison is currently unavailable.")

    with st.expander("Detailed Calculation Assumptions"):
        notes = breakdown.get("calculation_notes") or []

        if notes:
            for note in notes:
                st.write(f"- {note}")
        else:
            st.caption("No calculation notes available.")
