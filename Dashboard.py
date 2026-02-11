"""
Display Intelligence Dashboard
A professional analytics platform for display industry intelligence.

Author: Display Intelligence
"""

import re
import secrets
import streamlit as st
from datetime import datetime, timedelta
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

_AUTH_DB = Path(__file__).parent / "auth.db"

ALLOWED_EMAILS = [
    "andrew@displayintel.com",
    "admin@displayintel.com",
]


def _validate_password(password: str) -> list[str]:
    """Return list of unmet password requirements (empty = valid)."""
    errors = []
    if len(password) < 8:
        errors.append("At least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("At least 1 uppercase letter")
    if not re.search(r"[0-9]", password):
        errors.append("At least 1 number")
    return errors


_SESSION_DAYS = 7
_DEFAULT_ADMIN_EMAIL = "admin@displayintel.com"
_DEFAULT_ADMIN_PW = "Admin123!"


def _db_is_valid() -> bool:
    """Return True if auth.db exists and passes an integrity check."""
    if not _AUTH_DB.exists():
        return False
    try:
        conn = sqlite3.connect(_AUTH_DB, check_same_thread=False)
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        return result == "ok"
    except Exception:
        return False


def _recreate_auth_db():
    """Delete corrupted DB (keeping a backup) and create a fresh one."""
    if _AUTH_DB.exists():
        backup = _AUTH_DB.with_suffix(".db.backup")
        try:
            _AUTH_DB.rename(backup)
        except Exception:
            _AUTH_DB.unlink(missing_ok=True)
        # Also remove WAL / SHM sidecar files
        _AUTH_DB.with_suffix(".db-wal").unlink(missing_ok=True)
        _AUTH_DB.with_suffix(".db-shm").unlink(missing_ok=True)


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
    """Ensure auth.db is healthy and tables exist. Recreates DB if corrupted."""
    if not _db_is_valid():
        _recreate_auth_db()

    try:
        with _auth_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    last_login TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)"
            )
            # Clean expired sessions
            conn.execute(
                "DELETE FROM sessions WHERE expires_at < ?",
                (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),),
            )
    except Exception as e:
        st.error(f"Database error during initialization: {e}")


def _ensure_admin_exists():
    """Create default admin user if the users table is empty."""
    try:
        with _auth_conn() as conn:
            cnt = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        if cnt == 0:
            try:
                email = st.secrets["admin_email"]
            except (KeyError, FileNotFoundError):
                email = _DEFAULT_ADMIN_EMAIL
            try:
                pw = st.secrets["admin_password"]
            except (KeyError, FileNotFoundError):
                pw = _DEFAULT_ADMIN_PW
            _create_user(email, pw)
    except Exception as e:
        st.error(f"Could not check/create admin user: {e}")


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


def _create_session_token(email: str) -> str:
    """Generate a session token, store in DB with 7-day expiry."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(days=_SESSION_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    with _auth_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (token, email, expires_at) VALUES (?, ?, ?)",
            (token, email.lower().strip(), expires),
        )
    return token


def _validate_session_token(token: str):
    """Check token against DB. Returns email if valid, None otherwise."""
    if not token:
        return None
    try:
        with _auth_conn() as conn:
            row = conn.execute(
                "SELECT email, expires_at FROM sessions WHERE token = ?",
                (token,),
            ).fetchone()
        if row is None:
            return None
        if datetime.utcnow() > datetime.strptime(
            row["expires_at"], "%Y-%m-%d %H:%M:%S"
        ):
            _delete_session_token(token)
            return None
        return row["email"]
    except Exception:
        return None


def _delete_session_token(token: str):
    """Remove session from DB."""
    if not token:
        return
    try:
        with _auth_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    except Exception:
        pass


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
    """Render a modern, centered auth card with sign-in / sign-up toggle."""

    if st.session_state.get("password_correct", False):
        return True

    # ── Check "Remember me" token from URL ──────────────────────────────
    token = st.query_params.get("t")
    if token:
        remembered_email = _validate_session_token(token)
        if remembered_email:
            st.session_state["password_correct"] = True
            st.session_state["user_email"] = remembered_email
            st.session_state["session_token"] = token
            return True
        else:
            # Expired or invalid token — clear it
            del st.query_params["t"]

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "signin"

    is_signup = st.session_state["auth_mode"] == "signup"

    # ── Full-page auth styling ──────────────────────────────────────────
    st.markdown("""
    <style>
        /* Background */
        .stApp { background-color: #f7f8fa !important; }

        /* Hide ALL Streamlit chrome */
        header[data-testid="stHeader"],
        #MainMenu, footer,
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        .stDeployButton { display: none !important; }

        /* Card = block-container */
        section.main .block-container {
            max-width: 400px !important;
            margin: 10vh auto 0 auto !important;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
            padding: 2.5rem 2rem 2rem !important;
        }

        /* System fonts */
        section.main .block-container,
        section.main .block-container p,
        section.main .block-container span,
        section.main .block-container input,
        section.main .block-container button,
        section.main .block-container label {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
                         'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }

        /* Inputs */
        [data-testid="stTextInput"] > div > div > input {
            height: 48px !important;
            border-radius: 8px !important;
            border: 1px solid #e1e4e8 !important;
            font-size: 15px !important;
            padding: 0 14px !important;
            background: #fff !important;
            color: #111827 !important;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        [data-testid="stTextInput"] > div > div > input:focus {
            border-color: #007AFF !important;
            box-shadow: 0 0 0 3px rgba(0,102,255,0.08) !important;
        }
        [data-testid="stTextInput"] > div > div > input::placeholder {
            color: #9ca3af !important;
        }

        /* Primary button */
        [data-testid="stBaseButton-primary"] {
            height: 48px !important;
            border-radius: 8px !important;
            background-color: #007AFF !important;
            border: none !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            color: #fff !important;
            transition: background-color 0.15s;
            margin-top: 0.25rem !important;
        }
        [data-testid="stBaseButton-primary"]:hover {
            background-color: #0062cc !important;
        }

        /* Toggle link (secondary button → plain text) */
        [data-testid="stBaseButton-secondary"] {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
            color: #6b7280 !important;
            font-size: 14px !important;
            font-weight: 400 !important;
            padding: 0.25rem !important;
            height: auto !important;
        }
        [data-testid="stBaseButton-secondary"]:hover {
            background: none !important;
            color: #007AFF !important;
            border: none !important;
        }

        /* Checkbox */
        [data-testid="stCheckbox"] { margin-top: -0.25rem !important; }
        [data-testid="stCheckbox"] label span {
            font-size: 13px !important;
            color: #6b7280 !important;
        }

        /* Vertical spacing */
        section.main [data-testid="stVerticalBlock"] {
            gap: 0.75rem !important;
        }

        /* Alerts */
        .stAlert { border-radius: 8px !important; font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Branding ────────────────────────────────────────────────────────
    st.markdown("""
        <div style="text-align:center; margin-bottom:1.5rem;">
            <div style="display:inline-flex; align-items:center; justify-content:center;
                        width:56px; height:56px;
                        background:linear-gradient(135deg,#007AFF,#5856D6);
                        border-radius:14px; margin-bottom:0.75rem;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="12" width="4" height="9" rx="1" fill="white"/>
                    <rect x="10" y="7" width="4" height="14" rx="1" fill="white" opacity=".85"/>
                    <rect x="17" y="3" width="4" height="18" rx="1" fill="white"/>
                </svg>
            </div>
            <h1 style="font-size:24px; font-weight:700; color:#111827;
                       margin:0 0 2px; letter-spacing:-0.02em;">
                Display Intelligence
            </h1>
            <p style="font-size:14px; color:#9ca3af; margin:0;">
                Industry Analytics Platform
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ── Form fields ─────────────────────────────────────────────────────
    email = st.text_input(
        "Email", placeholder="name@company.com",
        key="auth_email", label_visibility="collapsed",
    )
    password = st.text_input(
        "Password", type="password", placeholder="Password",
        key="auth_password", label_visibility="collapsed",
    )

    confirm_pw = ""
    if is_signup:
        # Password requirements hint
        pw_errors = _validate_password(password) if password else [
            "At least 8 characters", "At least 1 uppercase letter", "At least 1 number",
        ]
        req_html = "".join(
            f'<span style="color:{("#34C759" if password and r not in pw_errors else "#9ca3af")}; '
            f'font-size:12px; display:block; margin-bottom:2px;">'
            f'{"&#10003;" if password and r not in pw_errors else "&#8226;"} {r}</span>'
            for r in ["At least 8 characters", "At least 1 uppercase letter", "At least 1 number"]
        )
        st.markdown(
            f'<div style="margin:-0.25rem 0 0.5rem 2px;">{req_html}</div>',
            unsafe_allow_html=True,
        )

        confirm_pw = st.text_input(
            "Confirm password", type="password", placeholder="Confirm password",
            key="auth_confirm", label_visibility="collapsed",
        )

    if not is_signup:
        st.checkbox("Remember me", value=False, key="auth_remember")

    # ── Submit ──────────────────────────────────────────────────────────
    btn_label = "Create Account" if is_signup else "Sign In"
    if st.button(btn_label, use_container_width=True, type="primary"):
        if is_signup:
            if not email or not password:
                st.error("Please fill in all fields.")
            elif email.lower().strip() not in [e.lower() for e in ALLOWED_EMAILS]:
                st.error("Email not authorized. Contact admin for access.")
            elif _validate_password(password):
                st.error("Password does not meet requirements.")
            elif password != confirm_pw:
                st.error("Passwords do not match.")
            elif _user_exists(email):
                st.error("An account with this email already exists.")
            else:
                try:
                    _create_user(email, password)
                    st.session_state["password_correct"] = True
                    st.session_state["user_email"] = email.lower().strip()
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not create account: {e}")
        else:
            user = _verify_user(email, password)
            if user:
                st.session_state["password_correct"] = True
                st.session_state["user_email"] = user["email"]
                if st.session_state.get("auth_remember", False):
                    token = _create_session_token(user["email"])
                    st.session_state["session_token"] = token
                    st.query_params["t"] = token
                st.rerun()
            else:
                st.error("Invalid email or password.")

    # ── Forgot password (sign-in only) ──────────────────────────────────
    if not is_signup:
        if "show_forgot" not in st.session_state:
            st.session_state["show_forgot"] = False

        if st.button("Forgot password?", use_container_width=True, key="auth_forgot"):
            st.session_state["show_forgot"] = not st.session_state["show_forgot"]

        if st.session_state.get("show_forgot"):
            st.info("Contact **admin@displayintel.com** to reset your password.")

    # ── Mode toggle ─────────────────────────────────────────────────────
    toggle_text = (
        "Already have an account? Sign in"
        if is_signup
        else "Don't have an account? Create one"
    )
    if st.button(toggle_text, use_container_width=True, key="auth_toggle"):
        st.session_state["auth_mode"] = "signin" if is_signup else "signup"
        st.rerun()

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
            token = st.session_state.pop("session_token", None)
            if token:
                _delete_session_token(token)
            st.session_state["password_correct"] = False
            st.session_state.pop("user_email", None)
            st.query_params.clear()
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
