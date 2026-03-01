"""Garmin Connect authentication with token persistence."""

import getpass
import os
from pathlib import Path

from garminconnect import Garmin


TOKEN_DIR = Path.home() / ".garmin-push" / "tokens"


def get_client(email: str | None = None, password: str | None = None) -> Garmin:
    """Get an authenticated Garmin client.

    Tries loading saved tokens first. Falls back to credential login
    with interactive prompts if needed.
    """
    token_dir = str(TOKEN_DIR)

    # Try token-based login first
    if TOKEN_DIR.exists():
        try:
            client = Garmin()
            client.login(tokenstore=token_dir)
            return client
        except Exception:
            pass  # Tokens expired or invalid, fall through

    # Credential-based login
    email = email or os.environ.get("GARMIN_EMAIL") or input("Garmin Connect email: ")
    password = password or os.environ.get("GARMIN_PASSWORD") or getpass.getpass(
        "Garmin Connect password: "
    )

    client = Garmin(email=email, password=password)
    client.login()

    # Save tokens for future use
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    client.garth.dump(token_dir)

    return client
