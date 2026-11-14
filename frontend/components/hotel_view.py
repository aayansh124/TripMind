
"""Accommodation recommendations view with discovery disclaimers."""

import html
from typing import Any

import streamlit as st


def render_hotel_view(trip_plan: dict[str, Any]) -> None:
    """Render recommended hotels and accommodation sources."""

    st.markdown("### Accommodation Recommendations")
    st.caption(
        "Discovered through web search based on travel style and budget."
    )

    hotels = trip_plan.get("hotels") or []

    if not hotels:
        st.info("No hotel recommendations discovered for this destination.")
        return

    cols = st.columns(2)

    for idx, hotel in enumerate(hotels):
        with cols[idx % 2]:
            name = html.escape(
                str(hotel.get("hotel_name") or "Recommended Stay")
            )
            location = html.escape(
                str(hotel.get("location") or "Central Area")
            )
            description = html.escape(
                str(hotel.get("description") or "")
            )
            currency = html.escape(
                str(hotel.get("currency") or "USD")
            )

            price = hotel.get("estimated_price_per_night")
            rating = hotel.get("rating")

            try:
                price_value = float(price)
                price_str = (
                    f"~{price_value:,.2f} {currency}/night"
                    if price_value > 0
                    else "Rate on request"
                )
            except (TypeError, ValueError):
                price_str = "Rate on request"

            try:
                rating_value = float(rating)
                rating_str = (
                    f"{rating_value:.1f}/5.0"
                    if 0 <= rating_value <= 5
                    else "Unrated"
                )
            except (TypeError, ValueError):
                rating_str = "Unrated"

            website = hotel.get("website") or hotel.get("source_url")
            website_html = ""

            if isinstance(website, str):
                website = website.strip()

                if website.startswith(("https://", "http://")):
                    safe_url = html.escape(website, quote=True)
                    website_html = (
                        f'<a href="{safe_url}" target="_blank" '
                        'rel="noopener noreferrer" '
                        'style="background: #3B82F6; color: white; '
                        'padding: 0.35rem 0.8rem; border-radius: 4px; '
                        'text-decoration: none; font-size: 0.85rem;">'
                        "View Stay</a>"
                    )

            st.markdown(
                f"""
                <div style="
                    background: #1E293B;
                    padding: 1.25rem;
                    border-radius: 8px;
                    margin-bottom: 1rem;
                    border: 1px solid #334155;
                    min-height: 200px;
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                    ">
                        <h4 style="margin: 0; color: #F8FAFC;">
                            {name}
                        </h4>
                        <span style="color: #FBBF24; font-weight: 600;">
                            {rating_str}
                        </span>
                    </div>

                    <p style="
                        color: #94A3B8;
                        font-size: 0.85rem;
                    ">
                        {location}
                    </p>

                    <p style="
                        color: #CBD5E1;
                        font-size: 0.9rem;
                        line-height: 1.5;
                    ">
                        {description}
                    </p>

                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-top: 1rem;
                    ">
                        <span style="
                            color: #38BDF8;
                            font-weight: 700;
                        ">
                            {price_str}
                        </span>
                        {website_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.warning(
        "Hotel recommendations are discovered from public web data. "
        "Confirm room availability and final prices directly with the property."
    )
