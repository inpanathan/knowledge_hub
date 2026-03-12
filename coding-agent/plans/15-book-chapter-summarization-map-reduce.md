# Plan 15: Chapter-Level Book Summarization (Map-Reduce)

## Status: Complete

### Step 1: Add `scroll_book_chunks()` to VectorStore
- [x] File: `src/utils/vector_store.py`

### Step 2: Add data models for book summarization
- [x] File: `src/features/summarization.py`

### Step 3: Update `SummarizationService` constructor
- [x] File: `src/features/summarization.py`

### Step 4: Wire dependencies in DI container
- [x] File: `src/api/dependencies.py`

### Step 5: Implement `summarize_book()` map-reduce method
- [x] File: `src/features/summarization.py`

### Step 6: Add API schemas
- [x] File: `src/api/schemas.py`

### Step 7: Add API endpoint
- [x] File: `src/api/routes.py`

### Step 8: Frontend types and API client
- [x] File: `frontend/src/api/types.ts`
- [x] File: `frontend/src/api/books.ts`

### Step 9: Add "Summarize" button to BookDetail
- [x] File: `frontend/src/features/library/BookDetail.tsx`

### Step 10: Add "By Book" tab to SummarizePage
- [x] File: `frontend/src/features/summarize/SummarizePage.tsx`

### Step 11: Tests
- [x] File: `tests/unit/test_book_summarization.py`
- [x] File: `tests/integration/test_book_summarization.py`

### Step 12: Documentation
- [x] Updated `docs/app_cheatsheet.md`
- [x] Plan file: `coding-agent/plans/15-book-chapter-summarization-map-reduce.md`
