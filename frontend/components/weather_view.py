
"""Destination weather observations and forecast view component."""

from typing import Any

import streamlit as st


def _format_number(value: Any, suffix: str = "") -> str:
    """Format a numeric value safely."""
    try:
        if value is None:
            return "N/A"
        return f"{float(value):.1f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def render_weather_view(trip_plan: dict[str, Any]) -> None:
    """Render weather conditions, forecast trends, and packing advice."""

    st.markdown("### Destination Weather & Climate")

    weather = trip_plan.get("weather") or {}

    if not weather:
        st.info("Weather information is currently unavailable.")
        return

    temperature = _format_number(
        weather.get("temperature_celsius"), " °C"
    )
    condition = str(weather.get("condition") or "Unknown")
    humidity = _format_number(weather.get("humidity"), "%")
    wind = _format_number(weather.get("wind_speed_mps"), " m/s")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Temperature", temperature)

    with col2:
        st.metric("Conditions", condition)

    with col3:
        st.metric("Humidity", humidity)

    with col4:
        st.metric("Wind Speed", wind)

    forecast = weather.get("forecast_summary")

    if forecast:
        st.info(f"Forecast Outlook: {forecast}")

    considerations = weather.get("considerations") or []

    if considerations:
        st.markdown("#### Weather & Packing Considerations")

        for tip in considerations:
            st.write(f"- {tip}")
