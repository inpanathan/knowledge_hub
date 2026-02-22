---
paths:
  - "tests/**/*.py"
---

# Testing Conventions

## Structure
- Unit tests: `tests/unit/` — mirrors `src/` directory structure
- Integration tests: `tests/integration/` — API and cross-module tests
- Evaluation tests: `tests/evaluation/` — model quality and performance
- Safety tests: `tests/safety/` — security and adversarial input
- Fixtures: `tests/fixtures/` — shared test data files

## Naming
- Test files: `test_<module>.py`
- Test functions: `test_<what>_<scenario>` (e.g., `test_create_item_with_missing_field_returns_422`)
- Fixtures: descriptive nouns (e.g., `client`, `sample_item`, `auth_headers`)

## Patterns
- Use `pytest.fixture()` decorator, not setup/teardown methods
- API tests use the `client` fixture from `TestClient(create_app())` with lifespan context
- Assert on specific values in response body, not just status codes
- One assertion focus per test — test one behavior, not multiple
- Tests must be independent — no shared mutable state, no ordering dependencies
- Use `pytest.raises(AppError)` for testing error cases, check `.code` on the caught exception

## What not to do
- Don't mock structlog or the config singleton unless explicitly needed
- Don't mock FastAPI internals — use the real TestClient
- Don't use `unittest.TestCase` — use plain pytest functions
- Don't write tests that depend on external services without a skip marker
