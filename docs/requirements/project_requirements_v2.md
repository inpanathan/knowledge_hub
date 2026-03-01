# Project Specification — Knowledge Hub v2: Book Library, Vector Embeddings & Knowledge Graph

## 1. Goal

- **One-time bulk seeding** of the Knowledge Hub with a personal book collection stored in Google Drive.
- Download the books to a server in the AI cluster, serve them via a properly indexed and cataloged web interface with rich metadata, and process each book to create vector embeddings in Qdrant and a knowledge graph in Neo4j.
- Enable RAG over the entire book collection and cross-book knowledge discovery via the knowledge graph.

## 2. Deliverables

- A Google Drive download pipeline that fetches all books from a specified folder to local storage on an AI cluster server.
- A book catalog web page with metadata extraction, full-text search, cover images, and browsing/filtering.
- A processing pipeline that chunks each book and creates vector embeddings in Qdrant with rich metadata.
- A knowledge graph in Neo4j built from extracted entities, concepts, and relationships across all books.
- API endpoints for browsing, searching, and querying the book library, embeddings, and knowledge graph.
- Scripts for one-time seeding (download, catalog, embed, graph build) with progress reporting.
- Integration with the existing Knowledge Hub RAG pipeline so books are queryable via chat.

## 3. High-Level Requirements

### Phase 1 — Download & Catalog

- [ ] **REQ-LIB-001**: Download all books from a specified Google Drive folder (and subfolders) to a designated directory on an AI cluster server.
- [ ] **REQ-LIB-002**: Extract metadata from each book (title, author, ISBN, publisher, publication year, page count, language, file format, file size, table of contents).
- [ ] **REQ-LIB-003**: Persist book metadata in a structured catalog database (SQLite for v2, upgradable to PostgreSQL).
- [ ] **REQ-LIB-004**: Serve books via a web interface with browsing, search, filtering, and metadata display.
- [ ] **REQ-LIB-005**: Store original book files organized by author/title on the server filesystem.

### Phase 2 — Vector Embeddings

- [ ] **REQ-LIB-006**: Parse each book into clean text, respecting structure (chapters, sections, paragraphs).
- [ ] **REQ-LIB-007**: Chunk each book using a structure-aware strategy (chapter-aware splitting, configurable chunk size with overlap).
- [ ] **REQ-LIB-008**: Generate vector embeddings for each chunk using the configured embedding model (default: `BAAI/bge-large-en-v1.5`, 1024-dim).
- [ ] **REQ-LIB-009**: Store embeddings in Qdrant with rich metadata (book ID, title, author, chapter, section, page range, chunk index).
- [ ] **REQ-LIB-010**: Register each processed book as a source in the existing Knowledge Hub catalog so it is available for RAG chat, Q&A, summarization, and interview features.

### Phase 3 — Knowledge Graph

- [ ] **REQ-LIB-011**: Extract named entities from each book (people, organizations, places, concepts, technologies, events, theories).
- [ ] **REQ-LIB-012**: Extract relationships between entities (e.g., "author_of", "mentions", "related_to", "part_of", "precedes", "contradicts", "supports").
- [ ] **REQ-LIB-013**: Build a knowledge graph in Neo4j with books, chapters, entities, and concepts as nodes, and extracted relationships as edges.
- [ ] **REQ-LIB-014**: Support cross-book entity resolution (merge duplicate entities referring to the same real-world thing across books).
- [ ] **REQ-LIB-015**: Provide API endpoints to query the knowledge graph (neighbors, paths, subgraphs, entity search).
- [ ] **REQ-LIB-016**: Visualize the knowledge graph in the frontend (interactive node-link diagram with filtering and search).

## 4. Functional Requirements

### Feature 1: Google Drive Download Pipeline

- [ ] **REQ-DLP-001**: Accept a Google Drive folder URL or folder ID as input. Authenticate via OAuth 2.0 using service account or user credentials stored in environment variables or a credentials file.
- [ ] **REQ-DLP-002**: Recursively list all files in the folder and subfolders. Supported book formats: PDF, EPUB, MOBI, DJVU, CBZ, TXT, DOCX, and Markdown. Skip unsupported formats with a warning.
- [ ] **REQ-DLP-003**: Download each file to a local staging directory on the AI cluster server. Organize files by subfolder structure mirroring the Drive hierarchy.
- [ ] **REQ-DLP-004**: Implement resumable downloads — track download progress so the script can be interrupted and resumed without re-downloading completed files.
- [ ] **REQ-DLP-005**: Generate a content hash (SHA-256) for each downloaded file. Skip files already present on disk with a matching hash (idempotent re-runs).
- [ ] **REQ-DLP-006**: Log download progress with structured logging: file name, size, download speed, elapsed time, files remaining.
- [ ] **REQ-DLP-007**: Produce a download manifest (JSON) listing all files: path, size, hash, download status, and any errors.
- [ ] **REQ-DLP-008**: Handle Google Drive API rate limits with exponential backoff and retry. Log rate limit events.
- [ ] **REQ-DLP-009**: Support Google Docs/Sheets/Slides export — if present in the folder, export as PDF before downloading. Skip or warn for formats that cannot be exported.

**Edge cases:**

- Empty folders or folders with only unsupported files: log warning, produce empty manifest.
- Files larger than 1 GB: stream download in chunks, log progress percentage.
- Google Drive shortcuts/aliases: resolve to the actual file before downloading.
- Files with identical names in different subfolders: preserve subfolder structure to avoid collisions.
- Corrupted or partial downloads: verify hash after download, re-download on mismatch.
- Network interruptions: retry with backoff, mark failed files in manifest for manual review.

### Feature 2: Book Metadata Extraction & Catalog

- [ ] **REQ-BMC-001**: Extract metadata from each downloaded book using format-specific parsers:
  - **PDF**: title, author, subject, keywords, creator, producer, page count, creation date (from PDF metadata dict). Fall back to filename parsing if metadata fields are empty.
  - **EPUB**: title, author, publisher, language, ISBN, publication date, description, table of contents (from OPF/Dublin Core metadata).
  - **MOBI/AZW**: title, author, publisher, ISBN, language (via calibre tools or KindleUnpack).
  - **DJVU**: title, author, page count (from DJVU metadata).
  - **TXT/MD/DOCX**: title from first heading or filename, author from document properties if available.
- [ ] **REQ-BMC-002**: For books with missing or incomplete metadata, attempt enrichment via:
  - ISBN lookup against Open Library API or Google Books API.
  - Title + author fuzzy matching against Open Library or Google Books.
  - Log which fields were enriched and from which source.
- [ ] **REQ-BMC-003**: Extract or generate a cover image for each book:
  - PDF: render first page as a thumbnail.
  - EPUB: extract embedded cover image from the package.
  - Others: generate a placeholder cover with title and author text.
- [ ] **REQ-BMC-004**: Persist all metadata in a `books` table with columns: `id`, `title`, `author`, `isbn`, `publisher`, `publication_year`, `language`, `page_count`, `file_format`, `file_size_bytes`, `file_hash`, `file_path`, `cover_image_path`, `description`, `table_of_contents` (JSON), `tags` (JSON array), `drive_folder_path`, `drive_file_id`, `created_at`, `processed_at`, `embedding_status`, `graph_status`.
- [ ] **REQ-BMC-005**: Provide a Pydantic model (`BookMetadata`) for the book catalog entry, used across API, processing, and frontend.
- [ ] **REQ-BMC-006**: Detect and flag duplicate books (by content hash or ISBN match). Present duplicates for user review rather than silently deduplicating.

**Edge cases:**

- Books with no extractable metadata: use filename-derived title, mark author as "Unknown", log warning.
- Multiple authors: store as a JSON array, display as comma-separated.
- Non-English metadata: preserve original encoding, store language tag.
- Corrupted or DRM-protected files: log error, mark as `status=failed` in catalog, skip processing.
- ISBN conflicts (two different books with same ISBN): flag for manual review.

### Feature 3: Book Library Web Interface

- [ ] **REQ-BLW-001**: Add a "Library" page to the frontend that displays all cataloged books in a grid layout with cover images, titles, and authors.
- [ ] **REQ-BLW-002**: Support list view (table with sortable columns: title, author, year, format, pages, size) and grid view (card layout with covers) toggle.
- [ ] **REQ-BLW-003**: Implement faceted search and filtering:
  - Full-text search on title, author, description, and tags.
  - Filter by: author, publication year range, file format, language, tags, processing status.
  - Sort by: title, author, year, date added, file size, page count.
- [ ] **REQ-BLW-004**: Book detail page showing: full metadata, cover image, table of contents (if available), description, tags, processing status (download, embedding, graph), and links to view/download the original file.
- [ ] **REQ-BLW-005**: Allow users to edit book metadata (title, author, tags, description) via the detail page.
- [ ] **REQ-BLW-006**: Integrate with the existing document viewer (Feature 6 from v1) so users can read books in-browser.
- [ ] **REQ-BLW-007**: Display processing status indicators: downloaded, text extracted, embeddings created, knowledge graph nodes created.
- [ ] **REQ-BLW-008**: Show library statistics on the page: total books, total pages, books by format, books by language, processing completion percentage.

### Feature 4: Book Text Extraction & Chunking

- [ ] **REQ-BTE-001**: Extract clean text from each book, preserving structural elements:
  - **PDF**: extract text page-by-page using `pypdf`. Detect chapter boundaries via heading patterns (font size, boldness, numbering). Handle multi-column layouts.
  - **EPUB**: parse each chapter from the EPUB spine, preserving chapter order and headings. Strip HTML tags, retain paragraph structure.
  - **MOBI**: convert to EPUB first (via calibre tools), then process as EPUB.
  - **DJVU**: extract text layer using `djvutxt` or `python-djvulibre`.
  - **DOCX**: extract using `python-docx`, preserve heading levels and paragraph breaks.
  - **TXT/MD**: read as-is, detect headings via Markdown syntax or ALL-CAPS lines.
- [ ] **REQ-BTE-002**: Build a document structure map for each book: chapters, sections, subsections with their page/position ranges. Store as JSON metadata.
- [ ] **REQ-BTE-003**: Chunk each book using a **structure-aware** strategy:
  - Primary split at chapter boundaries.
  - Secondary split at section/paragraph boundaries within chapters.
  - Configurable chunk size (default: 1000 tokens) and overlap (default: 200 tokens).
  - Never split mid-sentence.
  - Each chunk tagged with: `book_id`, `chapter_title`, `chapter_number`, `section_title`, `page_start`, `page_end`, `chunk_index`, `total_chunks`.
- [ ] **REQ-BTE-004**: Handle front matter (preface, foreword, introduction) and back matter (appendix, index, bibliography, glossary) as separate labeled sections.
- [ ] **REQ-BTE-005**: Detect and skip non-text content: images, tables of figures, blank pages, decorative pages. Log skipped content with page numbers.
- [ ] **REQ-BTE-006**: Produce a text extraction report per book: total characters extracted, chapter count, chunk count, pages with no extractable text, warnings.

**Edge cases:**

- Scanned PDFs (image-only, no text layer): detect and log; optionally fall back to OCR (Tesseract) if available, otherwise mark as `extraction_failed`.
- Books with no chapter structure: chunk by paragraph groups, use page ranges as section identifiers.
- Very short books (< 10 pages): may produce only a few chunks — set minimum chunk count to 1.
- Very long books (1000+ pages): process in streaming fashion, report progress, avoid loading entire text into memory.
- Mixed-language books: detect language per chunk, store as chunk metadata.
- Footnotes and endnotes: include in the chunk where they are referenced, tagged as `content_type=footnote`.

### Feature 5: Vector Embedding Pipeline

- [ ] **REQ-VEP-001**: For each chunk produced by the text extraction pipeline, generate an embedding vector using the configured model (default: `BAAI/bge-large-en-v1.5`, dimension 1024).
- [ ] **REQ-VEP-002**: Store embeddings in Qdrant in a dedicated `books` collection (separate from the general `sources` collection) with the following payload metadata per point:
  - `book_id`: unique identifier for the book.
  - `title`: book title.
  - `author`: book author(s).
  - `isbn`: ISBN if available.
  - `chapter_title`: chapter the chunk belongs to.
  - `chapter_number`: chapter ordinal.
  - `section_title`: section within the chapter (if applicable).
  - `page_start`, `page_end`: page range of the chunk.
  - `chunk_index`: ordinal index of the chunk within the book.
  - `total_chunks`: total chunks in the book.
  - `content_type`: `body`, `preface`, `appendix`, `glossary`, `bibliography`, `footnote`.
  - `language`: detected language of the chunk.
  - `file_format`: original book file format.
  - `tags`: user-assigned tags from the book catalog.
- [ ] **REQ-VEP-003**: Process books in batches (configurable batch size, default: 32 chunks per batch) to manage memory and GPU utilization.
- [ ] **REQ-VEP-004**: Track embedding progress per book in the catalog: `pending`, `in_progress`, `completed`, `failed`. Report overall progress (books completed / total, chunks embedded / total).
- [ ] **REQ-VEP-005**: Support incremental embedding — if a book has already been embedded, skip it unless `--force` is specified. Detect changes via content hash comparison.
- [ ] **REQ-VEP-006**: After embedding, register each book as a source in the existing Knowledge Hub catalog (via `CatalogService`) so that RAG chat, Q&A generation, summarization, and interview features can access book content.
- [ ] **REQ-VEP-007**: Create Qdrant collection with appropriate configuration:
  - Distance metric: cosine similarity.
  - Payload indexing on `book_id`, `author`, `chapter_number`, `content_type`, `tags` for filtered search.
  - HNSW parameters tuned for the collection size (ef_construct, m).
- [ ] **REQ-VEP-008**: Validate embedding quality by running a sample query per book (e.g., search for the book's title) and verifying the top result belongs to that book. Log validation results.

**Edge cases:**

- Embedding model OOM on large batches: reduce batch size dynamically, log memory usage.
- Qdrant connection failures: retry with backoff, checkpoint progress so resumed runs pick up where they left off.
- Books with only a few chunks: still embed, but log as potentially low-quality for RAG.
- Unicode/encoding errors in chunk text: sanitize before embedding, log problematic chunks.

### Feature 6: Knowledge Graph Construction

- [ ] **REQ-KGC-001**: Deploy or connect to a Neo4j instance (local or remote). Store connection configuration in the settings (`NEO4J__URL`, `NEO4J__USER`, `NEO4J__PASSWORD`).
- [ ] **REQ-KGC-002**: Define the knowledge graph schema with the following node types:
  - `Book`: properties — `id`, `title`, `author`, `isbn`, `publisher`, `year`, `language`, `page_count`, `file_format`.
  - `Author`: properties — `name`, `aliases` (JSON), `description`.
  - `Chapter`: properties — `book_id`, `title`, `number`, `page_start`, `page_end`.
  - `Entity`: properties — `name`, `type` (person, organization, place, technology, concept, theory, event), `description`, `aliases` (JSON), `first_mention_book_id`.
  - `Topic`: properties — `name`, `description`, `parent_topic_id`.
- [ ] **REQ-KGC-003**: Define the following relationship types:
  - `AUTHORED_BY` (Book → Author)
  - `HAS_CHAPTER` (Book → Chapter)
  - `MENTIONS` (Chapter → Entity, with `frequency` and `context_snippet` properties)
  - `DISCUSSES` (Chapter → Topic, with `depth` property: `surface`, `moderate`, `deep`)
  - `RELATED_TO` (Entity → Entity, with `relationship_type` and `confidence` properties)
  - `PART_OF` (Entity → Entity, e.g., sub-concept of broader concept)
  - `PRECEDES` (Entity → Entity, temporal or logical ordering)
  - `SUPPORTS` (Entity → Entity, one theory/concept supports another)
  - `CONTRADICTS` (Entity → Entity, conflicting theories or claims)
  - `CROSS_REFERENCED` (Book → Book, books that reference common entities/topics)
  - `SUBTOPIC_OF` (Topic → Topic, hierarchical topic taxonomy)
- [ ] **REQ-KGC-004**: Use LLM-based extraction (via the configured LLM — vLLM or Claude) to extract entities and relationships from each chunk. Use structured output prompts that return JSON with entity names, types, and relationships.
- [ ] **REQ-KGC-005**: Implement entity resolution across books:
  - Normalize entity names (case, whitespace, common abbreviations).
  - Merge entities with matching names and types.
  - Use embedding similarity to detect near-duplicate entities (e.g., "ML" vs "Machine Learning").
  - Log all merge decisions for auditability.
- [ ] **REQ-KGC-006**: Build cross-book relationships:
  - When the same entity appears in multiple books, create `CROSS_REFERENCED` edges between those books.
  - Compute cross-book topic overlap and create `RELATED_TO` edges between books that share significant topic coverage.
- [ ] **REQ-KGC-007**: Track knowledge graph construction progress per book in the catalog: `pending`, `in_progress`, `completed`, `failed`. Report entity counts and relationship counts.
- [ ] **REQ-KGC-008**: Provide a graph statistics endpoint: total nodes by type, total relationships by type, most connected entities, most cross-referenced books.

**Edge cases:**

- LLM extraction returns malformed JSON: retry with rephrased prompt, fall back to regex-based extraction, log failures.
- Entity explosion (too many low-quality entities): set a minimum frequency threshold (entity must appear in at least N chunks), allow post-processing pruning.
- Neo4j connection failures during batch insertion: checkpoint progress, retry failed batches.
- Ambiguous entities (e.g., "Python" — language or snake): use surrounding context from the chunk to disambiguate, store both possibilities if uncertain.
- Very large books producing thousands of entities: batch graph insertions, use `UNWIND` for bulk Cypher operations.

### Feature 7: Knowledge Graph API & Visualization

- [ ] **REQ-KGV-001**: Provide API endpoints for querying the knowledge graph:
  - `GET /api/v1/graph/search?q={query}` — search entities and topics by name (fuzzy match).
  - `GET /api/v1/graph/entity/{id}` — get entity details with all connected nodes (1-hop neighborhood).
  - `GET /api/v1/graph/entity/{id}/path/{target_id}` — find shortest path between two entities.
  - `GET /api/v1/graph/book/{book_id}` — get all entities and topics extracted from a specific book.
  - `GET /api/v1/graph/book/{book_id}/related` — get books related to a given book (via shared entities/topics).
  - `GET /api/v1/graph/topics` — get the topic taxonomy tree.
  - `GET /api/v1/graph/stats` — graph statistics (node counts, relationship counts, top entities).
- [ ] **REQ-KGV-002**: Support graph traversal queries with configurable depth (default: 2 hops) and filtering by node type and relationship type.
- [ ] **REQ-KGV-003**: Add a "Knowledge Graph" page to the frontend with an interactive force-directed graph visualization:
  - Nodes colored by type (books, authors, entities, topics).
  - Edges labeled with relationship type.
  - Click a node to expand its neighborhood.
  - Search to focus on a specific entity or book.
  - Filter by node type, relationship type, and book.
  - Zoom, pan, and drag for exploration.
- [ ] **REQ-KGV-004**: On the book detail page, show a mini knowledge graph showing the book's entities and their cross-book connections.
- [ ] **REQ-KGV-005**: Integrate the knowledge graph with the RAG pipeline: when answering a question, optionally retrieve relevant knowledge graph context (related entities, cross-book connections) to augment the LLM prompt. This enables "graph-augmented RAG."

## 5. Non-Functional Requirements

- [ ] **REQ-NFR-V2-001**: **Performance** — Full processing (download + extract + embed + graph) of a 500-page book should complete within 30 minutes. Embedding generation should achieve at least 50 chunks/second on GPU.
- [ ] **REQ-NFR-V2-002**: **Scalability** — Support a library of up to 5,000 books and 5 million chunks in Qdrant. Neo4j graph should handle up to 1 million nodes and 5 million relationships without query degradation.
- [ ] **REQ-NFR-V2-003**: **Reliability** — All processing pipelines must be resumable. A crash mid-processing should not corrupt previously completed work. Use checkpointing at the book level.
- [ ] **REQ-NFR-V2-004**: **Storage** — Plan for ~500 GB of raw book storage. Embeddings in Qdrant will consume ~20 GB for 5 million 1024-dim vectors. Ensure the target server has sufficient disk.
- [ ] **REQ-NFR-V2-005**: **Idempotency** — Running the seeding script multiple times should not create duplicates. Use content hashes and catalog status to skip already-processed books.
- [ ] **REQ-NFR-V2-006**: **Observability** — Log all pipeline stages with structured logging. Expose metrics: books downloaded, books processed, chunks created, embeddings stored, entities extracted, graph nodes created.
- [ ] **REQ-NFR-V2-007**: **Data Integrity** — Verify content hashes after download. Validate embedding dimensions before Qdrant insertion. Validate Neo4j node/relationship schemas before insertion.

## 6. Tech Stack Additions (v2)

| Component | Technology | Notes |
|-----------|-----------|-------|
| Google Drive API | `google-api-python-client`, `google-auth-oauthlib` | Already in `cloud` extras |
| EPUB parsing | `ebooklib` | New dependency |
| MOBI/AZW parsing | `calibre` (CLI) or `KindleUnpack` | External tool or new dependency |
| DJVU parsing | `python-djvulibre` or `djvutxt` (CLI) | External tool |
| OCR (optional) | `pytesseract` + `Pillow` | For scanned PDFs |
| Cover extraction | `pypdf`, `ebooklib`, `Pillow` | Thumbnail generation |
| ISBN lookup | Open Library API, Google Books API | HTTP calls via `httpx` |
| Knowledge graph | Neo4j + `neo4j` Python driver | New dependency |
| Graph visualization | `react-force-graph` or `d3-force` | Frontend dependency |
| Entity extraction | LLM-based (vLLM or Claude) | Uses existing LLM infrastructure |

## 7. New Project Structure (additions to v1)

```
├── src/
│   ├── data/
│   │   ├── gdrive_downloader.py     # Google Drive download pipeline
│   │   ├── book_parser.py           # Multi-format book text extraction
│   │   └── book_chunker.py          # Structure-aware book chunking
│   ├── models/
│   │   └── graph_extractor.py       # LLM-based entity/relationship extraction
│   ├── features/
│   │   └── knowledge_graph.py       # Knowledge graph query and traversal logic
│   ├── catalog/
│   │   └── book_repository.py       # Book-specific catalog CRUD
│   └── utils/
│       └── graph_store.py           # Neo4j connection and operations wrapper
├── scripts/
│   ├── seed_books.sh                # One-time seeding orchestrator
│   ├── download_books.py            # Google Drive download script
│   ├── process_books.py             # Text extraction + embedding pipeline
│   ├── build_knowledge_graph.py     # Knowledge graph construction script
│   └── start_neo4j.sh               # Start/stop Neo4j (Docker)
├── frontend/src/
│   ├── pages/
│   │   ├── Library.tsx              # Book library browse/search page
│   │   └── KnowledgeGraph.tsx       # Interactive graph visualization
│   └── components/
│       ├── BookCard.tsx              # Book grid card component
│       ├── BookDetail.tsx            # Book detail view
│       └── GraphViewer.tsx           # Force-directed graph component
├── configs/
│   └── local.yaml                   # Add neo4j section
└── data/
    ├── books/                       # Downloaded book files (organized by author/title)
    └── covers/                      # Extracted/generated cover images
```

## 8. Configuration Additions

| Env Var | Default | Description |
|---------|---------|-------------|
| `GDRIVE__CREDENTIALS_FILE` | `credentials.json` | Path to Google OAuth credentials file |
| `GDRIVE__TOKEN_FILE` | `token.json` | Path to stored OAuth token |
| `GDRIVE__FOLDER_ID` | (required) | Google Drive folder ID containing books |
| `BOOKS__STORAGE_DIR` | `data/books` | Local directory for downloaded books |
| `BOOKS__COVERS_DIR` | `data/covers` | Local directory for cover images |
| `BOOKS__CHUNK_SIZE` | `1000` | Tokens per chunk |
| `BOOKS__CHUNK_OVERLAP` | `200` | Token overlap between chunks |
| `BOOKS__EMBEDDING_BATCH_SIZE` | `32` | Chunks per embedding batch |
| `BOOKS__QDRANT_COLLECTION` | `books` | Qdrant collection name for book embeddings |
| `NEO4J__URL` | `bolt://localhost:7687` | Neo4j connection URL |
| `NEO4J__USER` | `neo4j` | Neo4j username |
| `NEO4J__PASSWORD` | (required) | Neo4j password |
| `NEO4J__DATABASE` | `knowledgehub` | Neo4j database name |

## 9. Scripts & Commands

```bash
# Full one-time seeding (download → catalog → embed → graph)
bash scripts/seed_books.sh

# Individual steps (for debugging or partial re-runs)
uv run python scripts/download_books.py --folder-id <DRIVE_FOLDER_ID>
uv run python scripts/download_books.py --resume        # Resume interrupted download
uv run python scripts/process_books.py                  # Extract text + create embeddings
uv run python scripts/process_books.py --book-id <ID>   # Process a single book
uv run python scripts/process_books.py --force           # Re-process already completed books
uv run python scripts/build_knowledge_graph.py           # Build graph from all processed books
uv run python scripts/build_knowledge_graph.py --book-id <ID>  # Graph a single book

# Neo4j management
bash scripts/start_neo4j.sh                              # Start Neo4j (Docker)
bash scripts/start_neo4j.sh stop                         # Stop Neo4j
bash scripts/start_neo4j.sh status                       # Check Neo4j status

# Verify seeding results
uv run python scripts/verify_seeding.py                  # Check download, embedding, graph completeness
```

## 10. API Endpoints (additions to v1, prefix: `/api/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/books` | List all books with filters (author, year, format, tags, search) |
| `GET` | `/books/{id}` | Get book details with full metadata |
| `PUT` | `/books/{id}` | Update book metadata (title, author, tags, description) |
| `DELETE` | `/books/{id}` | Delete book, its embeddings, and graph nodes |
| `GET` | `/books/{id}/chapters` | Get table of contents / chapter list |
| `GET` | `/books/{id}/cover` | Get cover image |
| `GET` | `/books/{id}/original` | Download original book file |
| `GET` | `/books/{id}/view` | View book in-browser |
| `GET` | `/books/{id}/status` | Get processing status (download, embed, graph) |
| `GET` | `/books/stats` | Library statistics (total books, by format, by language, processing status) |
| `GET` | `/graph/search` | Search entities and topics in the knowledge graph |
| `GET` | `/graph/entity/{id}` | Get entity details with connected nodes |
| `GET` | `/graph/entity/{id}/path/{target_id}` | Find shortest path between entities |
| `GET` | `/graph/book/{book_id}` | Get entities/topics from a specific book |
| `GET` | `/graph/book/{book_id}/related` | Get books related via shared entities |
| `GET` | `/graph/topics` | Get topic taxonomy tree |
| `GET` | `/graph/stats` | Graph statistics |

## 11. Seeding Workflow (One-Time Process)

```
┌─────────────────────────────────────────────────────────────────┐
│                     seed_books.sh                               │
│                                                                 │
│  Step 1: Download from Google Drive                             │
│  ┌───────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Auth with     │───▶│ List files   │───▶│ Download     │     │
│  │ Google Drive  │    │ recursively  │    │ to data/books│     │
│  └───────────────┘    └──────────────┘    └──────┬───────┘     │
│                                                   │             │
│  Step 2: Catalog & Metadata                       ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Extract       │───▶│ Enrich via   │───▶│ Store in     │     │
│  │ metadata      │    │ ISBN/API     │    │ catalog DB   │     │
│  └───────────────┘    └──────────────┘    └──────┬───────┘     │
│                                                   │             │
│  Step 3: Text & Embeddings                        ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Extract text  │───▶│ Chunk with   │───▶│ Embed &      │     │
│  │ per format    │    │ structure    │    │ store Qdrant │     │
│  └───────────────┘    └──────────────┘    └──────┬───────┘     │
│                                                   │             │
│  Step 4: Knowledge Graph                          ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Extract       │───▶│ Resolve      │───▶│ Build Neo4j  │     │
│  │ entities/rels │    │ entities     │    │ graph        │     │
│  └───────────────┘    └──────────────┘    └──────┬───────┘     │
│                                                   │             │
│  Step 5: Verification                             ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Verify        │───▶│ Sample RAG   │───▶│ Report       │     │
│  │ completeness  │    │ queries      │    │ results      │     │
│  └───────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## 12. Testing & Validation

- **Unit tests**: Book parsers (PDF, EPUB, DOCX extraction), chunking strategy, metadata extraction, entity extraction prompts, Neo4j query builders.
- **Integration tests**: Full pipeline — download mock file → extract → chunk → embed → verify in Qdrant. Knowledge graph — extract entities → insert into Neo4j → query back.
- **Evaluation tests**: Embedding quality (sample queries return relevant book chunks), entity extraction precision (manual review of extracted entities from sample chapters).
- **Acceptance criteria**:
  - All books from the Drive folder are downloaded and cataloged.
  - Each book has extracted metadata with at least title and file format populated.
  - All cataloged books have embeddings in Qdrant.
  - Knowledge graph contains nodes for all books and their extracted entities.
  - RAG chat can answer questions using book content with correct citations.
  - Library web page displays all books with covers and metadata.
  - Knowledge graph visualization renders and is navigable.
  - `verify_seeding.py` reports 100% completion with no errors.

## 13. Out of Scope

- Real-time sync with Google Drive (this is a one-time seed operation).
- User authentication or multi-tenancy (single-user, as per v1).
- Audio book processing.
- Image/diagram extraction and indexing from books.
- Full-text search engine (Elasticsearch/Meilisearch) — rely on Qdrant semantic search and SQLite full-text for now.
- Knowledge graph editing or manual curation via UI (read-only visualization in v2).
- Automated knowledge graph reasoning or inference (just storage and traversal).

## 14. Dependencies on v1

This specification builds on top of v1 and assumes the following v1 features are implemented:

- Content ingestion pipeline (`src/data/ingestion.py`) — used to register books as sources.
- Catalog service (`src/catalog/`) — book entries integrate with the source catalog.
- RAG pipeline (`src/pipelines/rag.py`) — books become queryable via existing RAG chat.
- Document viewer (Feature 6) — books viewable in-browser via existing viewer.
- Vector store abstraction (`src/utils/vector_store.py`) — embedding storage in Qdrant.
- Frontend pages (Sources, Chat) — Library page follows existing patterns.
- Settings and configuration (`src/utils/config.py`) — new settings extend existing structure.
