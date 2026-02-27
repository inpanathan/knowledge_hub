---
paths:
  - "src/**/*.py"
---

# Logging Rules

## Setup
- Use `from src.utils.logger import get_logger` then `logger = get_logger(__name__)`
- Never use `print()` in `src/` — structlog only (Ruff rule T20 enforces this)

## Event naming
- Use `snake_case` verb phrases: `"pdf_parsed"`, `"llm_response_generated"`, `"source_created"`
- Pass structured fields as kwargs, not f-strings: `logger.info("source_created", source_id=sid)`

## Required fields by category
- **Data operations**: `source_id=`, `chunk_count=`, `file_format=`
- **Model operations**: `model=`, `input_tokens=`, `output_tokens=`, `latency_ms=`
- **API operations**: `endpoint=`, `method=`, `status_code=`
- **Errors**: `error_code=`, `error_message=` (use AppError fields)

## Levels
- `DEBUG`: Full prompt/response bodies, detailed chunk content — non-production only
- `INFO`: Operation lifecycle events (started, completed), key metrics
- `WARNING`: Recoverable issues (duplicate detection, skipped files, fallback used)
- `ERROR`: Failed operations that need attention (parse failures, LLM errors)

## Sensitive data
- Never log raw user content, PII, or file contents at INFO level
- Never log API keys, tokens, or credentials at any level
- Use DEBUG level for detailed content, guarded behind log level checks

## Reference
- REQ-LOG-001: Structured logs with queryable fields
- REQ-LOG-006: Redact sensitive data before persisting
- REQ-LOG-008: Consistent standard log levels
- REQ-LOG-012: Centralized shared logger utility
