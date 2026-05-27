"""Google Sheets sync for family contacts.

This module pushes the local contacts (the source of truth) up to a Google
Sheet titled "Peaslee Family Contacts" so the family has a friendly,
human-readable mirror they can open in a browser.

Credentials
-----------
Programmatic Google Sheets access needs a credential. This code supports a
Google **service account** JSON key (the simplest option for an automated tool).

Resolution order for the credential path:
  1. The ``GOOGLE_SHEETS_CREDENTIALS`` environment variable, if set.
  2. ``credentials.json`` in the project root.

Both of those paths are gitignored so secrets never get committed.

See the README ("Enabling Google Sheet sync") for the exact steps to create
the credential.
"""

from __future__ import annotations

import os
from typing import List, Optional

from .store import SHEET_HEADERS, Contact

SHEET_TITLE = "Peaslee Family Contacts"

# Scopes needed to create and edit a spreadsheet and find it in Drive.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SyncError(RuntimeError):
    """Raised when sync cannot proceed (missing creds, missing lib, etc.)."""


def resolve_credentials_path(explicit: Optional[str] = None) -> Optional[str]:
    """Return the path to the credentials file, or None if not found."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    env_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if env_path:
        candidates.append(env_path)
    # Project root (one level up from this package).
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(project_root, "credentials.json"))

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def _open_client(credentials_path: str):
    """Authorize a gspread client using a service account key.

    Imports are done lazily so the rest of the CLI works without the Google
    libraries installed.
    """
    try:
        import gspread  # type: ignore
        from google.oauth2.service_account import Credentials  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on env
        raise SyncError(
            "Google libraries are not installed. Install them with:\n"
            "    pip install -r requirements.txt\n"
            "(or: pip install gspread google-auth)"
        ) from exc

    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_or_create_spreadsheet(client, share_with: Optional[str]):
    """Open the spreadsheet by title, creating and sharing it if needed."""
    try:
        return client.open(SHEET_TITLE)
    except Exception:
        spreadsheet = client.create(SHEET_TITLE)
        # A service account owns files it creates; share with a human so the
        # family can actually open the sheet in their browser.
        if share_with:
            try:
                spreadsheet.share(share_with, perm_type="user", role="writer")
            except Exception:
                pass
        return spreadsheet


def push(
    contacts: List[Contact],
    credentials_path: Optional[str] = None,
    share_with: Optional[str] = "clara@peaslee.co",
) -> str:
    """Push contacts to the Google Sheet. Returns the spreadsheet URL.

    Raises SyncError if credentials are missing or the Google libs aren't
    installed, so the caller can show a clear message.
    """
    cred_path = resolve_credentials_path(credentials_path)
    if not cred_path:
        raise SyncError(
            "No Google credentials found.\n"
            "Provide a service account JSON at ./credentials.json or set the\n"
            "GOOGLE_SHEETS_CREDENTIALS environment variable. See the README\n"
            "section 'Enabling Google Sheet sync' for setup steps."
        )

    client = _open_client(cred_path)
    spreadsheet = _get_or_create_spreadsheet(client, share_with)
    worksheet = spreadsheet.sheet1

    rows = [SHEET_HEADERS] + [c.to_row() for c in contacts]
    worksheet.clear()
    worksheet.update("A1", rows, value_input_option="USER_ENTERED")

    # Bold the header row for readability. Best-effort only.
    try:
        worksheet.format("A1:G1", {"textFormat": {"bold": True}})
    except Exception:
        pass

    return spreadsheet.url
