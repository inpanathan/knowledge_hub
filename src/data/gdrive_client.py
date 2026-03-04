"""Google Drive API client wrapper.

Handles OAuth 2.0 authentication, folder listing, and file downloads.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from src.utils.errors import AppError, ErrorCode
from src.utils.logger import get_logger

logger = get_logger(__name__)

# MIME types for book formats
BOOK_MIME_TYPES = [
    "application/pdf",
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
]

# Google Docs export MIME type (exported as PDF)
_GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
_GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"


class GoogleDriveClient:
    """Wrapper around Google Drive API v3 for downloading books."""

    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        scopes: list[str],
    ) -> None:
        self._credentials_file = credentials_file
        self._token_file = token_file
        self._scopes = scopes
        self._service: Any = None

    def _get_service(self) -> Any:
        """Authenticate and return the Drive API service, caching the token."""
        if self._service is not None:
            return self._service

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as e:
            raise AppError(
                code=ErrorCode.GDRIVE_AUTH_FAILED,
                message="Google Drive dependencies not installed. Run: uv sync --extra books",
                cause=e,
            ) from e

        creds: Credentials | None = None
        token_path = Path(self._token_file)

        # Load cached token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), self._scopes)

        # Refresh or run consent flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning("token_refresh_failed", error=str(e))
                    creds = None

            if not creds:
                creds_path = Path(self._credentials_file)
                if not creds_path.exists():
                    raise AppError(
                        code=ErrorCode.GDRIVE_AUTH_FAILED,
                        message=f"Credentials file not found: {self._credentials_file}",
                        context={"credentials_file": self._credentials_file},
                    )

                import json

                raw = json.loads(creds_path.read_text())
                if "installed" in raw:
                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), self._scopes)
                    creds = flow.run_local_server(port=0)
                else:
                    # Web credentials — require pre-authenticated token
                    raise AppError(
                        code=ErrorCode.GDRIVE_AUTH_FAILED,
                        message=(
                            "No valid token found. Run: "
                            "uv run python scripts/authenticate_gdrive_console.py"
                        ),
                        context={"token_file": self._token_file},
                    )

            # Save token for next run
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
            logger.info("gdrive_token_saved", path=str(token_path))

        self._service = build("drive", "v3", credentials=creds)
        logger.info("gdrive_service_initialized")
        return self._service

    def list_files(
        self,
        folder_id: str,
        *,
        mime_types: list[str] | None = None,
        recursive: bool = True,
    ) -> list[dict[str, Any]]:
        """List all files in a Drive folder, optionally recursively.

        Returns list of dicts with keys: id, name, mimeType, size, parents, folder_path.
        """
        service = self._get_service()
        allowed_mimes = set(mime_types or BOOK_MIME_TYPES)
        results: list[dict[str, Any]] = []

        self._list_folder(
            service,
            folder_id=folder_id,
            folder_path="",
            allowed_mimes=allowed_mimes,
            recursive=recursive,
            results=results,
        )

        logger.info("gdrive_files_listed", folder_id=folder_id, file_count=len(results))
        return results

    def _list_folder(
        self,
        service: Any,
        *,
        folder_id: str,
        folder_path: str,
        allowed_mimes: set[str],
        recursive: bool,
        results: list[dict[str, Any]],
    ) -> None:
        """Recursively list files in a folder."""
        page_token: str | None = None

        while True:
            try:
                query = f"'{folder_id}' in parents and trashed = false"
                response = (
                    service.files()
                    .list(
                        q=query,
                        fields="nextPageToken, files(id, name, mimeType, size, parents)",
                        pageSize=100,
                        pageToken=page_token,
                    )
                    .execute()
                )
            except Exception as e:
                raise AppError(
                    code=ErrorCode.GDRIVE_DOWNLOAD_FAILED,
                    message=f"Failed to list files in folder: {folder_id}",
                    context={"folder_id": folder_id},
                    cause=e,
                ) from e

            files = response.get("files", [])

            for file_info in files:
                mime = file_info.get("mimeType", "")

                if mime == _GOOGLE_FOLDER_MIME:
                    if recursive:
                        subfolder_name = file_info["name"]
                        subfolder_path = (
                            f"{folder_path}/{subfolder_name}" if folder_path else subfolder_name
                        )
                        self._list_folder(
                            service,
                            folder_id=file_info["id"],
                            folder_path=subfolder_path,
                            allowed_mimes=allowed_mimes,
                            recursive=recursive,
                            results=results,
                        )
                elif mime in allowed_mimes:
                    file_info["folder_path"] = folder_path
                    results.append(file_info)
                else:
                    logger.debug(
                        "gdrive_file_skipped",
                        name=file_info.get("name"),
                        mime_type=mime,
                    )

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    def download_file(
        self,
        file_id: str,
        dest_path: Path,
        *,
        chunk_size: int = 1024 * 1024,
    ) -> None:
        """Stream a Drive file to dest_path."""
        from googleapiclient.http import MediaIoBaseDownload

        service = self._get_service()
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            request = service.files().get_media(fileId=file_id)
            with open(dest_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(
                            "gdrive_download_progress",
                            file_id=file_id,
                            progress=f"{status.progress() * 100:.0f}%",
                        )
        except Exception as e:
            # Clean up partial download
            dest_path.unlink(missing_ok=True)
            raise AppError(
                code=ErrorCode.GDRIVE_DOWNLOAD_FAILED,
                message=f"Failed to download file: {file_id}",
                context={"file_id": file_id, "dest_path": str(dest_path)},
                cause=e,
            ) from e

        logger.info(
            "gdrive_file_downloaded",
            file_id=file_id,
            dest=str(dest_path),
            size_bytes=dest_path.stat().st_size,
        )

    def export_google_doc(
        self,
        file_id: str,
        dest_path: Path,
        *,
        export_mime: str = "application/pdf",
    ) -> None:
        """Export a Google Docs file to the specified format."""
        service = self._get_service()
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            content = io.BytesIO()
            from googleapiclient.http import MediaIoBaseDownload

            downloader = MediaIoBaseDownload(content, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            dest_path.write_bytes(content.getvalue())
        except Exception as e:
            dest_path.unlink(missing_ok=True)
            raise AppError(
                code=ErrorCode.GDRIVE_DOWNLOAD_FAILED,
                message=f"Failed to export Google Doc: {file_id}",
                context={"file_id": file_id},
                cause=e,
            ) from e

        logger.info("gdrive_doc_exported", file_id=file_id, dest=str(dest_path))
