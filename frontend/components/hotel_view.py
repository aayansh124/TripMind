"""Accommodation recommendations view with discovery disclaimers."""

from typing import Any, Dict, List
import streamlit as st


def render_hotel_view(trip_plan: Dict[str, Any]) -> None:
    """Render recommended hotels, boutique stays, and discovery sources.

    Args:
        trip_plan: Dictionary representing consolidated TravelPlan.
    """
    st.markdown("### 🏨 Accommodation Recommendations")
    st.caption("Discovered via web search analysis matching your style and budget.")

    hotels: List[Dict[str, Any]] = trip_plan.get("hotels", [])

    if not hotels:
        st.info("No hotel recommendations discovered for this destination.")
        return

    cols = st.columns(2)

    for idx, h in enumerate(hotels):
        col = cols[idx % 2]
        with col:
            name = h.get("hotel_name", "Recommended Stay")
            loc = h.get("location", "Central Area")
            desc = h.get("description", "")
            price = h.get("estimated_price_per_night")
            curr = h.get("currency", "USD")
            rating = h.get("rating")
            web = h.get("website") or h.get("source_url")

            price_str = f"~{price:,.2f} {curr}/night" if price else "Rate on request"
            rating_str = f"⭐ {rating:.1f}/5.0" if rating else "Unrated"

            with st.container():
                st.markdown(
                    f"""
                    <div style='background: #1E293B; padding: 1.25rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #334155; min-height: 200px;'>
                        <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                            <h4 style='margin: 0; color: #F8FAFC; font-size: 1.1rem;'>{name}</h4>
                            <span style='color: #FBBF24; font-weight: 600; font-size: 0.9rem;'>{rating_str}</span>
                        </div>
                        <p style='color: #94A3B8; font-size: 0.85rem; margin: 0.25rem 0 0.75rem 0;'>📍 {loc}</p>
                        <p style='color: #CBD5E1; font-size: 0.9rem; line-height: 1.5;'>{desc}</p>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;'>
                            <span style='color: #38BDF8; font-weight: 700; font-size: 1rem;'>{price_str}</span>
                            {"<a href='" + web + "' target='_blank' style='background: #3B82F6; color: white; padding: 0.35rem 0.8rem; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>View Stay ↗</a>" if web else ""}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.warning("⚠️ **Notice:** Hotel recommendations are discovered from public web data. Real-time room availability and confirmed pricing must be booked directly with properties.")

