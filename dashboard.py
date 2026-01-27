"""
Display Intelligence Dashboard
A professional analytics platform for display industry intelligence.

Author: Display Intelligence
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.styling import get_css
from utils.database import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="Display Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Display Intelligence Dashboard - Industry Analytics Platform"
    }
)

# Apply custom CSS
st.markdown(get_css(), unsafe_allow_html=True)


def check_password() -> bool:
    """Check if password is correct using Streamlit secrets."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        try:
            correct_password = st.secrets["password"]
        except (KeyError, FileNotFoundError):
            # Fallback for local development
            correct_password = "displayintel2024"

        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Remove password from state
        else:
            st.session_state["password_correct"] = False

    # Check if already authenticated
    if st.session_state.get("password_correct", False):
        return True

    # Show login form
    st.markdown("""
        <div style="text-align: center; padding: 3rem 0;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h1 style="font-size: 2.5rem; font-weight: 700; color: #1D1D1F; margin-bottom: 0.5rem;">
                Display Intelligence
            </h1>
            <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
                Industry Analytics Platform
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.08);
                border: 1px solid #E5E5E7;
            ">
        """, unsafe_allow_html=True)

        st.text_input(
            "Password",
            type="password",
            key="password",
            on_change=password_entered,
            placeholder="Enter your password"
        )

        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("Incorrect password. Please try again.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
            <p style="text-align: center; color: #86868B; font-size: 0.875rem; margin-top: 2rem;">
                Contact your administrator for access credentials.
            </p>
        """, unsafe_allow_html=True)

    return False


def main():
    """Main dashboard application."""

    # Password protection
    if not check_password():
        return

    # Sidebar
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 2rem;">📊</div>
                <h1 style="font-size: 1.25rem; margin: 0.5rem 0;">Display Intelligence</h1>
            </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Navigation info
        st.markdown("### Navigation")
        st.markdown("""
        Use the pages in the sidebar to navigate:
        - **Dashboard** - Overview & key metrics
        - **News** - Industry news & updates
        - **Suppliers** - Equipment vendors & orders
        - **Factories** - Factory database & utilization
        - **Market Intelligence** - Insights & analysis
        - **Financials** - Company financials
        """)

        st.divider()

        # Data timestamp
        st.markdown("### Data Status")
        st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y')}")

        # Logout button
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state["password_correct"] = False
            st.rerun()

    # Main content - Dashboard Overview
    st.markdown("""
        <h1 style="margin-bottom: 0.25rem;">Dashboard Overview</h1>
        <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
            Real-time display industry analytics and intelligence
        </p>
    """, unsafe_allow_html=True)

    # Load summary stats
    try:
        stats = DatabaseManager.get_summary_stats()

        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                label="Total Factories",
                value=f"{stats['total_factories']:,}",
                delta=f"{stats['active_factories']} operating"
            )

        with col2:
            st.metric(
                label="Manufacturers",
                value=f"{stats['manufacturers']:,}",
                delta=None
            )

        with col3:
            st.metric(
                label="Avg Utilization",
                value=f"{stats['avg_utilization']}%",
                delta=None
            )

        with col4:
            st.metric(
                label="Equipment Orders",
                value=f"{stats['equipment_orders']:,}",
                delta=None
            )

        with col5:
            st.metric(
                label="Shipment Records",
                value=f"{stats['shipments']:,}",
                delta=None
            )

        st.divider()

        # Quick insights section
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Quick Access")
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
                border-radius: 16px;
                padding: 1.5rem;
                color: white;
            ">
                <h3 style="color: white; margin-bottom: 0.5rem;">Factory Intelligence</h3>
                <p style="color: rgba(255,255,255,0.8); margin-bottom: 1rem;">
                    Explore 137 factories across 20+ manufacturers with detailed utilization data.
                </p>
                <p style="font-size: 0.9rem; color: rgba(255,255,255,0.6);">
                    Navigate to Factories page →
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #34C759 0%, #00C7BE 100%);
                border-radius: 16px;
                padding: 1.5rem;
                color: white;
            ">
                <h3 style="color: white; margin-bottom: 0.5rem;">Supply Chain Analytics</h3>
                <p style="color: rgba(255,255,255,0.8); margin-bottom: 1rem;">
                    Track equipment orders and supplier relationships across the industry.
                </p>
                <p style="font-size: 0.9rem; color: rgba(255,255,255,0.6);">
                    Navigate to Suppliers page →
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("### Database Coverage")

            # Create a simple summary table
            import pandas as pd
            coverage_data = pd.DataFrame({
                'Category': ['Factories', 'Utilization Records', 'Equipment Orders', 'Shipment Records'],
                'Records': [
                    f"{stats['total_factories']:,}",
                    f"{stats['utilization_records']:,}",
                    f"{stats['equipment_orders']:,}",
                    f"{stats['shipments']:,}"
                ],
                'Status': ['✓ Active', '✓ Active', '✓ Active', '✓ Active']
            })

            st.dataframe(
                coverage_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Category": st.column_config.TextColumn("Category", width="medium"),
                    "Records": st.column_config.TextColumn("Records", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small")
                }
            )

            st.markdown("<br>", unsafe_allow_html=True)

            st.info("""
            **Data Range:** January 2019 - June 2026

            This dashboard provides comprehensive coverage of the global display industry,
            including LCD and OLED manufacturing facilities.
            """)

    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        st.info("Please ensure the database file is present and accessible.")

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; color: #86868B; font-size: 0.875rem; padding: 2rem 0; border-top: 1px solid #E5E5E7;">
            Display Intelligence Dashboard • Built with Streamlit
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
