# Security Overview

## Authentication

- **Password hashing**: All passwords are hashed using **bcrypt** with a random salt (default 12 rounds). Plaintext passwords are never stored.
- **Storage**: User credentials are stored in the `users` table of the SQLite database (`displayintel.db`). The `hashed_password` column contains the bcrypt hash.
- **Session management**: Authentication state is maintained via Streamlit `session_state`. Sessions do not persist across page refreshes.

## Access Control

- **Email whitelist**: Signup is restricted to emails listed in `ALLOWED_EMAILS` in `Dashboard.py`. Unrecognized emails are rejected with a generic error.
- **Password requirements**: Accounts require passwords with at least 8 characters, 1 uppercase letter, and 1 number.
- **Default admin**: On first run, a default admin account is created from `st.secrets` or fallback credentials. Change the default password immediately after deployment.

## Password Resets

- **MVP approach**: Users contact `admin@displayintel.com` to request a password reset. An admin can update credentials directly in the database or via the `create_user.py` CLI tool.
- **Future**: Email-based self-service password reset will be added when migrating to a hosted environment (e.g., Railway).

## Data Protection

- **SQLite WAL mode**: The database uses Write-Ahead Logging for safe concurrent reads.
- **No sensitive data in cookies**: Session state is server-side only; no tokens or credentials are stored in browser cookies.

## Reporting Issues

If you discover a security vulnerability, please contact **admin@displayintel.com**.
