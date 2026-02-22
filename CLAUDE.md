# AI/ML Project Template

## Commands

```bash
# Dev server
uv run python main.py

# Tests (prefer running single test files, not the full suite)
uv run pytest tests/ -x -q                          # all tests
uv run pytest tests/unit/ -x -q                     # unit only
uv run pytest tests/integration/ -x -q              # integration only
uv run pytest tests/unit/test_foo.py -x -q           # single file
uv run pytest tests/unit/test_foo.py::test_bar -x -q # single test

# Lint and typecheck
uv run ruff check src/ tests/                       # lint
uv run ruff check src/ tests/ --fix                 # lint + autofix
uv run ruff format src/ tests/                      # format
uv run mypy src/ --ignore-missing-imports            # typecheck

# Full quality check (run before committing)
bash scripts/check_all.sh                            # lint + format + typecheck + tests
bash scripts/check_all.sh --fix                      # same, but auto-fix lint/format first

# Dependencies
uv sync --extra dev                                  # install dev deps
uv sync --extra dev --extra ml                       # install dev + ML deps
uv add <package>                                     # add a dependency

# Requirements sync
bash scripts/sync_requirements.sh                    # sync requirement controllers
bash scripts/sync_requirements.sh --dry-run          # preview changes
```

## Code style

- Python 3.12+, use modern syntax (`type X = ...`, `X | Y` unions, `StrEnum`)
- Line length: 100 characters
- Use `from __future__ import annotations` in every module
- ES-style imports: `from src.utils.config import settings` (not relative)
- Ruff rules: E, F, W, I, N, UP, B, SIM, T20 — no `print()` in src/ (use structlog)
- Type hints on all function signatures; use `TYPE_CHECKING` for import-only types
- Pydantic models for all data structures that cross boundaries (API, config, serialization)

## Architecture

- **Entry point**: `main.py` — creates FastAPI app, mounts routes at `/api/v1`
- **Config**: `src/utils/config.py` — layered: defaults < `configs/{APP_ENV}.yaml` < env vars. Import `settings` singleton
- **Logging**: `src/utils/logger.py` — structlog. Use `get_logger(__name__)`, log with `logger.info("event_name", key=value)`
- **Errors**: `src/utils/errors.py` — raise `AppError(code=ErrorCode.X, message="...", context={...})`
- **Routes**: `src/api/routes.py` — add endpoints to `router`, they mount at `/api/v1`
- **Source modules**: `src/data/`, `src/models/`, `src/features/`, `src/pipelines/`, `src/evaluation/`

## Patterns to follow

- New endpoints: add to `src/api/routes.py`, follow existing FastAPI patterns, include request/response Pydantic models
- New config values: add to `Settings` or a nested `*Settings` class in `src/utils/config.py`, then use via `settings.x`
- Error handling: raise `AppError` with an `ErrorCode`, never return raw dicts with error info
- Logging: always use structlog, never `print()`. Use event-style names: `logger.info("model_loaded", model_id=...)`
- Tests: mirror src/ structure in tests/. Use `pytest.fixture()` for shared setup. Integration tests get a `client` fixture from `TestClient`

## Workflow

- Use `uv` for all Python operations, never `pip` or `pip install`
- Run lint + typecheck + tests before committing
- Write tests for new functionality — at minimum, one happy-path test per endpoint or public function
- When compacting, preserve: list of modified files, failing test output, current task progress, architectural decisions made
- Before ending a session on a long task, write progress to `.claude/scratchpad/<branch-name>.md`
- Use subagents for broad codebase exploration to keep main context clean
- Pre-commit hooks run ruff (lint+format) and mypy automatically on commit

## Project structure

```
├── main.py                  # FastAPI entry point
├── src/
│   ├── api/routes.py        # API endpoints (mounted at /api/v1)
│   ├── data/                # Data loading and processing
│   ├── models/              # ML model wrappers
│   ├── features/            # Feature engineering
│   ├── pipelines/           # Orchestration logic
│   ├── evaluation/          # Model evaluation
│   └── utils/
│       ├── config.py        # Layered config (Settings singleton)
│       ├── logger.py        # Structured logging setup
│       └── errors.py        # AppError + ErrorCode enum
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # API/integration tests
│   ├── evaluation/          # Model evaluation tests
│   ├── safety/              # Safety and security tests
│   └── fixtures/            # Shared test data
├── configs/                 # Per-environment YAML configs
├── scripts/                 # Setup, deployment, utility scripts
├── docs/                    # Requirements, ADRs, runbooks
├── data/                    # raw/, interim/, processed/, uploads/
└── models/                  # Saved model artifacts
```

## Available skills

- `/run-checks` — full quality pipeline (lint, format, typecheck, tests)
- `/fix-issue 123` — end-to-end GitHub issue fix with tests and PR
- `/add-endpoint GET /items list items` — scaffold endpoint + models + tests
- `/review-code src/api/` — security and quality review (runs in isolated context)
- `/review-pr` — review current branch changes against main
- `/spec feature-name` — interview-driven feature spec to `docs/specs/`
- `/explain-code src/utils/config.py` — visual explanation with diagrams
- `/sync-requirements` — sync requirement controller JSONs from markdown

## Key references

See @pyproject.toml for dependencies and tool config.
See @docs/app_cheatsheet.md for dev URLs, credentials, and operational commands.
See @docs/requirements/common_requirements.md for project standards.
