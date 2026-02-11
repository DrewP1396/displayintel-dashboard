"""
Authentication module for Display Intelligence Dashboard.
Provides per-user accounts, bcrypt-hashed passwords, and cookie-based persistent sessions.
"""

import sqlite3
import secrets
import bcrypt
import streamlit as st
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timedelta

import extra_streamlit_components as stx

DB_PATH = Path(__file__).parent.parent / "displayintel.db"
SESSION_EXPIRY_DAYS = 7
COOKIE_NAME = "displayintel_session"


@contextmanager
def _get_auth_connection():
    """Context manager for auth database connections with WAL mode."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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


def init_auth_tables():
    """Create auth tables and indexes if they don't exist, clean expired sessions."""
    with _get_auth_connection() as conn:
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
        )
    cleanup_expired_sessions()


def create_user(email: str, password: str):
    """Insert a new user with a bcrypt-hashed password."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with _get_auth_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email.lower().strip(), hashed),
        )


def verify_user(email: str, password: str):
    """Check credentials. Returns a user dict or None."""
    with _get_auth_connection() as conn:
        cursor = conn.execute(
            "SELECT id, email, hashed_password, is_active FROM users WHERE email = ?",
            (email.lower().strip(),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if not row["is_active"]:
            return None
        if bcrypt.checkpw(password.encode("utf-8"), row["hashed_password"].encode("utf-8")):
            return {"id": row["id"], "email": row["email"]}
        return None


def create_session(user_id: int) -> str:
    """Generate a 64-char hex token, store in DB with 7-day expiry."""
    token = secrets.token_hex(32)
    expires_at = (datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    with _get_auth_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
    return token


def validate_session(token: str):
    """Look up token, check expiry. Returns user dict or None."""
    if not token:
        return None
    with _get_auth_connection() as conn:
        cursor = conn.execute(
            """
            SELECT s.token, s.expires_at, u.id, u.email, u.is_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (token,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if not row["is_active"]:
            return None
        expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() > expires_at:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            return None
        return {"id": row["id"], "email": row["email"]}


def delete_session(token: str):
    """Remove session row (logout)."""
    if not token:
        return
    with _get_auth_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def cleanup_expired_sessions():
    """Delete expired session rows."""
    with _get_auth_connection() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE expires_at < ?",
            (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),),
        )


@st.cache_resource
def get_cookie_manager():
    """Return a singleton CookieManager instance."""
    return stx.CookieManager()


def check_auth(cookie_manager):
    """Check session_state first, then cookie. Sets password_correct=True if valid."""
    if st.session_state.get("password_correct", False):
        return

    token = cookie_manager.get(COOKIE_NAME)
    if token:
        user = validate_session(token)
        if user:
            st.session_state["password_correct"] = True
            st.session_state["user_email"] = user["email"]
            st.session_state["session_token"] = token


def login(email: str, password: str, remember_me: bool, cookie_manager):
    """Verify creds, set session state, optionally create cookie."""
    user = verify_user(email, password)
    if user is None:
        return False

    st.session_state["password_correct"] = True
    st.session_state["user_email"] = user["email"]

    if remember_me:
        token = create_session(user["id"])
        st.session_state["session_token"] = token
        cookie_manager.set(
            COOKIE_NAME,
            token,
            expires_at=datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS),
        )
    return True


def logout(cookie_manager):
    """Clear session state, delete DB session, clear cookie."""
    token = st.session_state.get("session_token")
    if token:
        delete_session(token)

    st.session_state["password_correct"] = False
    st.session_state.pop("user_email", None)
    st.session_state.pop("session_token", None)

    cookie_manager.delete(COOKIE_NAME)


def ensure_admin_exists():
    """If the users table is empty, create a default admin user."""
    with _get_auth_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM users")
        count = cursor.fetchone()["cnt"]

    if count == 0:
        try:
            admin_email = st.secrets["admin_email"]
        except (KeyError, FileNotFoundError):
            admin_email = "admin@displayintel.com"

        try:
            admin_password = st.secrets["admin_password"]
        except (KeyError, FileNotFoundError):
            admin_password = "changeme2024!"

        create_user(admin_email, admin_password)
