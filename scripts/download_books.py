"""Download books from Google Drive and catalog them.

Usage:
    uv run python scripts/download_books.py [--folder-id FOLDER_ID] [--dry-run]

Requires: uv sync --extra books
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

# Resolve PROJECT_ROOT before app imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.books.models import BookCreate  # noqa: E402
from src.books.repository import BookRepository  # noqa: E402
from src.books.service import BookService  # noqa: E402
from src.data.book_metadata import extract_cover_image, extract_metadata  # noqa: E402
from src.data.gdrive_client import GoogleDriveClient  # noqa: E402
from src.utils.config import settings  # noqa: E402
from src.utils.logger import get_logger, setup_logging  # noqa: E402

logger = get_logger(__name__)


def _sanitize_filename(name: str) -> str:
    """Replace unsafe characters in a filename; preserve extension."""
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    safe = re.sub(r"[^\w\s\-.]", "", stem).strip().replace(" ", "_")
    if not safe:
        safe = "untitled"
    return f"{safe}{suffix}"


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main() -> int:
    """Download books from Google Drive and catalog them."""
    parser = argparse.ArgumentParser(description="Download books from Google Drive")
    parser.add_argument(
        "--folder-id",
        default=settings.google_drive.folder_id,
        help="Google Drive folder ID (overrides GOOGLE_DRIVE__FOLDER_ID)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without downloading",
    )
    args = parser.parse_args()

    setup_logging(level=settings.logging.level, fmt=settings.logging.format)

    folder_id = args.folder_id
    if not folder_id:
        logger.error("no_folder_id", message="GOOGLE_DRIVE__FOLDER_ID is required")
        return 1

    # Initialize services
    gdrive = GoogleDriveClient(
        credentials_file=settings.google_drive.credentials_file,
        token_file=settings.google_drive.token_file,
        scopes=settings.google_drive.scopes,
    )
    book_repo = BookRepository(settings.books.database_path)
    book_service = BookService(book_repo)

    storage_dir = Path(settings.books.storage_dir)
    covers_dir = Path(settings.books.covers_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    covers_dir.mkdir(parents=True, exist_ok=True)

    # List files from Drive
    logger.info("listing_drive_files", folder_id=folder_id)
    files = gdrive.list_files(folder_id, recursive=True)
    logger.info("drive_files_found", count=len(files))

    if not files:
        logger.info("no_files_found", folder_id=folder_id)
        return 0

    # Process each file
    downloaded = 0
    skipped = 0
    failed = 0

    for file_info in files:
        file_id = file_info["id"]
        file_name = file_info["name"]
        folder_path = file_info.get("folder_path", "")
        file_size = int(file_info.get("size", 0))

        if args.dry_run:
            logger.info(
                "dry_run_file",
                name=file_name,
                folder=folder_path,
                size_bytes=file_size,
                drive_id=file_id,
            )
            continue

        # Check if already downloaded (idempotent)
        existing = book_service.find_by_drive_file_id(file_id)
        if existing:
            logger.info("book_already_cataloged", name=file_name, book_id=existing.id)
            skipped += 1
            continue

        # Compute destination path
        safe_name = _sanitize_filename(file_name)
        if folder_path:
            dest_dir = storage_dir / folder_path
        else:
            dest_dir = storage_dir
        dest_path = dest_dir / safe_name

        # Handle name collisions
        counter = 1
        while dest_path.exists():
            stem = Path(safe_name).stem
            suffix = Path(safe_name).suffix
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        try:
            # Download
            logger.info("downloading_book", name=file_name, dest=str(dest_path))
            gdrive.download_file(file_id, dest_path)

            # Compute hash and check for content duplicates
            file_hash = _compute_file_hash(dest_path)
            duplicate = book_service.find_duplicate(file_hash)
            if duplicate:
                logger.warning(
                    "duplicate_content_detected",
                    name=file_name,
                    duplicate_of=duplicate.title,
                )
                dest_path.unlink(missing_ok=True)
                skipped += 1
                continue

            # Extract metadata
            metadata = extract_metadata(dest_path)

            # Extract cover image
            cover_path = extract_cover_image(dest_path, covers_dir, file_hash[:12])

            # Create book catalog entry
            suffix = dest_path.suffix.lstrip(".").lower()
            book_data = BookCreate(
                title=metadata.get("title", file_name) or file_name,
                author=metadata.get("author", "") or "",
                isbn=metadata.get("isbn", "") or "",
                publisher=metadata.get("publisher", "") or "",
                publication_year=metadata.get("publication_year"),
                language=metadata.get("language", "") or "",
                page_count=metadata.get("page_count"),
                file_format=suffix,
                file_size_bytes=dest_path.stat().st_size,
                file_hash=file_hash,
                file_path=str(dest_path),
                cover_image_path=cover_path,
                description=metadata.get("description", "") or "",
                table_of_contents=metadata.get("table_of_contents", []) or [],
                tags=[],
                drive_folder_path=folder_path,
                drive_file_id=file_id,
            )

            book = book_service.create_book(book_data)
            book_service.mark_processed(book.id, processed_at=datetime.now(tz=UTC))

            logger.info(
                "book_cataloged",
                book_id=book.id,
                title=book.title,
                author=book.author,
                format=suffix,
                size_bytes=book_data.file_size_bytes,
            )
            downloaded += 1

        except Exception as e:
            logger.error(
                "book_download_failed",
                name=file_name,
                error=str(e),
            )
            failed += 1

    # Summary
    total = len(files)
    logger.info(
        "download_summary",
        total_files=total,
        downloaded=downloaded,
        skipped=skipped,
        failed=failed,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        for f in files:
            size_mb = int(f.get("size", 0)) / (1024 * 1024)
            folder = f.get("folder_path", "")
            loc = f"{folder}/{f['name']}" if folder else f["name"]
            # Use sys.stdout since this is a CLI script, not src/
            sys.stdout.write(f"  {loc}  ({size_mb:.1f} MB)\n")
        sys.stdout.write(f"\nTotal: {total} files\n")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
