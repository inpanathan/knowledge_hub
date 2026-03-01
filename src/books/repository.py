"""SQLite-backed repository for the book catalog."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.books.models import Book, EmbeddingStatus, GraphStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    isbn TEXT DEFAULT '',
    publisher TEXT DEFAULT '',
    publication_year INTEGER,
    language TEXT DEFAULT 'en',
    page_count INTEGER,
    file_format TEXT DEFAULT '',
    file_size_bytes INTEGER DEFAULT 0,
    file_hash TEXT DEFAULT '',
    file_path TEXT DEFAULT '',
    cover_image_path TEXT DEFAULT '',
    description TEXT DEFAULT '',
    table_of_contents TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    drive_folder_path TEXT DEFAULT '',
    drive_file_id TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    processed_at TEXT,
    embedding_status TEXT DEFAULT 'pending',
    graph_status TEXT DEFAULT 'skipped',
    source_id TEXT
);
"""


class BookRepository:
    """CRUD operations for the book catalog backed by SQLite."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()
        logger.info("books_db_initialized", path=self._db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_book(self, row: sqlite3.Row) -> Book:
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"] or "",
            isbn=row["isbn"] or "",
            publisher=row["publisher"] or "",
            publication_year=row["publication_year"],
            language=row["language"] or "en",
            page_count=row["page_count"],
            file_format=row["file_format"] or "",
            file_size_bytes=row["file_size_bytes"] or 0,
            file_hash=row["file_hash"] or "",
            file_path=row["file_path"] or "",
            cover_image_path=row["cover_image_path"] or "",
            description=row["description"] or "",
            table_of_contents=(
                json.loads(row["table_of_contents"]) if row["table_of_contents"] else []
            ),
            tags=json.loads(row["tags"]) if row["tags"] else [],
            drive_folder_path=row["drive_folder_path"] or "",
            drive_file_id=row["drive_file_id"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            processed_at=(
                datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None
            ),
            embedding_status=EmbeddingStatus(row["embedding_status"]),
            graph_status=GraphStatus(row["graph_status"]),
            source_id=row["source_id"],
        )

    def create(self, book: Book) -> Book:
        """Insert a new book."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO books
                   (id, title, author, isbn, publisher, publication_year, language,
                    page_count, file_format, file_size_bytes, file_hash, file_path,
                    cover_image_path, description, table_of_contents, tags,
                    drive_folder_path, drive_file_id, created_at, processed_at,
                    embedding_status, graph_status, source_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    book.id,
                    book.title,
                    book.author,
                    book.isbn,
                    book.publisher,
                    book.publication_year,
                    book.language,
                    book.page_count,
                    book.file_format,
                    book.file_size_bytes,
                    book.file_hash,
                    book.file_path,
                    book.cover_image_path,
                    book.description,
                    json.dumps(book.table_of_contents),
                    json.dumps(book.tags),
                    book.drive_folder_path,
                    book.drive_file_id,
                    book.created_at.isoformat(),
                    book.processed_at.isoformat() if book.processed_at else None,
                    book.embedding_status.value,
                    book.graph_status.value,
                    book.source_id,
                ),
            )
            conn.commit()
        logger.info("book_created", book_id=book.id, title=book.title)
        return book

    def get(self, book_id: str) -> Book | None:
        """Get a book by ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_book(row)

    def list_books(
        self,
        *,
        author: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        embedding_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Book], int]:
        """List books with optional filters. Returns (books, total_count)."""
        conditions: list[str] = []
        params: list[str | int] = []

        if author:
            conditions.append("author LIKE ?")
            params.append(f"%{author}%")
        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")
        if search:
            conditions.append("(title LIKE ? OR author LIKE ? OR description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        if embedding_status:
            conditions.append("embedding_status = ?")
            params.append(embedding_status)

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._connect() as conn:
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM books{where}",  # noqa: S608
                params,
            ).fetchone()
            total = count_row["cnt"] if count_row else 0

            rows = conn.execute(
                f"SELECT * FROM books{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",  # noqa: S608
                [*params, limit, offset],
            ).fetchall()

        return [self._row_to_book(r) for r in rows], total

    def update(self, book_id: str, **fields: object) -> Book | None:
        """Update specific fields on a book."""
        if not fields:
            return self.get(book_id)

        set_clauses: list[str] = []
        params: list[object] = []
        for key, value in fields.items():
            if key in ("tags", "table_of_contents") and isinstance(value, list):
                set_clauses.append(f"{key} = ?")
                params.append(json.dumps(value))
            elif key in ("created_at", "processed_at") and isinstance(value, datetime):
                set_clauses.append(f"{key} = ?")
                params.append(value.isoformat())
            else:
                set_clauses.append(f"{key} = ?")
                params.append(value)

        params.append(book_id)

        with self._connect() as conn:
            conn.execute(
                f"UPDATE books SET {', '.join(set_clauses)} WHERE id = ?",  # noqa: S608
                params,
            )
            conn.commit()

        return self.get(book_id)

    def delete(self, book_id: str) -> bool:
        """Delete a book. Returns True if a row was deleted."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("book_deleted", book_id=book_id)
        return deleted

    def find_by_hash(self, file_hash: str) -> Book | None:
        """Find a book by its file hash for duplicate detection."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM books WHERE file_hash = ?", (file_hash,)).fetchone()
        if row is None:
            return None
        return self._row_to_book(row)

    def find_by_drive_file_id(self, drive_file_id: str) -> Book | None:
        """Find a book by its Google Drive file ID for idempotent re-runs."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM books WHERE drive_file_id = ?", (drive_file_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_book(row)
