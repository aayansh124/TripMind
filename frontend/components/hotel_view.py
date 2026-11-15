
"""Accommodation recommendations view with discovery disclaimers."""

import html
from typing import Any
from urllib.parse import urlparse

import streamlit as st


def _format_price(price: Any, currency: str) -> str:
    """Format the nightly price safely."""
    if price is None:
        return "Rate on request"

    try:
        amount = float(price)
        if amount <= 0:
            return "Rate on request"

        return f"~{amount:,.2f} {currency}/night"

    except (TypeError, ValueError):
        return "Rate on request"


def _format_rating(rating: Any) -> str:
    """Format a valid hotel rating."""
    if rating is None:
        return "Unrated"

    try:
        value = float(rating)
        if 0 <= value <= 5:
            return f"{value:.1f}/5.0"

    except (TypeError, ValueError):
        pass

    return "Unrated"


def _valid_website(value: Any) -> str | None:
    """Return a valid HTTP or HTTPS website URL."""
    if not isinstance(value, str):
        return None

    url = value.strip()
    parsed = urlparse(url)

    if parsed.scheme in ("http", "https") and parsed.netloc:
        return url

    return None


def render_hotel_view(trip_plan: dict[str, Any]) -> None:
    """Render recommended hotels using native Streamlit components."""

    st.markdown("### Accommodation Recommendations")
    st.caption(
        "Discover accommodation options based on your destination, "
        "travel style and budget."
    )

    hotels = trip_plan.get("hotels") or []

    if not hotels:
        st.info(
            "No hotel recommendations were found. "
            "Try searching again or changing your accommodation preference."
        )
        return

    columns = st.columns(2)

    for index, hotel in enumerate(hotels):
        with columns[index % 2]:
            name = str(
                hotel.get("hotel_name") or "Recommended Stay"
            )
            location = str(
                hotel.get("location") or "Location not available"
            )
            description = str(
                hotel.get("description") or "No description available."
            )
            currency = str(
                hotel.get("currency") or "INR"
            ).upper()

            price = _format_price(
                hotel.get("estimated_price_per_night"),
                currency,
            )

            rating = _format_rating(
                hotel.get("rating")
            )

            website = _valid_website(
                hotel.get("website") or hotel.get("source_url")
            )

            with st.container(border=True):
                st.markdown(f"#### {name}")

                st.caption(f"📍 {location}")

                st.markdown(description)

                st.divider()

                price_col, rating_col = st.columns(2)

                with price_col:
                    st.markdown("**Estimated price**")
                    st.markdown(f"### {price}")

                with rating_col:
                    st.markdown("**Guest rating**")
                    st.markdown(f"### {rating}")

                if website:
                    st.link_button(
                        "View Hotel / Website",
                        website,
                        use_container_width=True,
                    )
                else:
                    st.caption(
                        "Website or booking link not available."
                    )

    st.divider()

    st.warning(
        "These recommendations are collected through web search. "
        "Prices, ratings and room availability may not be verified. "
        "Confirm the final details directly with the hotel before booking."
    )
