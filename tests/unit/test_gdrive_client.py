"""Unit tests for GoogleDriveClient (mocked Google API calls)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.data.gdrive_client import GoogleDriveClient
from src.utils.errors import AppError, ErrorCode


@pytest.fixture()
def gdrive_client() -> GoogleDriveClient:
    """Create a GoogleDriveClient with dummy credentials paths."""
    return GoogleDriveClient(
        credentials_file="configs/test_creds.json",
        token_file="data/test_token.json",
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )


@patch.object(GoogleDriveClient, "_get_service")
def test_list_files_returns_file_info(
    mock_get_svc: MagicMock, gdrive_client: GoogleDriveClient
) -> None:
    """list_files returns a list of file dicts from Drive."""
    mock_service = MagicMock()
    mock_get_svc.return_value = mock_service

    mock_service.files.return_value.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "f1",
                "name": "book1.pdf",
                "mimeType": "application/pdf",
                "size": "1024",
            },
            {
                "id": "f2",
                "name": "book2.epub",
                "mimeType": "application/epub+zip",
                "size": "2048",
            },
        ],
        "nextPageToken": None,
    }

    files = gdrive_client.list_files("test-folder-id")
    assert len(files) == 2
    assert files[0]["id"] == "f1"
    assert files[1]["name"] == "book2.epub"


@patch.object(GoogleDriveClient, "_get_service")
def test_list_files_empty_folder(mock_get_svc: MagicMock, gdrive_client: GoogleDriveClient) -> None:
    """list_files returns empty list for empty folder."""
    mock_service = MagicMock()
    mock_get_svc.return_value = mock_service

    mock_service.files.return_value.list.return_value.execute.return_value = {
        "files": [],
        "nextPageToken": None,
    }

    files = gdrive_client.list_files("empty-folder-id")
    assert files == []


@patch.object(GoogleDriveClient, "_get_service")
def test_list_files_skips_unsupported_mimes(
    mock_get_svc: MagicMock, gdrive_client: GoogleDriveClient
) -> None:
    """list_files skips files with unsupported MIME types."""
    mock_service = MagicMock()
    mock_get_svc.return_value = mock_service

    mock_service.files.return_value.list.return_value.execute.return_value = {
        "files": [
            {"id": "f1", "name": "book.pdf", "mimeType": "application/pdf", "size": "1024"},
            {"id": "f2", "name": "image.png", "mimeType": "image/png", "size": "512"},
        ],
        "nextPageToken": None,
    }

    files = gdrive_client.list_files("folder-id")
    assert len(files) == 1
    assert files[0]["name"] == "book.pdf"


@patch.object(GoogleDriveClient, "_get_service")
def test_download_file_calls_api(
    mock_get_svc: MagicMock,
    gdrive_client: GoogleDriveClient,
    tmp_dir: Path,
) -> None:
    """download_file invokes get_media and streams to dest_path."""
    mock_service = MagicMock()
    mock_get_svc.return_value = mock_service

    dest = tmp_dir / "downloaded.pdf"

    # Create a mock for MediaIoBaseDownload that we inject via sys.modules
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.return_value = (
        MagicMock(progress=MagicMock(return_value=1.0)),
        True,
    )

    mock_dl_cls = MagicMock(return_value=mock_downloader)

    # Patch the local import inside download_file
    import sys
    from types import ModuleType

    mock_http_module = ModuleType("googleapiclient.http")
    mock_http_module.MediaIoBaseDownload = mock_dl_cls  # type: ignore[attr-defined]

    orig = sys.modules.get("googleapiclient.http")
    sys.modules["googleapiclient.http"] = mock_http_module
    try:
        gdrive_client.download_file("file-id", dest)
    finally:
        if orig is not None:
            sys.modules["googleapiclient.http"] = orig
        else:
            sys.modules.pop("googleapiclient.http", None)

    mock_service.files.return_value.get_media.assert_called_once_with(fileId="file-id")
    mock_dl_cls.assert_called_once()


@patch.object(GoogleDriveClient, "_get_service")
def test_list_files_api_error_raises_app_error(
    mock_get_svc: MagicMock, gdrive_client: GoogleDriveClient
) -> None:
    """API errors during list are wrapped in AppError."""
    mock_service = MagicMock()
    mock_get_svc.return_value = mock_service

    mock_service.files.return_value.list.return_value.execute.side_effect = RuntimeError(
        "API unavailable"
    )

    with pytest.raises(AppError) as exc_info:
        gdrive_client.list_files("folder-id")
    assert exc_info.value.code == ErrorCode.GDRIVE_DOWNLOAD_FAILED
