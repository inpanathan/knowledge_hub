"""Pydantic models for the book catalog."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EmbeddingStatus(StrEnum):
    """Embedding pipeline status for a book."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GraphStatus(StrEnum):
    """Knowledge graph construction status for a book."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Book(BaseModel):
    """A single book entry in the catalog."""

    id: str
    title: str
    author: str = ""
    isbn: str = ""
    publisher: str = ""
    publication_year: int | None = None
    language: str = "en"
    page_count: int | None = None

    # File info
    file_format: str = ""
    file_size_bytes: int = 0
    file_hash: str = ""
    file_path: str = ""
    cover_image_path: str = ""

    # Enriched metadata
    description: str = ""
    table_of_contents: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Drive provenance
    drive_folder_path: str = ""
    drive_file_id: str = ""

    # Timestamps + pipeline status
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    processed_at: datetime | None = None
    embedding_status: EmbeddingStatus = EmbeddingStatus.PENDING
    graph_status: GraphStatus = GraphStatus.SKIPPED

    # Link to sources table (populated in Phase 2)
    source_id: str | None = None


class BookCreate(BaseModel):
    """Input for creating a book catalog entry."""

    title: str
    author: str = ""
    isbn: str = ""
    publisher: str = ""
    publication_year: int | None = None
    language: str = "en"
    page_count: int | None = None
    file_format: str = ""
    file_size_bytes: int = 0
    file_hash: str = ""
    file_path: str = ""
    cover_image_path: str = ""
    description: str = ""
    table_of_contents: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    drive_folder_path: str = ""
    drive_file_id: str = ""


class BookUpdate(BaseModel):
    """Fields that can be updated via API."""

    title: str | None = None
    author: str | None = None
    tags: list[str] | None = None
    description: str | None = None


class BookSummary(BaseModel):
    """Lightweight book info for list views."""

    id: str
    title: str
    author: str
    file_format: str
    publication_year: int | None
    cover_image_path: str
    tags: list[str]
    embedding_status: EmbeddingStatus


class BookListResponse(BaseModel):
    """Paginated book list response."""

    books: list[BookSummary]
    total: int
