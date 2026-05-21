"""
Uploads resume DOCX files to Google Drive and returns public shareable links.
Uses OAuth2 for personal Drive access. Credentials are cached in token.json after
the first browser-based authorization flow.
"""

import logging
import os
from pathlib import Path
from datetime import date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _get_credentials(credentials_file: str, token_file: str) -> Credentials:
    creds = None
    token_path = Path(token_file)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(credentials_file).exists():
                raise FileNotFoundError(
                    f"Google credentials file not found at '{credentials_file}'. "
                    "See SETUP.md for instructions on downloading it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())
        logger.info(f"Google Drive token saved to {token_file}")

    return creds


class DriveUploader:
    """
    Stateful uploader. Reuse one instance per run so the Drive service
    client is built once and auth tokens are reused.
    """

    def __init__(self, credentials_file: str, token_file: str, folder_id: str):
        self.folder_id = folder_id
        creds = _get_credentials(credentials_file, token_file)
        self.service = build("drive", "v3", credentials=creds)
        self._daily_folder_id = self._get_or_create_daily_folder()

    def _get_or_create_daily_folder(self) -> str:
        """Get or create a dated subfolder inside the configured Drive folder."""
        folder_name = f"Job Applications {date.today().isoformat()}"
        query = (
            f"name='{folder_name}' and "
            f"'{self.folder_id}' in parents and "
            "mimeType='application/vnd.google-apps.folder' and "
            "trashed=false"
        )
        results = (
            self.service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )
        files = results.get("files", [])
        if files:
            folder_id = files[0]["id"]
            logger.debug(f"Reusing Drive folder: {folder_name}")
            return folder_id

        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [self.folder_id],
        }
        folder = self.service.files().create(body=metadata, fields="id").execute()
        logger.info(f"Created Drive folder: {folder_name}")
        return folder["id"]

    def upload(self, file_path: Path) -> str:
        """
        Upload a DOCX file to the daily Drive folder.
        Sets public read permission and returns the shareable link.
        """
        metadata = {
            "name": file_path.name,
            "parents": [self._daily_folder_id],
        }
        media = MediaFileUpload(str(file_path), mimetype=MIME_DOCX, resumable=False)
        uploaded = (
            self.service.files()
            .create(body=metadata, media_body=media, fields="id")
            .execute()
        )
        file_id = uploaded["id"]

        self.service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        link = f"https://drive.google.com/file/d/{file_id}/view"
        logger.info(f"Uploaded to Drive: {file_path.name} → {link}")
        return link
