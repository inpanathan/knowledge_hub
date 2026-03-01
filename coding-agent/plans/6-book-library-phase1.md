# Phase 1 — Book Library: Download, Catalog & Library UI

## Context

The user has a personal book collection in Google Drive that needs to be downloaded to an AI cluster server, cataloged with rich metadata, and served via an indexed web interface. This is Phase 1 of a 3-phase effort — Phase 2 adds vector embeddings in Qdrant, Phase 3 adds a Neo4j knowledge graph. Phase 1 delivers the foundation: download pipeline, book catalog, REST API, and a React Library page.

**Requirements**: REQ-LIB-001–005, REQ-DLP-001–009, REQ-BMC-001–006, REQ-BLW-001–008 (from `docs/requirements/project_requirements_v2.md`)

**Decisions**:
- Auth: User OAuth 2.0 (browser consent, cached token)
- Storage: External path `/opt/document-store/books/` (configurable via `BOOKS__STORAGE_DIR`)
- Catalog: Separate `books` table in same SQLite DB, dedicated `BookRepository`/`BookService`
- Scope: Backend + Frontend (full Library page)

---

## Step 1 — Config + Error Codes `[x]`

### 1.1 Modify `src/utils/config.py` `[x]`
- Add `GoogleDriveSettings` (credentials_file, token_file, folder_id, scopes)
- Add `BooksSettings` (storage_dir=/opt/document-store/books/, covers_dir, chunk_size, chunk_overlap, embedding_batch_size, qdrant_collection, database_path=data/catalog.db, supported_formats)
- Add both as fields on `Settings`
- Fix `validate_app_env` — add `"local"` to allowed set

### 1.2 Modify `src/utils/errors.py` `[x]`
- Add to `ErrorCode`: `GDRIVE_AUTH_FAILED`, `GDRIVE_DOWNLOAD_FAILED`, `GDRIVE_FOLDER_NOT_FOUND`, `BOOK_NOT_FOUND`, `BOOK_DUPLICATE`, `BOOK_METADATA_FAILED`

### 1.3 Modify `main.py` `[x]`
- Add HTTP status mappings for new error codes (404, 401, 409)

---

## Step 2 — Book Catalog (Models, Repository, Service) `[x]`

### 2.1 Create `src/books/__init__.py` `[x]`

### 2.2 Create `src/books/models.py` `[x]`
- `EmbeddingStatus` (StrEnum: pending, processing, completed, failed)
- `GraphStatus` (StrEnum: pending, processing, completed, failed, skipped)
- `Book` — id, title, author, isbn, publisher, publication_year, language, page_count, file_format, file_size_bytes, file_hash, file_path, cover_image_path, description, table_of_contents (list), tags (list), drive_folder_path, drive_file_id, created_at, processed_at, embedding_status, graph_status, source_id
- `BookCreate`, `BookUpdate`, `BookSummary`, `BookListResponse`

### 2.3 Create `src/books/repository.py` `[x]`
- Mirror `src/catalog/repository.py` pattern exactly
- `books` table in same SQLite file as `sources`
- CRUD: create, get, list_books (filter by author/tag/search/embedding_status + pagination), update, delete
- `find_by_hash(file_hash)`, `find_by_drive_file_id(drive_file_id)`

### 2.4 Create `src/books/service.py` `[x]`
- Mirror `src/catalog/service.py` pattern
- create_book, get_book (raises BOOK_NOT_FOUND), list_books, update_book, delete_book
- find_duplicate, find_by_drive_file_id
- mark_processed, mark_embedding_completed, mark_embedding_failed

---

## Step 3 — Google Drive Client `[x]`

### 3.1 Create `src/data/gdrive_client.py` `[x]`
- `GoogleDriveClient(credentials_file, token_file, scopes)`
- `_get_service()` — load cached token, or run `InstalledAppFlow` browser consent, cache token
- `list_files(folder_id, *, mime_types, recursive=True) -> list[dict]` — paginated listing, recursive subfolder walk
- `download_file(file_id, dest_path, *, chunk_size=1MB)` — streaming via `MediaIoBaseDownload`
- Path traversal validation on dest_path
- Raises `AppError(GDRIVE_AUTH_FAILED | GDRIVE_DOWNLOAD_FAILED | GDRIVE_FOLDER_NOT_FOUND)`

---

## Step 4 — Book Metadata Extraction `[x]`

### 4.1 Create `src/data/book_metadata.py` `[x]`
- `extract_metadata(file_path: Path) -> dict` — dispatches by suffix
- `_extract_pdf_metadata` — pypdf: title, author, subject, page_count, ISBN regex scan
- `_extract_epub_metadata` — ebooklib: Dublin Core fields, ToC
- `_extract_docx_metadata` — python-docx: core_properties
- `_extract_txt_metadata` — filename-based title
- `extract_cover_image(file_path, covers_dir, book_id) -> str` — EPUB cover in Phase 1, PDF deferred

---

## Step 5 — Download Pipeline Script `[x]`

### 5.1 Create `scripts/download_books.py` `[x]`
- CLI args: `--folder-id`, `--dry-run`, `--resume`
- Flow: auth → list files → for each: check idempotency (drive_file_id/hash) → download → extract metadata → extract cover → create book catalog entry → log
- Filename sanitization
- Download manifest (summary at end)
- Structured logging throughout
- Exit code 0 on success, 1 if any failures

---

## Step 6 — Seed Orchestrator Script `[x]`

### 6.1 Create `scripts/seed_books.sh` `[x]`
- Follows existing script pattern (set -euo pipefail, resolve PROJECT_ROOT, load .env)
- Commands: `run` (default), `--dry-run`, `status`
- `status` prints book count from catalog

---

## Step 7 — API Endpoints + Schemas `[x]`

### 7.1 Modify `src/api/schemas.py` `[x]`
- `BookSummaryResponse`, `BookDetailResponse`, `BookListResponse`, `BookUpdateRequest`

### 7.2 Modify `src/api/routes.py` `[x]`
- `GET /books` — list with filters (author, tag, search, embedding_status, limit, offset)
- `GET /books/{book_id}` — full detail
- `PUT /books/{book_id}` — update metadata
- `DELETE /books/{book_id}` — delete book + file
- `GET /books/{book_id}/download` — stream file (with path traversal protection)
- `GET /books/{book_id}/cover` — serve cover image

---

## Step 8 — Dependency Injection Wiring `[x]`

### 8.1 Modify `src/api/dependencies.py` `[x]`
- Import `BookRepository`, `BookService`
- Add `books: BookService` to `ServiceContainer`
- Wire in `init_services()`: `BookRepository(settings.books.database_path)` → `BookService(repo)`
- Add `get_books() -> BookService` accessor

---

## Step 9 — Config File Updates `[x]`

### 9.1 Modify `configs/dev.yaml` `[x]`
- Add `google_drive:` section (local paths, empty folder_id)
- Add `books:` section (storage_dir=data/books/, covers_dir=data/covers/)

### 9.2 Modify `configs/local.yaml` `[x]`
- Add same sections with production paths (/opt/document-store/...)

### 9.3 Modify `.env.example` `[x]`
- Add `GOOGLE_DRIVE__*` and `BOOKS__*` variables with comments

---

## Step 10 — Dependencies `[x]`

### 10.1 Modify `pyproject.toml` `[x]`
- Add `books` optional extra: google-api-python-client, google-auth-oauthlib, google-auth-httplib2, ebooklib
- Install: `uv sync --extra dev --extra books`

---

## Step 11 — Frontend Library Page `[x]`

### 11.1 Create `frontend/src/api/books.ts` `[x]`
- listBooks, getBook, updateBook, deleteBook, getBookDownloadUrl, getBookCoverUrl

### 11.2 Modify `frontend/src/api/types.ts` `[x]`
- BookSummary, BookDetail, BookListResponse, BookUpdateRequest interfaces

### 11.3 Create `frontend/src/features/library/BookCard.tsx` `[x]`
- Cover image / placeholder icon, title, author, year, format, tags, dropdown (download/delete)

### 11.4 Create `frontend/src/features/library/BookDetail.tsx` `[x]`
- Sheet component with full metadata, editable fields, ToC, actions

### 11.5 Create `frontend/src/features/library/LibraryPage.tsx` `[x]`
- Search bar, grid layout, loading skeletons, empty state, detail sheet on click

### 11.6 Modify `frontend/src/App.tsx` `[x]`
- Add `/library` route

### 11.7 Modify sidebar/nav component `[x]`
- Add Library nav item with BookOpen icon

---

## Step 12 — Tests `[x]`

### 12.1 Create `tests/unit/test_book_repository.py` `[x]`
- create/get, list (empty, search, filter), update, delete, find_by_hash, find_by_drive_file_id, table coexistence with sources

### 12.2 Create `tests/unit/test_book_metadata.py` `[x]`
- PDF metadata extraction, TXT fallback, unknown format safety, ISBN regex

### 12.3 Create `tests/unit/test_gdrive_client.py` `[x]`
- Mocked: list_files, download_file, auth failure handling

### 12.4 Create `tests/integration/test_books_api.py` `[x]`
- list (empty + seeded), get, get 404, update, delete 204, download file bytes

---

## Step 13 — Documentation `[x]`

### 13.1 Update `docs/app_cheatsheet.md` `[x]`
- Add book API endpoints, config vars, scripts, Library URL

---

## Verification

1. `uv run ruff check src/ tests/ && uv run mypy src/ --ignore-missing-imports` — no errors
2. `uv run pytest tests/unit/test_book_repository.py tests/unit/test_book_metadata.py tests/unit/test_gdrive_client.py tests/integration/test_books_api.py -x -q` — all pass
3. `APP_ENV=dev uv run python main.py` — starts, `GET /api/v1/books` returns 200
4. `bash scripts/seed_books.sh status` — prints book count
5. `bash scripts/seed_books.sh --dry-run` — lists Drive files without downloading
6. `http://localhost:3000/library` — renders Library page with grid, search, detail sheet
7. After seeding: books appear in grid with metadata and download works

## Key Files

| File | Action | Purpose |
|------|--------|---------|
| `src/utils/config.py` | Modify | Add GoogleDriveSettings, BooksSettings |
| `src/utils/errors.py` | Modify | Add 6 new error codes |
| `src/catalog/repository.py` | Reference | Pattern to mirror for BookRepository |
| `src/books/models.py` | Create | Book, BookCreate, BookUpdate, BookSummary |
| `src/books/repository.py` | Create | SQLite CRUD for books table |
| `src/books/service.py` | Create | Business logic layer |
| `src/data/gdrive_client.py` | Create | Google Drive API wrapper |
| `src/data/book_metadata.py` | Create | Multi-format metadata extraction |
| `scripts/download_books.py` | Create | CLI download + catalog script |
| `scripts/seed_books.sh` | Create | Bash orchestrator |
| `src/api/schemas.py` | Modify | Book request/response models |
| `src/api/routes.py` | Modify | 6 book endpoints |
| `src/api/dependencies.py` | Modify | Wire BookService into DI |
| `frontend/src/features/library/` | Create | LibraryPage, BookCard, BookDetail |
| `pyproject.toml` | Modify | Add books optional extra |
