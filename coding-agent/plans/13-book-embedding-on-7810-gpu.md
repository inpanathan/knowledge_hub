# Plan 13: Run Book Embedding Pipeline on 7810 (GPU)

## Context

The book embedding pipeline (`scripts/process_books.py`) uses sentence-transformers (`BAAI/bge-large-en-v1.5`) to embed book chunks into Qdrant. Currently configured for CPU. The 7810 node has 2× idle RTX 3060 GPUs (12GB each) that can accelerate this significantly. We'll set up 7810 to run the pipeline with `EMBEDDING__DEVICE=cuda`, test with one book first, then the user will handle the frontend.

## Current State

- **7810**: Python 3.13, 2× RTX 3060, no `uv`, no project code, no book files
- **3090-1** (current machine): project code, 66 books (1.1GB, all `pending`), `data/catalog.db`, Qdrant on port 6333
- **Network**: 7810 → Qdrant on 3090-1 via Tailscale (`100.111.249.61:6333`) — verified working
- **Book paths in DB**: relative (`data/books/...`) — will work once project is synced
- **No code changes needed** — all config via env vars

## Steps

### Step 1: Install `uv` on 7810
- [x] Installed uv 0.10.8 on 7810

### Step 2: Rsync project + books to 7810
- [x] Synced project to 7810 (29,740 files)
- [!] **Gotcha**: `--exclude 'models/'` also excluded `src/models/` — fixed with targeted rsync of `src/models/`

### Step 3: Install Python dependencies on 7810
- [x] `uv sync --extra dev --extra ml` — 201 packages installed (Python 3.12.13, torch 2.9.1, CUDA 12.8)

### Step 4: Run dry-run
- [x] Dry run successful — 66 pending books found
- [!] **Gotcha**: `APP_ENV=local` uses `local.yaml` which hardcodes `vector_store.url=localhost:6333` via kwargs (overrides env vars per REQ-CFG-007). Fix: use default `APP_ENV=dev` with env var overrides instead.
- Working command:
  ```bash
  ssh vinpanathan-precision-tower-7810 "cd ~/projects/knowledge_hub && \
    MODEL_BACKEND=local \
    VECTOR_STORE__URL=http://100.111.249.61:6333 \
    EMBEDDING__DEVICE=cuda \
    ~/.local/bin/uv run python scripts/process_books.py --dry-run"
  ```

### Step 5: Process one book
- [x] Processed "Fuzzy Data Matching With SQL" (1.9MB, 285 pages)
  - 162 chunks, 97,429 tokens
  - **17.9 seconds** on RTX 3060 GPU
  - Book ID: `630b3165-713d-42a2-b77b-92d448d49b5b`

### Step 6: Verify
- [x] Book status: `completed` in catalog DB
- [x] Qdrant `books` collection: 162 points, status green
- [x] Synced updated `catalog.db` back to 3090-1 (1 completed, 65 pending)

## Verification

1. ✅ `--dry-run` lists 66 pending books
2. ✅ Single book processes without errors, status → `completed`
3. ✅ Qdrant `books` collection shows 162 points
4. ⏭️ `nvidia-smi` not checked (pipeline completed successfully with `device=cuda` in logs)

## Command to Process All Remaining Books

```bash
ssh vinpanathan-precision-tower-7810 "cd ~/projects/knowledge_hub && \
  MODEL_BACKEND=local \
  VECTOR_STORE__URL=http://100.111.249.61:6333 \
  EMBEDDING__DEVICE=cuda \
  ~/.local/bin/uv run python scripts/process_books.py"
```

After completion, sync catalog.db back:
```bash
rsync -az vinpanathan-precision-tower-7810:/home/vinpanathan/projects/knowledge_hub/data/catalog.db \
  /home/vinpanathan/projects/knowledge_hub/data/catalog.db
```
