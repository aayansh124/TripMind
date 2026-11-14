"""Destination weather observations and forecast view component."""

from typing import Any, Dict
import streamlit as st


def render_weather_view(trip_plan: Dict[str, Any]) -> None:
    """Render meteorological conditions, forecast trends, and packing advice.

    Args:
        trip_plan: Dictionary representing consolidated TravelPlan.
    """
    st.markdown("### 🌤️ Destination Weather & Climate")

    weather: Dict[str, Any] = trip_plan.get("weather") or {}

    if not weather:
        st.info("Weather observation is currently unavailable for this destination.")
        return

    temp = weather.get("temperature_celsius")
    cond = weather.get("condition") or "Clear"
    humidity = weather.get("humidity")
    wind = weather.get("wind_speed_mps")
    forecast_summary = weather.get("forecast_summary")
    considerations = weather.get("considerations", [])

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Temperature", f"{temp:.1f} °C" if temp is not None else "N/A")
    with m2:
        st.metric("Conditions", cond)
    with m3:
        st.metric("Humidity", f"{humidity}%" if humidity is not None else "N/A")
    with m4:
        st.metric("Wind Speed", f"{wind} m/s" if wind is not None else "N/A")

    if forecast_summary:
        st.info(f"**Forecast Outlook:** {forecast_summary}")

    if considerations:
        st.markdown("#### 🎒 Weather & Packing Considerations")
        for tip in considerations:
            st.markdown(f"- {tip}")

