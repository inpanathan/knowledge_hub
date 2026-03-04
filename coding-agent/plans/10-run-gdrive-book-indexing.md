# Run Google Drive Book Indexing Pipeline

## Context
User wants to index books from a specific Google Drive folder using the existing pipeline (download → embed → knowledge graph). All infrastructure code is already built (Plans 6-9). This is an operational run, not new implementation.

## Prerequisites
- Google Drive OAuth credentials at `configs/gdrive_credentials.json` (already exists)
- Google Drive folder ID (user will provide)
- Services: Qdrant (vector store), vLLM (LLM inference), Neo4j (knowledge graph)

## Steps

### 1. Configure folder ID
- [x] Set `GOOGLE_DRIVE__FOLDER_ID` in `.env` with the user's folder ID

### 2. Authenticate with Google Drive
- [x] Run `uv run python scripts/authenticate_gdrive_console.py` (two-step: URL + paste code)
- [x] Verify token saved at `data/gdrive_token.json`
- [x] Note: switched from desktop to web OAuth app; updated credentials and gdrive_client

### 3. Start infrastructure services
- [ ] Start Qdrant: `bash scripts/start_qdrant.sh`
- [ ] Start Neo4j: `bash scripts/start_neo4j.sh`
- [ ] Start vLLM: `bash scripts/start_vllm.sh` (port 8001)

### 4. Dry run (preview)
- [ ] Run `bash scripts/seed_books.sh --dry-run` to list files without downloading

### 5. Run full pipeline
- [ ] Run `bash scripts/seed_books.sh` (download → embed → graph)
- Alternatively for overnight: `nohup bash scripts/seed_books.sh > data/seed_books.log 2>&1 &`

### 6. Verify
- [ ] Check `bash scripts/seed_books.sh status` for counts
- [ ] Start app server and check `/api/v1/books` endpoint

## Notes
- Pipeline is idempotent — safe to re-run (skips already-downloaded files)
- Use `--skip-embed` or `--skip-graph` flags to run partial pipeline
- Logs go to stdout (or redirect to file for overnight runs)
