"""
Display Intelligence Dashboard
A professional analytics platform for display industry intelligence.

Author: Display Intelligence
"""

import streamlit as st
from datetime import datetime
import sys
import sqlite3
import bcrypt
from pathlib import Path
from contextlib import contextmanager

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.styling import get_css
from utils.database import DatabaseManager, format_integer, format_percent

# ---------------------------------------------------------------------------
# Auth helpers (inline – avoids import issues on Streamlit Cloud)
# ---------------------------------------------------------------------------

_AUTH_DB = Path(__file__).parent / "displayintel.db"


@contextmanager
def _auth_conn():
    conn = sqlite3.connect(_AUTH_DB, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_auth_tables():
    with _auth_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)


def _ensure_admin_exists():
    with _auth_conn() as conn:
        cnt = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    if cnt == 0:
        try:
            email = st.secrets["admin_email"]
        except (KeyError, FileNotFoundError):
            email = "admin@displayintel.com"
        try:
            pw = st.secrets["admin_password"]
        except (KeyError, FileNotFoundError):
            pw = "changeme2024!"
        _create_user(email, pw)


def _create_user(email: str, password: str):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with _auth_conn() as conn:
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email.lower().strip(), hashed),
        )


def _verify_user(email: str, password: str):
    with _auth_conn() as conn:
        row = conn.execute(
            "SELECT id, email, hashed_password, is_active FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
    if row is None or not row["is_active"]:
        return None
    if bcrypt.checkpw(password.encode(), row["hashed_password"].encode()):
        return {"id": row["id"], "email": row["email"]}
    return None


def _user_exists(email: str) -> bool:
    with _auth_conn() as conn:
        cnt = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()["c"]
    return cnt > 0


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


def _login_page():
    """Render a full-screen login page with Sign In / Sign Up tabs."""

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

    # Card wrapper
    st.markdown("""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E5E5E7;
            border-radius: 16px;
            padding: 2rem 1.75rem 1.5rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        ">
    """, unsafe_allow_html=True)

    sign_in_tab, sign_up_tab = st.tabs(["Sign In", "Sign Up"])

    with sign_in_tab:
        email = st.text_input("Email", key="signin_email", placeholder="Email address")
        password = st.text_input(
            "Password", type="password", key="signin_password", placeholder="Password"
        )
        if st.button("Sign In", use_container_width=True, type="primary"):
            user = _verify_user(email, password)
            if user:
                st.session_state["password_correct"] = True
                st.session_state["user_email"] = user["email"]
                st.rerun()
            else:
                st.error("Incorrect email or password.")

    with sign_up_tab:
        new_email = st.text_input(
            "Email", key="signup_email", placeholder="Email address"
        )
        new_password = st.text_input(
            "Password", type="password", key="signup_password", placeholder="Password"
        )
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm",
            placeholder="Confirm password",
        )
        if st.button("Sign Up", use_container_width=True, type="primary"):
            if not new_email or not new_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif _user_exists(new_email):
                st.error("An account with this email already exists.")
            else:
                try:
                    _create_user(new_email, new_password)
                    st.success("Account created! Switch to **Sign In** to log in.")
                except Exception as e:
                    st.error(f"Error creating account: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    return False


def main():
    """Main dashboard application."""

    # Initialize auth system
    _init_auth_tables()
    _ensure_admin_exists()

    # Gate: show login page until authenticated
    if not _login_page():
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
            st.session_state["password_correct"] = False
            st.session_state.pop("user_email", None)
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
