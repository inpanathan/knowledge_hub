---
paths:
  - "src/data/**/*.py"
---

# Data Pipeline Rules

## Parser pattern
- Each parser function takes a `Path` and returns `str` (extracted text)
- Wrap format-specific exceptions in `AppError(code=ErrorCode.PARSE_FAILED)`
- Adding a new format: create parser function, update `SUPPORTED_FORMATS`, add to `parse_file()` dispatcher

## Chunking
- Use `chunk_text()` with parameters from `settings.chunking` (chunk_size, overlap)
- Never hardcode chunk sizes or overlap values — always read from config
- Chunking strategy must be configurable via settings (REQ-ING-008)

## Ingestion order
1. Parse document to extract text
2. Chunk text into segments
3. Compute embeddings for each chunk
4. Store chunks and embeddings in vector store
5. Store original file via file store
6. Create catalog entry with metadata

## Duplicate detection
- Compute content hash via `compute_file_hash()` or `compute_content_hash()` before proceeding
- Warn on duplicate, don't silently skip or silently re-index (REQ-ING-013)

## URL fetching
- Always pass explicit `timeout=` to HTTP requests
- Catch `httpx.TimeoutException` and `httpx.HTTPStatusError` separately
- Wrap failures in `AppError(code=ErrorCode.URL_FETCH_FAILED)`

## Folder scanning
- Skip unsupported file types with a warning, not a failure (REQ-ING-006)
- Detect symlinks and circular directory references — skip with warning
- Report per-file status (success/failure/skipped) and batch summary
