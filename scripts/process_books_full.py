"""Process all books: embedding + knowledge graph, one by one.

Runs each book sequentially: embed → build knowledge graph → next book.
Continues on failure so one bad book doesn't block the rest.
After all books, builds cross-references between books sharing entities.

Usage:
    MODEL_BACKEND=local \
    VECTOR_STORE__URL=http://100.111.249.61:6333 \
    EMBEDDING__DEVICE=cuda \
    LLM__VLLM_BASE_URL=http://100.111.249.61:8001/v1 \
    LLM__VLLM_MODEL=Qwen/Qwen2.5-14B-Instruct-AWQ \
    NEO4J__URL=bolt://100.111.249.61:7687 \
    NEO4J__USER=neo4j \
    NEO4J__PASSWORD=neo4j_dev \
    NEO4J__DATABASE=knowledgehub \
    uv run python scripts/process_books_full.py

    # Single book
    uv run python scripts/process_books_full.py --book-id <ID>

    # Re-process completed books
    uv run python scripts/process_books_full.py --force

    # Preview
    uv run python scripts/process_books_full.py --dry-run

    # Skip the knowledge graph step (embed only)
    uv run python scripts/process_books_full.py --skip-graph

    # Skip cross-references
    uv run python scripts/process_books_full.py --skip-cross-refs
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.books.models import EmbeddingStatus
from src.books.repository import BookRepository
from src.books.service import BookService
from src.catalog.repository import CatalogRepository
from src.catalog.service import CatalogService
from src.data.book_chunking import chunk_book
from src.data.book_text_extractor import extract_book_text
from src.features.knowledge_graph.entity_resolution import EntityResolver
from src.models.embeddings import create_embedding_model
from src.models.graph_extractor import create_graph_extractor
from src.models.llm import create_llm_client
from src.pipelines.book_embedding import BookEmbeddingPipeline
from src.pipelines.knowledge_graph import KnowledgeGraphPipeline
from src.utils.config import settings
from src.utils.graph_store import create_graph_store
from src.utils.vector_store import VectorStore


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process books: embed + build knowledge graph")
    parser.add_argument("--book-id", help="Process a single book by ID")
    parser.add_argument("--force", action="store_true", help="Re-process completed books")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--skip-graph", action="store_true", help="Skip knowledge graph step")
    parser.add_argument(
        "--skip-cross-refs", action="store_true", help="Skip cross-reference building"
    )
    return parser.parse_args()


def _create_embedding_pipeline(book_service: BookService) -> BookEmbeddingPipeline:
    """Initialize the embedding pipeline."""
    catalog_repo = CatalogRepository(settings.catalog.database_path)
    catalog_service = CatalogService(catalog_repo)

    embedding_model = create_embedding_model(
        backend=settings.model_backend,
        model_name=settings.embedding.model_name,
        dimension=settings.embedding.dimension,
        device=settings.embedding.device,
    )

    vector_store = VectorStore(
        url=settings.vector_store.url,
        collection_name=settings.vector_store.collection_name,
        dimension=settings.embedding.dimension,
        in_memory=(settings.model_backend == "mock"),
    )

    return BookEmbeddingPipeline(
        book_service=book_service,
        catalog_service=catalog_service,
        embedding_model=embedding_model,
        vector_store=vector_store,
        books_collection=settings.books.qdrant_collection,
        chunk_size=settings.books.chunk_size,
        chunk_overlap=settings.books.chunk_overlap,
        embedding_batch_size=settings.books.embedding_batch_size,
    )


def _create_graph_pipeline(book_service: BookService) -> KnowledgeGraphPipeline:
    """Initialize the knowledge graph pipeline."""
    llm_client = create_llm_client(
        backend=settings.model_backend,
        api_key=settings.llm.api_key,
        model_id=settings.llm.model_id,
        temperature=settings.llm.temperature,
        timeout=settings.llm.timeout_seconds,
        vllm_base_url=settings.llm.vllm_base_url,
        vllm_model=settings.llm.vllm_model,
    )

    graph_extractor = create_graph_extractor(settings.model_backend, llm_client)
    entity_resolver = EntityResolver()
    graph_store = create_graph_store(settings.model_backend)

    return KnowledgeGraphPipeline(
        graph_extractor=graph_extractor,
        entity_resolver=entity_resolver,
        graph_store=graph_store,
        book_service=book_service,
    )


def _process_book(
    book_id: str,
    book_service: BookService,
    embed_pipeline: BookEmbeddingPipeline,
    graph_pipeline: KnowledgeGraphPipeline | None,
    *,
    force: bool,
) -> tuple[bool, list[str]]:
    """Process a single book: embed then graph.

    Returns (success, errors).
    """
    errors: list[str] = []
    book = book_service.get_book(book_id)
    title = book.title

    # Step 1: Embed
    try:
        result = embed_pipeline.process_book(book_id, force=force)
        if result.skipped:
            print("  Embed: skipped (already completed)")  # noqa: T201
        else:
            print(  # noqa: T201
                f"  Embed: {result.chunk_count} chunks, "
                f"{result.total_tokens} tokens, "
                f"{result.duration_ms}ms"
            )
    except Exception as e:
        errors.append(f"embedding: {e}")
        print(f"  Embed: FAILED — {e}")  # noqa: T201
        return False, errors

    # Step 2: Knowledge graph
    if graph_pipeline is not None:
        try:
            # Re-fetch book to get updated embedding_status
            book = book_service.get_book(book_id)
            structure = extract_book_text(Path(book.file_path), book.file_format)
            book_chunks = chunk_book(structure)
            chunk_dicts = [
                {
                    "text": c.text,
                    "chapter_title": c.chapter_title,
                    "chapter_number": c.chapter_number,
                }
                for c in book_chunks
            ]
            graph_result = graph_pipeline.build_book_graph(book_id, chunk_dicts, force=force)
            if graph_result.error:
                errors.append(f"graph: {graph_result.error}")
                print(f"  Graph: FAILED — {graph_result.error}")  # noqa: T201
            else:
                print(  # noqa: T201
                    f"  Graph: {graph_result.entity_count} entities, "
                    f"{graph_result.relationship_count} rels, "
                    f"{graph_result.topic_count} topics, "
                    f"{graph_result.duration_ms}ms"
                )
        except Exception as e:
            errors.append(f"graph: {e}")
            print(f"  Graph: FAILED — {e}")  # noqa: T201

    return len(errors) == 0, errors


def main() -> int:
    args = _parse_args()

    # Initialize services
    book_repo = BookRepository(settings.books.database_path)
    book_service = BookService(book_repo)

    # Get books to process
    response = book_service.list_books(limit=10000)
    all_books = response.books

    if args.book_id:
        targets = [b for b in all_books if b.id == args.book_id]
        if not targets:
            print(f"Book not found: {args.book_id}")  # noqa: T201
            return 1
    elif args.force:
        targets = all_books
    else:
        targets = [b for b in all_books if b.embedding_status != EmbeddingStatus.COMPLETED]

    # Dry run
    if args.dry_run:
        print(f"\n{'=' * 70}")  # noqa: T201
        print(f"  Books to process: {len(targets)}")  # noqa: T201
        print(f"  Mode: {'force' if args.force else 'pending only'}")  # noqa: T201
        print(f"  Graph: {'skip' if args.skip_graph else 'enabled'}")  # noqa: T201
        print(f"  Device: {settings.embedding.device}")  # noqa: T201
        print(f"  Qdrant: {settings.vector_store.url}")  # noqa: T201
        print(f"  vLLM: {settings.llm.vllm_base_url}")  # noqa: T201
        print(f"  Neo4j: {settings.neo4j.url}")  # noqa: T201
        print(f"{'=' * 70}")  # noqa: T201
        for b in targets:
            print(f"  [{b.embedding_status}] {b.title} ({b.file_format})")  # noqa: T201
        return 0

    # Initialize pipelines
    print(f"\n{'=' * 70}")  # noqa: T201
    print(f"  Processing {len(targets)} books (embed + graph)")  # noqa: T201
    print(f"  Device: {settings.embedding.device}")  # noqa: T201
    print(f"  Qdrant: {settings.vector_store.url}")  # noqa: T201
    print(f"  vLLM: {settings.llm.vllm_base_url}")  # noqa: T201
    print(f"  Neo4j: {settings.neo4j.url}")  # noqa: T201
    print(f"{'=' * 70}\n")  # noqa: T201

    embed_pipeline = _create_embedding_pipeline(book_service)
    graph_pipeline = None if args.skip_graph else _create_graph_pipeline(book_service)

    total_start = time.monotonic()
    completed = 0
    failed = 0
    all_errors: list[str] = []

    for i, book_summary in enumerate(targets):
        print(  # noqa: T201
            f"\n[{i + 1}/{len(targets)}] {book_summary.title} ({book_summary.file_format})"
        )
        book_start = time.monotonic()

        success, errors = _process_book(
            book_summary.id,
            book_service,
            embed_pipeline,
            graph_pipeline,
            force=args.force,
        )

        elapsed = time.monotonic() - book_start
        if success:
            completed += 1
            print(f"  Done in {elapsed:.1f}s")  # noqa: T201
        else:
            failed += 1
            for err in errors:
                all_errors.append(f"{book_summary.title}: {err}")
            print(f"  Failed after {elapsed:.1f}s")  # noqa: T201

    # Cross-references
    if graph_pipeline is not None and not args.skip_cross_refs and completed > 0:
        print("\nBuilding cross-references...")  # noqa: T201
        try:
            cross_ref = graph_pipeline.build_cross_references()
            print(  # noqa: T201
                f"  Cross-refs: {cross_ref.cross_ref_edges} edges "
                f"across {cross_ref.books_processed} books"
            )
        except Exception as e:
            print(f"  Cross-refs FAILED: {e}")  # noqa: T201
            all_errors.append(f"cross-references: {e}")

    # Summary
    total_elapsed = time.monotonic() - total_start
    print(f"\n{'=' * 70}")  # noqa: T201
    print(f"  Total:     {len(targets)}")  # noqa: T201
    print(f"  Completed: {completed}")  # noqa: T201
    print(f"  Failed:    {failed}")  # noqa: T201
    print(f"  Time:      {total_elapsed:.1f}s ({total_elapsed / 60:.1f}m)")  # noqa: T201
    print(f"{'=' * 70}")  # noqa: T201

    if all_errors:
        print("\nErrors:")  # noqa: T201
        for err in all_errors:
            print(f"  - {err}")  # noqa: T201

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
