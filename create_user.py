#!/usr/bin/env python3
"""CLI tool to create users for the Display Intelligence Dashboard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.auth import init_auth_tables, create_user


def main():
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <email> <password>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    init_auth_tables()

    try:
        create_user(email, password)
        print(f"User created: {email}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
