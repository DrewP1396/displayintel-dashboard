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
from utils.database import DatabaseManager, format_integer, format_percent
from utils.auth import (
    init_auth_tables,
    ensure_admin_exists,
    get_cookie_manager,
    check_auth,
    login,
    logout,
)


def _is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    return st.session_state.get("password_correct", False)


# Page configuration — collapse sidebar when not authenticated
st.set_page_config(
    page_title="Display Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" if _is_authenticated() else "collapsed",
    menu_items={
        'About': "Display Intelligence Dashboard - Industry Analytics Platform"
    }
)

# Apply custom CSS
st.markdown(get_css(), unsafe_allow_html=True)


def _login_page(cookie_manager):
    """Render a full-screen, professional login page with email/password auth."""

    # Check cookie-based session first
    check_auth(cookie_manager)
    if st.session_state.get("password_correct", False):
        return True

    # Hide sidebar, header chrome, and page nav while on login screen
    st.markdown("""
    <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 480px;
            padding-top: 8vh;
        }
    </style>
    """, unsafe_allow_html=True)

    # Branding
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2.5rem;">
            <div style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 72px; height: 72px;
                background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
                border-radius: 18px;
                margin-bottom: 1.25rem;
            ">
                <span style="font-size: 2rem; color: white; line-height: 1;">&#x1F4CA;</span>
            </div>
            <h1 style="font-size: 1.75rem; font-weight: 700; color: #1D1D1F; margin: 0 0 0.25rem;">
                Display Intelligence
            </h1>
            <p style="color: #86868B; font-size: 0.95rem; margin: 0;">
                Industry Analytics Platform
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Login card
    st.markdown("""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E5E5E7;
            border-radius: 16px;
            padding: 2rem 1.75rem 1.5rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        ">
            <p style="font-size: 0.95rem; font-weight: 600; color: #1D1D1F; margin: 0 0 0.25rem;">
                Sign in
            </p>
            <p style="font-size: 0.8125rem; color: #86868B; margin: 0 0 1rem;">
                Enter your credentials to continue.
            </p>
    """, unsafe_allow_html=True)

    email = st.text_input(
        "Email",
        key="login_email",
        placeholder="Email address",
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_password",
        placeholder="Password",
    )

    remember_me = st.checkbox("Remember me for 7 days", value=True)

    if st.button("Sign In", use_container_width=True, type="primary"):
        if login(email, password, remember_me, cookie_manager):
            st.rerun()
        else:
            st.error("Incorrect email or password. Please try again.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
        <p style="text-align: center; color: #86868B; font-size: 0.75rem; margin-top: 1.5rem;">
            Contact your administrator for access credentials.
        </p>
    """, unsafe_allow_html=True)

    return False


def main():
    """Main dashboard application."""

    # Initialize auth system
    init_auth_tables()
    ensure_admin_exists()

    # Cookie manager (one instance per session)
    cookie_manager = get_cookie_manager()

    # Gate: show login page until authenticated
    if not _login_page(cookie_manager):
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

        # Quick Filters
        st.markdown("### Quick Filters")
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.selectbox("From", options=list(range(2018, 2027)), index=0, key="dash_start_year")
        with col2:
            end_year = st.selectbox("To", options=list(range(2018, 2027)), index=8, key="dash_end_year")

        st.divider()

        # Data timestamp
        st.markdown("### Data Status")
        st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y')}")

        # User info and logout
        st.divider()
        user_email = st.session_state.get("user_email", "")
        if user_email:
            st.caption(f"Signed in as {user_email}")
        if st.button("Logout", use_container_width=True):
            logout(cookie_manager)
            st.rerun()

    # Main content - Dashboard Overview
    st.markdown("""
        <h1 style="margin-bottom: 0.25rem;">Dashboard Overview</h1>
        <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
            Real-time display industry analytics and intelligence
        </p>
    """, unsafe_allow_html=True)

    # Load summary stats
    # NOTE: get_summary_stats() does not currently support year filtering.
    # The sidebar year filters (start_year, end_year) are available for future use
    # when this function is updated to accept year parameters.
    try:
        stats = DatabaseManager.get_summary_stats()

        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                label="Total Factories",
                value=format_integer(stats['total_factories']),
                delta=f"{format_integer(stats['active_factories'])} operating"
            )

        with col2:
            st.metric(
                label="Manufacturers",
                value=format_integer(stats['manufacturers']),
                delta=None
            )

        with col3:
            st.metric(
                label="Avg Utilization",
                value=format_percent(stats['avg_utilization']),
                delta=None
            )

        with col4:
            st.metric(
                label="Equipment Orders",
                value=format_integer(stats['equipment_orders']),
                delta=None
            )

        with col5:
            st.metric(
                label="Shipment Records",
                value=format_integer(stats['shipments']),
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
                    format_integer(stats['total_factories']),
                    format_integer(stats['utilization_records']),
                    format_integer(stats['equipment_orders']),
                    format_integer(stats['shipments'])
                ],
                'Status': ['Active', 'Active', 'Active', 'Active']
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
