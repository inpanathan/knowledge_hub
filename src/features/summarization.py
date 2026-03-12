"""Content summarization feature."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from src.utils.config import settings
from src.utils.errors import AppError, ErrorCode
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.books.service import BookService
    from src.catalog.service import CatalogService
    from src.models.embeddings import EmbeddingModel
    from src.models.llm import LLMClient
    from src.utils.cache import CacheStore
    from src.utils.vector_store import VectorStore

logger = get_logger(__name__)

# Reserve tokens for system prompt, user instructions, and output
_OUTPUT_TOKENS = 1024
_PROMPT_OVERHEAD_TOKENS = 300
# Content budget per LLM call in characters (~3,700 tokens * 4 chars/token)
_CONTENT_BUDGET_CHARS = 14_800


def _truncate_to_token_budget(text: str, max_tokens: int) -> str:
    """Truncate text to fit within a token budget (rough: 1 token ~ 4 chars)."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Content truncated to fit context window]"


class SummaryMode(StrEnum):
    """Summary output mode."""

    SHORT = "short"
    DETAILED = "detailed"


@dataclass
class SummaryResult:
    """Result of a summarization request."""

    summary: str
    mode: SummaryMode
    source_ids: list[str]
    source_titles: list[str]


@dataclass
class ChapterSummary:
    """Summary of a single book chapter."""

    chapter_number: int
    chapter_title: str
    summary: str
    chunk_count: int


@dataclass
class BookSummaryResult:
    """Full book summarization result with per-chapter detail."""

    book_id: str
    book_title: str
    author: str
    overall_summary: str
    chapters: list[ChapterSummary] = field(default_factory=list)
    total_chunks_processed: int = 0
    total_llm_calls: int = 0


class SummarizationService:
    """Generates summaries of indexed content."""

    def __init__(
        self,
        llm_client: LLMClient,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        catalog: CatalogService,
        *,
        book_service: BookService | None = None,
        cache: CacheStore | None = None,
    ) -> None:
        self._llm = llm_client
        self._vector_store = vector_store
        self._embedding = embedding_model
        self._catalog = catalog
        self._book_service = book_service
        self._cache = cache

    def summarize_sources(
        self,
        source_ids: list[str],
        *,
        mode: SummaryMode = SummaryMode.SHORT,
    ) -> SummaryResult:
        """Generate a summary of one or more sources."""
        if not source_ids:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="At least one source ID is required",
            )

        # Collect content from each source
        all_content: list[str] = []
        titles: list[str] = []

        for sid in source_ids:
            source = self._catalog.get_source(sid)
            titles.append(source.title)

            # Retrieve chunks for this source
            dummy_embedding = self._embedding.embed_query(source.title)
            results = self._vector_store.search(
                query_embedding=dummy_embedding,
                top_k=50,
                where={"source_id": sid},
            )
            chunks = sorted(results, key=lambda r: r.metadata.get("chunk_index", 0))
            source_text = "\n\n".join(r.text for r in chunks)
            all_content.append(f"[Source: {source.title}]\n{source_text}")

        combined = "\n\n---\n\n".join(all_content)
        content_budget = settings.rag.max_context_tokens - _PROMPT_OVERHEAD_TOKENS
        combined = _truncate_to_token_budget(combined, content_budget)

        # Build prompt based on mode
        if mode == SummaryMode.SHORT:
            prompt = (
                f"Provide a concise summary (1-3 paragraphs) of the following content. "
                f"Focus on the key takeaways and main points.\n\n"
                f"Content:\n{combined}"
            )
        else:
            prompt = (
                f"Provide a detailed, comprehensive summary of the following content. "
                f"Organize the summary with clear sections and subsections. "
                f"Include key points, important details, and notable insights. "
                f"If there are multiple sources, organize by source with clear attribution.\n\n"
                f"Content:\n{combined}"
            )

        system = (
            "You are a skilled summarizer. Create clear, accurate summaries that "
            "capture the essential information from the provided content. "
            "Never fabricate information not present in the source material."
        )

        summary = self._llm.generate(prompt, system=system, max_tokens=_OUTPUT_TOKENS)

        logger.info(
            "summary_generated",
            mode=mode.value,
            source_count=len(source_ids),
            summary_length=len(summary),
        )

        return SummaryResult(
            summary=summary,
            mode=mode,
            source_ids=source_ids,
            source_titles=titles,
        )

    def summarize_topic(
        self,
        topic: str,
        *,
        mode: SummaryMode = SummaryMode.SHORT,
    ) -> SummaryResult:
        """Summarize a topic across all indexed sources."""
        query_embedding = self._embedding.embed_query(topic)
        results = self._vector_store.search(query_embedding=query_embedding, top_k=20)

        if not results:
            raise AppError(
                code=ErrorCode.NO_RELEVANT_CONTEXT,
                message=f"No relevant content found for topic: {topic}",
                context={"topic": topic},
            )

        # Group by source
        source_ids = list({r.metadata.get("source_id", "") for r in results})
        titles: list[str] = []
        for sid in source_ids:
            try:
                source = self._catalog.get_source(sid)
                titles.append(source.title)
            except Exception:
                titles.append("Unknown")

        combined = "\n\n---\n\n".join(r.text for r in results)
        content_budget = settings.rag.max_context_tokens - _PROMPT_OVERHEAD_TOKENS
        combined = _truncate_to_token_budget(combined, content_budget)

        if mode == SummaryMode.SHORT:
            prompt = (
                f"Provide a concise summary (1-3 paragraphs) about '{topic}' "
                f"based on the following content.\n\n"
                f"Content:\n{combined}"
            )
        else:
            prompt = (
                f"Provide a detailed summary about '{topic}' based on the following content. "
                f"Organize by subtopics with clear sections.\n\n"
                f"Content:\n{combined}"
            )

        system = (
            "You are a skilled summarizer. Create clear, accurate summaries that "
            "capture the essential information. Never fabricate information."
        )

        summary = self._llm.generate(prompt, system=system, max_tokens=_OUTPUT_TOKENS)

        return SummaryResult(
            summary=summary,
            mode=mode,
            source_ids=source_ids,
            source_titles=titles,
        )

    # ── Book summarization (map-reduce) ──────────────────────────────────

    def summarize_book(
        self,
        book_id: str,
        *,
        mode: SummaryMode = SummaryMode.DETAILED,
    ) -> BookSummaryResult:
        """Summarize an entire book chapter-by-chapter using map-reduce.

        1. Discover chapters from stored chunks
        2. Map: summarize each chapter (batched if large)
        3. Reduce: synthesize overall summary from chapter summaries
        """
        if self._book_service is None:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Book service not available for book summarization",
            )

        book = self._book_service.get_book(book_id)
        if book.embedding_status != "completed":
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Book must be embedded before summarization",
                context={"book_id": book_id, "embedding_status": book.embedding_status},
            )

        # Check cache
        cache_key = f"book_summary:{book_id}:{mode.value}"
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.info("book_summary_cache_hit", book_id=book_id, mode=mode.value)
                return BookSummaryResult(
                    book_id=cached["book_id"],
                    book_title=cached["book_title"],
                    author=cached["author"],
                    overall_summary=cached["overall_summary"],
                    chapters=[ChapterSummary(**ch) for ch in cached["chapters"]],
                    total_chunks_processed=cached["total_chunks_processed"],
                    total_llm_calls=cached["total_llm_calls"],
                )

        collection = settings.books.qdrant_collection
        llm_calls = 0

        # Discover chapters
        all_chunks = self._vector_store.scroll_book_chunks(collection, book_id)
        if not all_chunks:
            raise AppError(
                code=ErrorCode.NO_RELEVANT_CONTEXT,
                message="No chunks found for this book",
                context={"book_id": book_id},
            )

        chapter_map: dict[int, str] = {}
        for chunk in all_chunks:
            ch_num = chunk.metadata.get("chapter_number", 0)
            ch_title = chunk.metadata.get("chapter_title", "")
            if ch_num not in chapter_map:
                chapter_map[ch_num] = ch_title

        sorted_chapters = sorted(chapter_map.items())
        logger.info(
            "book_chapters_discovered",
            book_id=book_id,
            chapter_count=len(sorted_chapters),
            total_chunks=len(all_chunks),
        )

        # Map phase: summarize each chapter
        chapter_summaries: list[ChapterSummary] = []
        total_chunks = 0

        for ch_num, ch_title in sorted_chapters:
            try:
                chapter_chunks = self._vector_store.scroll_book_chunks(
                    collection, book_id, chapter_number=ch_num
                )
                if not chapter_chunks:
                    continue

                total_chunks += len(chapter_chunks)
                summary_text, calls = self._summarize_chapter(chapter_chunks, ch_title, mode)
                llm_calls += calls

                chapter_summaries.append(
                    ChapterSummary(
                        chapter_number=ch_num,
                        chapter_title=ch_title or f"Chapter {ch_num}",
                        summary=summary_text,
                        chunk_count=len(chapter_chunks),
                    )
                )
                logger.info(
                    "chapter_summarized",
                    book_id=book_id,
                    chapter_number=ch_num,
                    chunk_count=len(chapter_chunks),
                    llm_calls=calls,
                )
            except Exception:
                logger.warning(
                    "chapter_summarization_failed",
                    book_id=book_id,
                    chapter_number=ch_num,
                    exc_info=True,
                )

        if not chapter_summaries:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="All chapter summarizations failed",
                context={"book_id": book_id},
            )

        # Reduce phase: overall summary from chapter summaries
        overall_summary, reduce_calls = self._reduce_to_overall(
            book.title, book.author, chapter_summaries, mode
        )
        llm_calls += reduce_calls

        result = BookSummaryResult(
            book_id=book_id,
            book_title=book.title,
            author=book.author,
            overall_summary=overall_summary,
            chapters=chapter_summaries,
            total_chunks_processed=total_chunks,
            total_llm_calls=llm_calls,
        )

        # Cache result
        if self._cache is not None:
            self._cache.set(
                cache_key,
                {
                    "book_id": result.book_id,
                    "book_title": result.book_title,
                    "author": result.author,
                    "overall_summary": result.overall_summary,
                    "chapters": [
                        {
                            "chapter_number": ch.chapter_number,
                            "chapter_title": ch.chapter_title,
                            "summary": ch.summary,
                            "chunk_count": ch.chunk_count,
                        }
                        for ch in result.chapters
                    ],
                    "total_chunks_processed": result.total_chunks_processed,
                    "total_llm_calls": result.total_llm_calls,
                },
            )

        logger.info(
            "book_summarization_completed",
            book_id=book_id,
            chapter_count=len(chapter_summaries),
            total_chunks=total_chunks,
            llm_calls=llm_calls,
        )
        return result

    def _summarize_chapter(
        self,
        chunks: list,
        chapter_title: str,
        mode: SummaryMode,
    ) -> tuple[str, int]:
        """Summarize a chapter's chunks, batching if needed. Returns (summary, llm_calls)."""
        texts = [c.text for c in chunks]
        batches = self._batch_texts(texts, _CONTENT_BUDGET_CHARS)
        llm_calls = 0

        batch_summaries: list[str] = []
        for batch in batches:
            combined = "\n\n".join(batch)
            summary = self._summarize_chunk_batch(combined, chapter_title, mode)
            llm_calls += 1
            batch_summaries.append(summary)

        if len(batch_summaries) == 1:
            return batch_summaries[0], llm_calls

        # Reduce multiple batch summaries into one chapter summary
        reduced = self._reduce_summaries(batch_summaries, chapter_title, mode)
        llm_calls += 1
        return reduced, llm_calls

    def _summarize_chunk_batch(self, content: str, chapter_title: str, mode: SummaryMode) -> str:
        """Summarize a single batch of chunk text."""
        label = f"chapter '{chapter_title}'" if chapter_title else "this section"
        if mode == SummaryMode.SHORT:
            prompt = (
                f"Summarize {label} concisely (1-2 paragraphs). "
                f"Focus on key points.\n\nContent:\n{content}"
            )
        else:
            prompt = (
                f"Provide a detailed summary of {label}. "
                f"Include key arguments, examples, and insights.\n\nContent:\n{content}"
            )

        system = (
            "You are summarizing a section of a book. Be accurate and comprehensive. "
            "Never fabricate information not present in the text."
        )
        return self._llm.generate(prompt, system=system, max_tokens=_OUTPUT_TOKENS)

    def _reduce_summaries(self, summaries: list[str], chapter_title: str, mode: SummaryMode) -> str:
        """Reduce multiple partial summaries into one combined summary."""
        combined = "\n\n---\n\n".join(f"[Part {i + 1}]\n{s}" for i, s in enumerate(summaries))
        combined = combined[:_CONTENT_BUDGET_CHARS]

        prompt = (
            f"The following are partial summaries of '{chapter_title}'. "
            f"Combine them into a single coherent summary.\n\n{combined}"
        )
        system = (
            "You are combining partial summaries into one. Preserve all key information. "
            "Remove redundancy. Never fabricate information."
        )
        return self._llm.generate(prompt, system=system, max_tokens=_OUTPUT_TOKENS)

    def _reduce_to_overall(
        self,
        book_title: str,
        author: str,
        chapters: list[ChapterSummary],
        mode: SummaryMode,
    ) -> tuple[str, int]:
        """Reduce chapter summaries into an overall book summary. Returns (summary, llm_calls)."""
        chapter_texts = [f"## {ch.chapter_title}\n{ch.summary}" for ch in chapters]
        combined = "\n\n".join(chapter_texts)

        # If all chapter summaries fit in one call, use one call
        if len(combined) <= _CONTENT_BUDGET_CHARS:
            summary = self._generate_overall(book_title, author, combined, mode)
            return summary, 1

        # Otherwise batch the chapter summaries and reduce
        batches = self._batch_texts(chapter_texts, _CONTENT_BUDGET_CHARS)
        batch_summaries: list[str] = []
        for batch in batches:
            batch_combined = "\n\n".join(batch)
            summary = self._generate_overall(book_title, author, batch_combined, mode)
            batch_summaries.append(summary)

        if len(batch_summaries) == 1:
            return batch_summaries[0], len(batches)

        # Final reduce
        final_combined = "\n\n---\n\n".join(batch_summaries)[:_CONTENT_BUDGET_CHARS]
        final = self._generate_overall(book_title, author, final_combined, mode)
        return final, len(batches) + 1

    def _generate_overall(
        self, book_title: str, author: str, content: str, mode: SummaryMode
    ) -> str:
        """Generate an overall book summary from chapter summaries."""
        by_author = f" by {author}" if author else ""
        if mode == SummaryMode.SHORT:
            prompt = (
                f"Based on these chapter summaries of '{book_title}'{by_author}, "
                f"write a concise overall summary (2-3 paragraphs).\n\n{content}"
            )
        else:
            prompt = (
                f"Based on these chapter summaries of '{book_title}'{by_author}, "
                f"write a comprehensive overall summary. Include the book's main thesis, "
                f"key themes, and important conclusions.\n\n{content}"
            )
        system = (
            "You are writing an overall book summary from chapter summaries. "
            "Be comprehensive and accurate. Never fabricate information."
        )
        return self._llm.generate(prompt, system=system, max_tokens=_OUTPUT_TOKENS)

    @staticmethod
    def _batch_texts(texts: list[str], budget_chars: int) -> list[list[str]]:
        """Split texts into batches that fit within the character budget."""
        batches: list[list[str]] = []
        current_batch: list[str] = []
        current_size = 0

        for text in texts:
            text_size = len(text) + 2  # +2 for join separators
            if current_batch and current_size + text_size > budget_chars:
                batches.append(current_batch)
                current_batch = []
                current_size = 0
            current_batch.append(text)
            current_size += text_size

        if current_batch:
            batches.append(current_batch)

        return batches
