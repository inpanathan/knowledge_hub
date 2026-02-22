---
paths:
  - "src/api/**/*.py"
  - "tests/integration/**/*.py"
---

# API Conventions

## Endpoints
- All routes go on the `router` in `src/api/routes.py` — it mounts at `/api/v1` in `main.py`
- Use `async def` for all handlers
- Use HTTP method decorators: `@router.get`, `@router.post`, `@router.put`, `@router.delete`
- Use plural nouns for resource paths: `/items`, `/users`, `/predictions`
- Return Pydantic response models, not raw dicts

## Request/Response models
- Define Pydantic models for all request bodies and response shapes
- Use `Field(...)` for required fields with descriptions
- Name models with suffix: `ItemCreate`, `ItemResponse`, `ItemList`
- List responses should include a count: `{"items": [...], "count": N}`

## Error handling
- Raise `AppError(code=ErrorCode.X, message="...", context={...})` for all error cases
- Never return raw `{"error": "..."}` dicts — the `AppError` handler in `main.py` does this
- Map error codes to HTTP status: VALIDATION_ERROR=400, UNAUTHORIZED=401, NOT_FOUND=404, RATE_LIMITED=429

## Logging
- Log at entry and exit of significant operations: `logger.info("items_listed", count=len(items))`
- Use snake_case event names, not sentences
- Include relevant IDs and counts as structured fields
