"""Header and branding component for Streamlit application."""

import streamlit as st


def render_header() -> None:
    """Render SaaS-style header bar with custom typography and badge."""
    st.markdown(
        """
        <style>
            .main-header {
                background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                padding: 1.5rem 2rem;
                border-radius: 12px;
                color: #FFFFFF;
                margin-bottom: 2rem;
                border: 1px solid #334155;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .title-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 1rem;
            }
            .brand-title {
                font-size: 1.85rem;
                font-weight: 700;
                letter-spacing: -0.025em;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            .brand-badge {
                background: #3B82F6;
                color: #FFFFFF;
                font-size: 0.75rem;
                font-weight: 600;
                padding: 0.25rem 0.65rem;
                border-radius: 9999px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .header-subtitle {
                color: #94A3B8;
                font-size: 0.95rem;
                margin-top: 0.4rem;
                margin-bottom: 0;
            }
        </style>
        <div class="main-header">
            <div class="title-row">
                <div class="brand-title">
                    <span>✈️ AI Multi-Agent Travel Planner</span>
                    <span class="brand-badge">Autonomous LangGraph Swarm</span>
                </div>
            </div>
            <p class="header-subtitle">
                Intelligent destination synthesis, flight tracking, accommodation discovery, deterministic budget auditing, and day-by-day itineraries powered by Google Gemini.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

