---
paths:
  - "src/**/*.py"
---

# Security Rules

## Input validation
- Validate all external inputs (API params, file paths, URLs) before use
- Prevent path traversal — use `Path.resolve()` and check against allowed directories
- Validate file uploads server-side by content type, not just extension; enforce `settings.ingestion.max_file_size_mb`
- Sanitize user inputs before including in LLM prompts; separate system content from user content in prompt construction

## Secrets and credentials
- Never log API keys, tokens, or credentials; access secrets only via `settings.llm.api_key`
- Never hardcode secrets — use environment variables or `settings` singleton
- Never commit `.env` files; only `.env.example` with placeholder values

## Dangerous operations
- No `eval()`, `exec()`, `os.system()`, or `subprocess(shell=True)`
- No `pickle.load()` on untrusted data — use safe serialization formats (JSON, YAML)
- No `__import__()` with user-supplied strings

## Reference
- REQ-SEC-001: Secrets in env vars / secrets manager, never in VCS
- REQ-SEC-002: Validate and sanitize all external inputs
- REQ-SEC-003: Prompt injection defenses for LLM-facing inputs
