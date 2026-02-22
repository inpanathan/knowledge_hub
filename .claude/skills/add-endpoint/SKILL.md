---
name: add-endpoint
description: Scaffold a new API endpoint following project patterns, including route, models, and tests
disable-model-invocation: true
argument-hint: "[method] [path] [description]"
---

Add a new API endpoint based on: $ARGUMENTS

1. Read `src/api/routes.py` and `main.py` to understand existing patterns
2. Read `src/utils/errors.py` for error handling conventions

3. Implement the endpoint in `src/api/routes.py`:
   - Define Pydantic request/response models in the same file (or a separate `src/api/schemas.py` if one exists)
   - Add the route to the existing `router` — it mounts at `/api/v1` automatically
   - Use `async def` for the handler
   - Add type hints for parameters and return type
   - Raise `AppError(code=ErrorCode.X, ...)` for error cases
   - Log key events with `logger.info("event_name", key=value)`

4. Write tests in `tests/integration/test_api.py`:
   - Use the existing `client` fixture (TestClient with lifespan)
   - Test the happy path
   - Test validation errors (400)
   - Test not-found cases (404) if applicable

5. Run quality checks:
   ```bash
   uv run ruff check src/ tests/ --fix && uv run mypy src/ --ignore-missing-imports && uv run pytest tests/ -x -q
   ```

6. Fix any failures before finishing
