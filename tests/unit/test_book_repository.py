"""Unit tests for BookRepository CRUD operations."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.books.models import Book, EmbeddingStatus, GraphStatus
from src.books.repository import BookRepository


@pytest.fixture()
def book_repo(tmp_dir: Path) -> BookRepository:
    """Provide a BookRepository with an isolated SQLite database."""
    return BookRepository(str(tmp_dir / "test_books.db"))


def _make_book(**overrides: object) -> Book:
    """Create a Book with sensible defaults, overriding any fields."""
    defaults = {
        "id": "book-001",
        "title": "Test Book",
        "author": "Test Author",
        "file_format": "pdf",
        "file_hash": "abc123hash",
        "file_path": "/tmp/test.pdf",
        "drive_file_id": "gdrive-001",
    }
    defaults.update(overrides)
    return Book(**defaults)


def test_create_and_get(book_repo: BookRepository) -> None:
    book = _make_book()
    created = book_repo.create(book)
    assert created.id == "book-001"

    fetched = book_repo.get("book-001")
    assert fetched is not None
    assert fetched.title == "Test Book"
    assert fetched.author == "Test Author"


def test_get_returns_none_for_missing(book_repo: BookRepository) -> None:
    assert book_repo.get("nonexistent") is None


def test_list_empty(book_repo: BookRepository) -> None:
    books, total = book_repo.list_books()
    assert books == []
    assert total == 0


def test_list_with_books(book_repo: BookRepository) -> None:
    book_repo.create(_make_book(id="b1", title="Alpha"))
    book_repo.create(_make_book(id="b2", title="Beta"))

    books, total = book_repo.list_books()
    assert total == 2
    assert len(books) == 2


def test_list_search_filter(book_repo: BookRepository) -> None:
    book_repo.create(_make_book(id="b1", title="Python Crash Course", author="Eric Matthes"))
    book_repo.create(_make_book(id="b2", title="Clean Code", author="Robert Martin"))

    books, total = book_repo.list_books(search="Python")
    assert total == 1
    assert books[0].title == "Python Crash Course"


def test_list_author_filter(book_repo: BookRepository) -> None:
    book_repo.create(_make_book(id="b1", author="Alice"))
    book_repo.create(_make_book(id="b2", author="Bob"))

    books, total = book_repo.list_books(author="Alice")
    assert total == 1
    assert books[0].author == "Alice"


def test_list_embedding_status_filter(book_repo: BookRepository) -> None:
    b1 = _make_book(id="b1", embedding_status=EmbeddingStatus.COMPLETED)
    b2 = _make_book(id="b2", embedding_status=EmbeddingStatus.PENDING)
    book_repo.create(b1)
    book_repo.create(b2)

    books, total = book_repo.list_books(embedding_status="completed")
    assert total == 1
    assert books[0].id == "b1"


def test_list_pagination(book_repo: BookRepository) -> None:
    for i in range(5):
        book_repo.create(_make_book(id=f"b{i}", title=f"Book {i}"))

    books, total = book_repo.list_books(limit=2, offset=0)
    assert total == 5
    assert len(books) == 2


def test_update(book_repo: BookRepository) -> None:
    book_repo.create(_make_book())
    updated = book_repo.update("book-001", title="Updated Title", author="New Author")
    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.author == "New Author"


def test_update_tags(book_repo: BookRepository) -> None:
    book_repo.create(_make_book())
    updated = book_repo.update("book-001", tags=["python", "programming"])
    assert updated is not None
    assert updated.tags == ["python", "programming"]


def test_delete(book_repo: BookRepository) -> None:
    book_repo.create(_make_book())
    assert book_repo.delete("book-001") is True
    assert book_repo.get("book-001") is None


def test_delete_nonexistent(book_repo: BookRepository) -> None:
    assert book_repo.delete("nonexistent") is False


def test_find_by_hash(book_repo: BookRepository) -> None:
    book_repo.create(_make_book(file_hash="deadbeef"))
    found = book_repo.find_by_hash("deadbeef")
    assert found is not None
    assert found.file_hash == "deadbeef"


def test_find_by_hash_returns_none(book_repo: BookRepository) -> None:
    assert book_repo.find_by_hash("nonexistent") is None


def test_find_by_drive_file_id(book_repo: BookRepository) -> None:
    book_repo.create(_make_book(drive_file_id="gdrive-xyz"))
    found = book_repo.find_by_drive_file_id("gdrive-xyz")
    assert found is not None
    assert found.drive_file_id == "gdrive-xyz"


def test_find_by_drive_file_id_returns_none(book_repo: BookRepository) -> None:
    assert book_repo.find_by_drive_file_id("nonexistent") is None


def test_json_fields_roundtrip(book_repo: BookRepository) -> None:
    """Verify table_of_contents and tags survive JSON serialization."""
    book = _make_book(
        table_of_contents=["Chapter 1", "Chapter 2"],
        tags=["python", "ml"],
    )
    book_repo.create(book)
    fetched = book_repo.get("book-001")
    assert fetched is not None
    assert fetched.table_of_contents == ["Chapter 1", "Chapter 2"]
    assert fetched.tags == ["python", "ml"]


def test_enum_fields_roundtrip(book_repo: BookRepository) -> None:
    """Verify embedding_status and graph_status enums survive roundtrip."""
    book = _make_book(
        embedding_status=EmbeddingStatus.COMPLETED,
        graph_status=GraphStatus.PROCESSING,
    )
    book_repo.create(book)
    fetched = book_repo.get("book-001")
    assert fetched is not None
    assert fetched.embedding_status == EmbeddingStatus.COMPLETED
    assert fetched.graph_status == GraphStatus.PROCESSING


def test_table_coexistence_with_sources(tmp_dir: Path) -> None:
    """Verify books and sources tables can coexist in the same SQLite file."""
    from src.catalog.repository import CatalogRepository

    db_path = str(tmp_dir / "shared.db")
    catalog_repo = CatalogRepository(db_path)
    book_repo = BookRepository(db_path)

    # Both repos should work independently
    books, _ = book_repo.list_books()
    assert books == []

    sources, total = catalog_repo.list_sources()
    assert total == 0
