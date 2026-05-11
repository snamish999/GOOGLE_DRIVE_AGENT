"""
drive_service.py
────────────────
Handles Google Drive API authentication and all file-search operations.
Uses a Service Account so no OAuth browser flow is needed.
"""

from __future__ import annotations

import os
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Drive API scopes — read-only is enough for searching
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# MIME type friendly names for display
MIME_LABELS: dict[str, str] = {
    "application/vnd.google-apps.document": "Google Doc",
    "application/vnd.google-apps.spreadsheet": "Google Sheet",
    "application/vnd.google-apps.presentation": "Google Slide",
    "application/vnd.google-apps.folder": "Folder",
    "application/pdf": "PDF",
    "image/png": "PNG Image",
    "image/jpeg": "JPEG Image",
    "image/gif": "GIF Image",
    "text/plain": "Text File",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
}


def _get_drive_service():
    """Build and return an authenticated Google Drive API service."""
    service_account_file = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE", "../credentials/service_account.json"
    )
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def search_drive_files(query: str, max_results: int = 15) -> list[dict[str, Any]]:
    """
    Execute a Google Drive files.list query and return formatted results.

    Args:
        query:       A valid Google Drive API q-parameter string.
                     e.g. "name contains 'report' and mimeType='application/pdf'"
        max_results: Maximum number of files to return (default 15).

    Returns:
        List of dicts with keys: id, name, mimeType, mimeLabel,
        modifiedTime, size, webViewLink, iconLink
    """
    service = _get_drive_service()
    folder_id = os.getenv("DRIVE_FOLDER_ID", "")

    # Always scope the search to the configured folder (and its children)
    folder_clause = f"'{folder_id}' in parents" if folder_id else ""
    trash_clause = "trashed = false"

    if query.strip():
        full_query = f"({query}) and {trash_clause}"
        if folder_clause:
            full_query = f"{folder_clause} and {full_query}"
    else:
        full_query = trash_clause
        if folder_clause:
            full_query = f"{folder_clause} and {full_query}"

    try:
        response = (
            service.files()
            .list(
                q=full_query,
                pageSize=max_results,
                fields=(
                    "files(id, name, mimeType, modifiedTime, "
                    "size, webViewLink, iconLink, description)"
                ),
                orderBy="modifiedTime desc",
            )
            .execute()
        )
    except HttpError as e:
        raise RuntimeError(f"Google Drive API error: {e}") from e

    files = response.get("files", [])
    results = []
    for f in files:
        mime = f.get("mimeType", "")
        results.append(
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "mimeType": mime,
                "mimeLabel": MIME_LABELS.get(mime, mime.split("/")[-1].capitalize()),
                "modifiedTime": f.get("modifiedTime"),
                "size": f.get("size"),
                "webViewLink": f.get("webViewLink"),
                "iconLink": f.get("iconLink"),
                "description": f.get("description", ""),
            }
        )
    return results
