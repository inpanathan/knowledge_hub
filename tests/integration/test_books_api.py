"""Integration tests for the books API endpoints."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.books.models import BookCreate
from src.books.service import BookService


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Create a lifespan-aware test client with isolated data directories."""
    from main import create_app
    from src.utils.config import settings

    with tempfile.TemporaryDirectory() as tmp:
        settings.catalog.database_path = f"{tmp}/catalog.db"
        settings.books.database_path = f"{tmp}/catalog.db"
        settings.file_store.base_directory = f"{tmp}/originals"
        settings.books.storage_dir = f"{tmp}/books/"
        settings.books.covers_dir = f"{tmp}/covers/"

        app = create_app()
        with TestClient(app) as c:
            yield c


def _seed_book(client: TestClient) -> str:
    """Seed one book directly via the service and return its ID."""
    from src.api.dependencies import get_container

    container = get_container()
    book_service: BookService = container.books
    book = book_service.create_book(
        BookCreate(
            title="Test Book",
            author="Test Author",
            file_format="pdf",
            file_size_bytes=1024,
            file_hash="testhash123",
            file_path="/tmp/test.pdf",
            tags=["python", "testing"],
        )
    )
    return book.id


def test_list_books_empty(client: TestClient) -> None:
    response = client.get("/api/v1/books")
    assert response.status_code == 200
    data = response.json()
    assert data["books"] == []
    assert data["total"] == 0


def test_list_books_with_data(client: TestClient) -> None:
    _seed_book(client)
    response = client.get("/api/v1/books")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["books"][0]["title"] == "Test Book"
    assert data["books"][0]["author"] == "Test Author"


def test_get_book(client: TestClient) -> None:
    book_id = _seed_book(client)
    response = client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["file_format"] == "pdf"
    assert data["tags"] == ["python", "testing"]


def test_get_book_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/books/nonexistent-id")
    assert response.status_code == 404


def test_update_book(client: TestClient) -> None:
    book_id = _seed_book(client)
    response = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Updated Title", "author": "New Author"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["author"] == "New Author"


def test_delete_book(client: TestClient) -> None:
    book_id = _seed_book(client)
    response = client.delete(f"/api/v1/books/{book_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 404


def test_list_books_search_filter(client: TestClient) -> None:
    _seed_book(client)
    response = client.get("/api/v1/books?search=Test")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/books?search=nonexistent")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_books_service_in_container(client: TestClient) -> None:
    """Verify the books service is properly wired into the container."""
    from src.api.dependencies import get_container

    container = get_container()
    assert container.books is not None
    assert isinstance(container.books, BookService)
