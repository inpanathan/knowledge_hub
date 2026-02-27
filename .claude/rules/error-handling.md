---
paths:
  - "src/**/*.py"
---

# Error Handling Rules

## Raising errors
- Always raise `AppError(code=ErrorCode.X, message="...", context={...})` — never return raw error dicts
- Chain exceptions with `cause=`: `raise AppError(..., cause=e) from e`
- Include relevant context in `AppError.context` dict (IDs, paths, parameters) for debugging
- Reference `ErrorCode` enum from `src/utils/errors.py` — add new codes there for new failure modes

## Catching errors
- Catch the narrowest exception type needed (REQ-ERR-006)
- No bare `except:` — always specify the exception class
- No broad `except Exception` unless re-raising or at the top-level error handler
- Fallback-to-mock patterns should only catch `ImportError`, not `(ImportError, OSError)`

## External calls
- Set explicit timeouts on all external calls: HTTP requests, database queries, LLM inference (REQ-ERR-003)
- Set explicit `max_tokens` on every LLM `generate()` call — never rely on large defaults (REQ-ERR-007)
- Use retries with exponential backoff for transient failures (REQ-ERR-004)

## Reference
- Error codes: `src/utils/errors.py` — `ErrorCode` enum and `AppError` class
- Exception chaining pattern: `raise AppError(code=..., message=..., cause=e) from e`
