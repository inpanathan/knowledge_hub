# Plan: Local GPU Stack — vLLM + Qdrant + BGE Embeddings

## Context

Knowledge Hub currently runs entirely on mocks (`MODEL_BACKEND=mock`) with ChromaDB for vectors and an Anthropic SDK client for LLM. The server has an **RTX 3090 (24 GB VRAM)**. This plan migrates to a local GPU stack:

- **vLLM** serving Qwen2.5-14B-Instruct (configurable) via OpenAI-compatible API
- **Qdrant** (Docker) replacing ChromaDB for vector storage
- **BGE-large-en-v1.5** (1024-dim) replacing all-MiniLM-L6-v2 for embeddings
- All model/infra choices **fully configurable** via settings — swap by config change, no code changes

---

## Phase 1: Dependencies and Configuration [x]

Add packages and config fields. No behavior change — all 65 tests pass unchanged.

### 1.1 [x] Update dependencies
**File:** `pyproject.toml`
- Add `qdrant-client>=1.12.0` and `openai>=1.50.0` to dependencies
- Keep `chromadb` for now (removed in Phase 2)
- Run `uv sync --extra dev`

### 1.2 [x] Add config fields
**File:** `src/utils/config.py`
- `LLMSettings`: add `vllm_base_url: str = "http://localhost:8000/v1"`, `vllm_model: str = "Qwen/Qwen2.5-14B-Instruct"`
- `VectorStoreSettings`: add `url: str = "http://localhost:6333"`
- `EmbeddingSettings`: change defaults to `model_name = "BAAI/bge-large-en-v1.5"`, `dimension = 1024`

### 1.3 [x] Update .env.example
**File:** `.env.example`
- Add `LLM__VLLM_BASE_URL`, `LLM__VLLM_MODEL`, `VECTOR_STORE__URL`, `EMBEDDING__MODEL_NAME`, `EMBEDDING__DIMENSION`

**Acceptance:** `uv sync` succeeds. All 65 tests pass. Ruff + mypy clean.

---

## Phase 2: Rewrite VectorStore to Qdrant [x]

Replace ChromaDB with Qdrant. The public API (`.add()`, `.search()`, `.delete_by_source()`, `.count()`) stays identical. ChromaDB-format `where` filters are translated internally — **zero caller changes**.

### 2.1 [x] Rewrite VectorStore
**File:** `src/utils/vector_store.py` — full rewrite

New constructor:
```python
def __init__(self, *, url: str = "", collection_name: str = "knowledge_hub",
             dimension: int = 1024, in_memory: bool = False) -> None:
```

Key design:
- `in_memory=True` → `QdrantClient(":memory:")` (no Docker needed, used for tests/mock)
- `in_memory=False` → `QdrantClient(url=url)` (connects to Docker Qdrant)
- `_translate_where()` private method converts ChromaDB filter dicts to Qdrant `Filter` objects:
  - `None` → `None`
  - `{"source_id": "x"}` → `Filter(must=[FieldCondition(key="source_id", match=MatchValue(value="x"))])`
  - `{"source_id": {"$in": [...]}}` → `Filter(must=[FieldCondition(key="source_id", match=MatchAny(any=[...]))])`
- Qdrant returns similarity scores directly (higher=better) — no `1-distance` conversion
- `add()` uses `upsert()` with `PointStruct`, text stored in payload
- `delete_by_source()` uses Qdrant filter-based delete
- Auto-creates collection with cosine distance if it doesn't exist

### 2.2 [x] Update DI container
**File:** `src/api/dependencies.py`

Change VectorStore instantiation:
```python
vector_store = VectorStore(
    url=settings.vector_store.url,
    collection_name=settings.vector_store.collection_name,
    dimension=settings.embedding.dimension,
    in_memory=(settings.model_backend == "mock"),
)
```

### 2.3 [x] Update test fixtures
**File:** `tests/conftest.py`

Change `vector_store` fixture to use Qdrant in-memory mode:
```python
def vector_store() -> VectorStore:
    return VectorStore(collection_name="test_collection", dimension=384, in_memory=True)
```

### 2.4 [x] Update 7 integration test client fixtures
**Files:** `tests/integration/test_api.py`, `test_sources.py`, `test_chat.py`, `test_interview.py`, `test_qna.py`, `test_summarization.py`, `test_e2e_flow.py`

Remove `settings.vector_store.persist_directory = ...` line from each. The mock backend auto-uses `in_memory=True`.

### 2.5 [x] Remove ChromaDB
**File:** `pyproject.toml` — remove `chromadb>=0.6.0`
Run `uv sync --extra dev`

**Acceptance:** All 65 tests pass. No caller files (rag.py, interview.py, qna.py, summarization.py) modified. Ruff + mypy clean.

---

## Phase 3: Add vLLM LLM Client [x]

New `VLLMLLMClient` class using OpenAI SDK to talk to vLLM. Wire into factory.

### 3.1 [x] Add VLLMLLMClient
**File:** `src/models/llm.py`

```python
class VLLMLLMClient:
    def __init__(self, base_url, model, temperature, timeout) -> None:
        # Uses openai.OpenAI(base_url=..., api_key="not-needed")

    def generate(self, prompt, *, system="", max_tokens=1024) -> str:
        # Uses client.chat.completions.create() with messages format
```

### 3.2 [x] Update factory
**File:** `src/models/llm.py`

`create_llm_client()` dispatches: `mock` → Mock, `local` → VLLMLLMClient, `cloud` → ClaudeLLMClient. Add `vllm_base_url` and `vllm_model` kwargs.

### 3.3 [x] Update DI container
**File:** `src/api/dependencies.py`

Pass `vllm_base_url` and `vllm_model` from settings to factory.

### 3.4 [x] Add unit tests
**New file:** `tests/unit/test_llm.py`
- Test factory dispatches correctly for mock/local/cloud
- Test VLLMLLMClient instantiation (mock the openai import)

**Acceptance:** All tests pass. `create_llm_client("local")` returns VLLMLLMClient. Ruff + mypy clean.

---

## Phase 4: Scripts and Documentation [x]

### 4.1 [x] Create vLLM start script
**New file:** `scripts/start_vllm.sh`
- Configurable model via arg or `LLM__VLLM_MODEL` env var
- Configurable port, GPU memory utilization
- Kills existing process on port before starting (REQ-RUN-009)

### 4.2 [x] Create Qdrant start/stop script
**New file:** `scripts/start_qdrant.sh`
- Start Qdrant Docker container with persistent storage at `data/qdrant_storage/`
- `bash scripts/start_qdrant.sh stop` to stop
- Idempotent — stops existing container before starting (REQ-RUN-005)

### 4.3 [x] Create local config
**New file:** `configs/local.yaml`
- `model_backend: local`, embedding/LLM/vector store settings for GPU stack

### 4.4 [x] Update .gitignore
Add `data/qdrant_storage/`

### 4.5 [x] Update app cheatsheet
**File:** `docs/app_cheatsheet.md`
- Add "Local GPU Stack" section with startup instructions
- Update Configuration table with new env vars
- Update "Running in Local Mode" checklist

**Acceptance:** Scripts are executable. Docs complete. All tests pass.

---

## Phase 5: Final Validation [x]

### 5.1 [x] Run full quality checks
```bash
bash scripts/check_all.sh
```

### 5.2 [x] Verify mock mode (CI-safe)
```bash
MODEL_BACKEND=mock uv run pytest tests/ -x -q
```

### 5.3 Verify local mode (manual, requires GPU + Docker)
```bash
bash scripts/start_qdrant.sh
bash scripts/start_vllm.sh  # in separate terminal
MODEL_BACKEND=local uv run python main.py
curl http://localhost:8000/health
# POST /api/v1/sources/text → POST /api/v1/chat
```

---

## Files Changed Summary

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| 1 | — | `pyproject.toml`, `src/utils/config.py`, `.env.example` |
| 2 | — | `src/utils/vector_store.py` (rewrite), `src/api/dependencies.py`, `tests/conftest.py`, 7 integration test files |
| 3 | `tests/unit/test_llm.py` | `src/models/llm.py`, `src/api/dependencies.py` |
| 4 | `scripts/start_vllm.sh`, `scripts/start_qdrant.sh`, `configs/local.yaml` | `.gitignore`, `docs/app_cheatsheet.md` |
| 5 | — | — (validation only) |

**Totals:** ~3 new files, ~14 modified files, ~3 new tests

## Key Design Decisions

1. **Filter translation inside VectorStore** — callers keep passing ChromaDB-format dicts, VectorStore translates to Qdrant filters internally. Zero downstream changes.
2. **Qdrant in-memory mode for tests** — `QdrantClient(":memory:")` replaces ChromaDB temp directories. No Docker needed for tests.
3. **OpenAI SDK for vLLM** — standard, well-maintained client. Same code works with any OpenAI-compatible server (vLLM, Ollama, etc.).
4. **Config-driven model selection** — change `LLM__VLLM_MODEL` to switch models, change `EMBEDDING__MODEL_NAME` to switch embeddings. No code changes.
