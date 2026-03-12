"""Unit tests for book summarization (map-reduce)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.features.summarization import (
    BookSummaryResult,
    SummarizationService,
)
from src.models.embeddings import MockEmbeddingModel
from src.models.llm import MockLLMClient
from src.utils.cache import InMemoryCacheStore
from src.utils.errors import AppError
from src.utils.vector_store import SearchResult, VectorStore


def _make_chunk(
    book_id: str,
    chapter_number: int,
    chapter_title: str,
    chunk_index: int,
    text: str = "Some content.",
) -> SearchResult:
    """Create a fake SearchResult mimicking a book chunk."""
    return SearchResult(
        chunk_id=f"{book_id}-ch{chapter_number}-{chunk_index}",
        text=text,
        score=0.0,
        metadata={
            "book_id": book_id,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "chunk_index": chunk_index,
        },
    )


@pytest.fixture()
def book_service() -> MagicMock:
    """Mock BookService."""
    svc = MagicMock()
    book = MagicMock()
    book.id = "book-1"
    book.title = "Test Book"
    book.author = "Test Author"
    book.embedding_status = "completed"
    svc.get_book.return_value = book
    return svc


@pytest.fixture()
def summarization_service(
    llm_client: MockLLMClient,
    vector_store: VectorStore,
    embedding_model: MockEmbeddingModel,
    catalog_service: MagicMock | None = None,
    book_service: MagicMock | None = None,
) -> SummarizationService:
    """Create a SummarizationService with mock deps."""
    catalog = catalog_service or MagicMock()
    cache = InMemoryCacheStore()
    return SummarizationService(
        llm_client=llm_client,
        vector_store=vector_store,
        embedding_model=embedding_model,
        catalog=catalog,
        book_service=book_service,
        cache=cache,
    )


def _seed_book_chunks(vector_store: VectorStore, embedding_model: MockEmbeddingModel) -> None:
    """Seed the vector store with book chunks across two chapters."""
    collection = "test_books"
    vector_store.ensure_books_collection(collection, 384)

    chunks_ch1 = [
        (
            "book-1-ch1-0",
            "Chapter 1 content part 1.",
            {
                "book_id": "book-1",
                "chapter_number": 1,
                "chapter_title": "Introduction",
                "chunk_index": 0,
            },
        ),
        (
            "book-1-ch1-1",
            "Chapter 1 content part 2.",
            {
                "book_id": "book-1",
                "chapter_number": 1,
                "chapter_title": "Introduction",
                "chunk_index": 1,
            },
        ),
    ]
    chunks_ch2 = [
        (
            "book-1-ch2-0",
            "Chapter 2 content part 1.",
            {
                "book_id": "book-1",
                "chapter_number": 2,
                "chapter_title": "Methods",
                "chunk_index": 0,
            },
        ),
    ]

    all_chunks = chunks_ch1 + chunks_ch2
    chunk_ids = [c[0] for c in all_chunks]
    documents = [c[1] for c in all_chunks]
    metadatas = [c[2] for c in all_chunks]
    embeddings = [embedding_model.embed_query(d) for d in documents]

    vector_store.add_book_chunks(
        collection_name=collection,
        book_id="book-1",
        chunk_ids=chunk_ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def test_summarize_book_basic(
    llm_client: MockLLMClient,
    vector_store: VectorStore,
    embedding_model: MockEmbeddingModel,
    book_service: MagicMock,
) -> None:
    """Test basic book summarization returns structured result."""
    _seed_book_chunks(vector_store, embedding_model)

    # Override the books collection name in settings
    from unittest.mock import patch

    with patch("src.features.summarization.settings") as mock_settings:
        mock_settings.books.qdrant_collection = "test_books"
        mock_settings.rag.max_context_tokens = 4000

        svc = SummarizationService(
            llm_client=llm_client,
            vector_store=vector_store,
            embedding_model=embedding_model,
            catalog=MagicMock(),
            book_service=book_service,
            cache=InMemoryCacheStore(),
        )

        result = svc.summarize_book("book-1")

    assert isinstance(result, BookSummaryResult)
    assert result.book_id == "book-1"
    assert result.book_title == "Test Book"
    assert result.author == "Test Author"
    assert len(result.chapters) == 2
    assert result.chapters[0].chapter_number == 1
    assert result.chapters[0].chapter_title == "Introduction"
    assert result.chapters[1].chapter_number == 2
    assert result.chapters[1].chapter_title == "Methods"
    assert result.total_chunks_processed == 3
    assert result.total_llm_calls > 0
    assert len(result.overall_summary) > 0


def test_no_book_service_raises(
    llm_client: MockLLMClient,
    vector_store: VectorStore,
    embedding_model: MockEmbeddingModel,
) -> None:
    """Test that summarize_book raises when book_service is not provided."""
    svc = SummarizationService(
        llm_client=llm_client,
        vector_store=vector_store,
        embedding_model=embedding_model,
        catalog=MagicMock(),
    )

    with pytest.raises(AppError) as exc_info:
        svc.summarize_book("book-1")
    assert exc_info.value.code.value == "INTERNAL_ERROR"


def test_not_embedded_raises(
    llm_client: MockLLMClient,
    vector_store: VectorStore,
    embedding_model: MockEmbeddingModel,
) -> None:
    """Test that summarize_book raises for non-embedded books."""
    book_svc = MagicMock()
    book = MagicMock()
    book.embedding_status = "pending"
    book_svc.get_book.return_value = book

    svc = SummarizationService(
        llm_client=llm_client,
        vector_store=vector_store,
        embedding_model=embedding_model,
        catalog=MagicMock(),
        book_service=book_svc,
    )

    with pytest.raises(AppError) as exc_info:
        svc.summarize_book("book-1")
    assert exc_info.value.code.value == "VALIDATION_ERROR"


def test_chapter_batching() -> None:
    """Test that _batch_texts correctly splits texts by budget."""
    texts = ["a" * 5000, "b" * 5000, "c" * 5000]
    batches = SummarizationService._batch_texts(texts, 10_100)

    # First batch fits 2 texts (5002 + 5002 = 10004 <= 10100)
    # Second batch gets the third
    assert len(batches) == 2
    assert len(batches[0]) == 2
    assert len(batches[1]) == 1


def test_cache_hit(
    llm_client: MockLLMClient,
    vector_store: VectorStore,
    embedding_model: MockEmbeddingModel,
    book_service: MagicMock,
) -> None:
    """Test that cached results are returned without LLM calls."""
    cache = InMemoryCacheStore()
    cache.set(
        "book_summary:book-1:detailed",
        {
            "book_id": "book-1",
            "book_title": "Cached Book",
            "author": "Cached Author",
            "overall_summary": "Cached summary",
            "chapters": [
                {
                    "chapter_number": 1,
                    "chapter_title": "Ch1",
                    "summary": "Ch1 summary",
                    "chunk_count": 5,
                },
            ],
            "total_chunks_processed": 5,
            "total_llm_calls": 3,
        },
    )

    svc = SummarizationService(
        llm_client=llm_client,
        vector_store=vector_store,
        embedding_model=embedding_model,
        catalog=MagicMock(),
        book_service=book_service,
        cache=cache,
    )

    result = svc.summarize_book("book-1")
    assert result.book_title == "Cached Book"
    assert result.overall_summary == "Cached summary"
    assert len(result.chapters) == 1
