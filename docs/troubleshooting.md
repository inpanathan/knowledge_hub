# Troubleshooting Guide

This is a living document. Update it after resolving non-trivial debugging sessions (REQ-AGT-004).

For each issue, document: symptom, root cause, diagnostic commands used, and resolution.

---

## General

### Application fails to start

**Symptom:** `uvicorn` exits immediately or throws `ConfigError` on startup.

**Root cause:** Missing or invalid configuration — `.env` not created, required env vars unset, or invalid YAML in `configs/`.

**Diagnostic commands:**
```bash
# Check if .env exists
ls -la .env

# Validate config loads
uv run python -c "from src.utils.config import settings; print(settings)"

# Check for YAML syntax errors
uv run python -c "import yaml; yaml.safe_load(open('configs/dev.yaml'))"
```

**Resolution:** Copy `.env.example` to `.env` and fill in required values. Run `bash scripts/setup.sh` for first-time setup.

---

## Ingestion Pipeline

### PDF parsing fails with encoding errors

**Symptom:** `AppError(code=PARSE_FAILED)` when ingesting certain PDFs.

**Root cause:** PDF contains scanned images without OCR text layer, or uses non-standard encoding.

**Diagnostic commands:**
```bash
# Check if PDF has extractable text
uv run python -c "from pypdf import PdfReader; r = PdfReader('path/to/file.pdf'); print(len(r.pages[0].extract_text()))"
```

**Resolution:** Verify the PDF has a text layer. Image-only PDFs are not supported in v1 (text extraction only).

### URL fetch times out

**Symptom:** `AppError(code=URL_FETCH_FAILED)` with timeout error.

**Diagnostic commands:**
```bash
# Test URL accessibility
curl -sI --max-time 10 "https://example.com/page"

# Check timeout config
uv run python -c "from src.utils.config import settings; print(settings.ingestion.url_timeout)"
```

**Resolution:** Check if the URL is accessible from the server. Increase `INGESTION__URL_TIMEOUT` if the site is slow. Check for firewall or proxy issues.

---

## RAG / Chat

### Chat returns "no relevant context found"

**Symptom:** Chat responses indicate no indexed content matches the query, even when relevant documents are indexed.

**Root cause:** Embedding mismatch, empty vector store, or similarity threshold too high.

**Diagnostic commands:**
```bash
# Check vector store has entries
uv run python -c "from src.utils.vector_store import get_vector_store; vs = get_vector_store(); print(vs.count())"

# Check embedding model is loaded
uv run python -c "from src.models.embeddings import create_embedding_model; m = create_embedding_model(); print(type(m))"
```

**Resolution:** Verify documents were fully ingested (check catalog for chunk count > 0). Try lowering the similarity threshold in settings. Re-index if the embedding model was changed.

---

## Models

### Model fails to load

**Symptom:** `AppError(code=MODEL_LOAD_FAILED)` on first inference call.

**Root cause:** Missing ML dependencies (`torch`, `sentence-transformers`) or model weights not downloaded.

**Diagnostic commands:**
```bash
# Check ML deps are installed
uv run python -c "import torch; import sentence_transformers; print('OK')"

# Check model backend setting
uv run python -c "from src.utils.config import settings; print(settings.model_backend)"
```

**Resolution:** Install ML extras with `uv sync --extra dev --extra ml`. For local models, run `bash scripts/download_models.sh`. For development, set `MODEL_BACKEND=mock` in `.env`.

---

## Configuration

### Environment variable not taking effect

**Symptom:** Changed an env var in `.env` but the application still uses the old value.

**Root cause:** Layered config precedence — YAML values passed as explicit constructor kwargs can override env vars. Or the application wasn't restarted.

**Diagnostic commands:**
```bash
# Print resolved config
uv run python -c "from src.utils.config import settings; print(settings.model_dump_json(indent=2))"

# Check .env is being loaded
grep "VARIABLE_NAME" .env
```

**Resolution:** Restart the application. Check `configs/dev.yaml` isn't overriding the value. Env vars use `__` for nesting (e.g., `LLM__API_KEY`). See REQ-CFG-007.
