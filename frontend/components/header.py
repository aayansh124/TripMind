
"""Header and branding component for Streamlit application."""

import streamlit as st


def render_header() -> None:
    """Render the application header and branding."""

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
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }

            .title-row {
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 1rem;
            }

            .brand-title {
                font-size: 1.85rem;
                font-weight: 700;
                letter-spacing: -0.025em;
                margin: 0;
            }

            .brand-badge {
                background: #3B82F6;
                color: #FFFFFF;
                font-size: 0.75rem;
                font-weight: 600;
                padding: 0.25rem 0.65rem;
                border-radius: 9999px;
                text-transform: uppercase;
            }

            .header-subtitle {
                color: #CBD5E1;
                font-size: 0.95rem;
                margin-top: 0.8rem;
                margin-bottom: 0;
                line-height: 1.6;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="main-header">
            <div class="title-row">
                <h1 class="brand-title">AI Multi-Agent Travel Planner</h1>
                <span class="brand-badge">LangGraph Multi-Agent System</span>
            </div>
            <p class="header-subtitle">Discover destinations, explore flight options, find accommodations, check weather, and generate personalized itineraries with Google Gemini.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
