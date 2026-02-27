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

## Data Pipeline

<!-- Add entries as issues are encountered -->
<!-- Template:
### <Short description>

**Symptom:** <What the user sees>

**Root cause:** <Why it happens>

**Diagnostic commands:**
```bash
<commands used to diagnose>
```

**Resolution:** <How to fix it>
-->

---

## Models

### Model fails to load

**Symptom:** `AppError(code=MODEL_LOAD_FAILED)` on first inference call.

**Root cause:** Missing ML dependencies (`torch`, `sentence-transformers`) or model weights not downloaded.

**Diagnostic commands:**
```bash
# Check ML deps are installed
uv run python -c "import torch; print('OK')"

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

---

## Testing

<!-- Add entries as issues are encountered -->

---

## Deployment

<!-- Add entries as issues are encountered -->
