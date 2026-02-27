# Plan: Add Missing .claude/ Artifacts and Reorganize

## Context

The project has a solid `.claude/` foundation (4 rules, 3 agents, 8 skills, 2 hooks) but is missing rules for several key domains (security, error handling, logging, data pipeline, ML models, documentation), role-based agents for PM and QA workflows, workflow rules for maintaining living docs (cheatsheet, runbooks, troubleshooting), and a troubleshooting guide required by REQ-AGT-004.

**No existing files need reorganization.** The current rules are clean, focused, and correctly path-scoped. New artifacts fill gaps without overlapping existing ones.

---

## Status

- [x] Phase 1: New Rules (6 files)
- [x] Phase 2: New Agents (3 files)
- [x] Phase 3: CLAUDE.md Workflow Additions
- [x] Phase 4: Documentation Artifacts
- [x] Phase 5: Verification

---

## Changes Summary

| # | File | Action | Status |
|---|------|--------|--------|
| 1 | `.claude/rules/security.md` | Create | [x] |
| 2 | `.claude/rules/error-handling.md` | Create | [x] |
| 3 | `.claude/rules/logging.md` | Create | [x] |
| 4 | `.claude/rules/documentation.md` | Create | [x] |
| 5 | `.claude/rules/data-pipeline.md` | Create | [x] |
| 6 | `.claude/rules/models-ml.md` | Create | [x] |
| 7 | `.claude/agents/product-manager.md` | Create | [x] |
| 8 | `.claude/agents/qa-tester.md` | Create | [x] |
| 9 | `.claude/agents/code-reviewer.md` | Create | [x] |
| 10 | `CLAUDE.md` | Modify — add 3 workflow bullets | [x] |
| 11 | `docs/troubleshooting.md` | Create | [x] |
| 12 | `.claude/CLAUDE.local.md.template` | Create | [x] |

**10 new files, 1 modification, 0 deletions.**

---

## Phase 1: New Rules (6 files)

### 1. `.claude/rules/security.md`
**Paths:** `src/**/*.py`

- Validate all external inputs (API params, file paths, URLs) before use
- Prevent path traversal — use `Path.resolve()` and check against allowed directories
- Never log API keys, tokens, or credentials; use `settings.llm.api_key` from config
- Sanitize user inputs before including in LLM prompts; separate system from user content
- Validate file uploads server-side by content, not just extension; enforce `max_file_size_mb`
- No `eval()`, `exec()`, `os.system()`, or `subprocess(shell=True)`
- Reference: REQ-SEC-001 through REQ-SEC-003

### 2. `.claude/rules/error-handling.md`
**Paths:** `src/**/*.py`

- Always raise `AppError(code=ErrorCode.X, message="...", context={...})`
- Chain exceptions with `cause=` parameter: `raise AppError(..., cause=e) from e`
- Catch narrowest exception type; no bare `except:` or broad `except Exception` (REQ-ERR-006)
- Set explicit timeouts on all external calls (REQ-ERR-003)
- Set explicit `max_tokens` on every LLM `generate()` call (REQ-ERR-007)
- Include relevant context in `AppError.context` dict for debugging
- Reference: `ErrorCode` enum from `src/utils/errors.py`, chaining pattern in `src/models/llm.py`

### 3. `.claude/rules/logging.md`
**Paths:** `src/**/*.py`

- Use `from src.utils.logger import get_logger` + `logger = get_logger(__name__)`
- Event names: `snake_case` verbs — `"pdf_parsed"`, `"llm_response_generated"`
- Structured fields as kwargs: `logger.info("source_created", source_id=sid)` not f-strings
- Required fields by category (data ops: `source_id=`, `chunk_count=`; model ops: `model=`, `input_tokens=`, `output_tokens=`, `latency_ms=`)
- Never log sensitive content at INFO; use DEBUG for detailed content in non-production only
- Reference: REQ-LOG-001 through REQ-LOG-012

### 4. `.claude/rules/documentation.md`
**Paths:** `docs/**/*.md`

- Public modules/classes/functions need Google-style docstrings (REQ-DOC-001)
- Runbooks in `docs/runbook/` with format: symptoms, root causes, mitigation, long-term fix
- New scripts/commands → update `docs/app_cheatsheet.md`
- New endpoints → update API Endpoints table in `docs/app_cheatsheet.md`
- README.md is the anchor doc linking to everything (REQ-AGT-001)

### 5. `.claude/rules/data-pipeline.md`
**Paths:** `src/data/**/*.py`

- Parser pattern: takes `Path`, returns `str`, wraps exceptions in `AppError(code=ErrorCode.PARSE_FAILED)`
- New format: add parser function, update `SUPPORTED_FORMATS`, add to `parse_file()` dispatcher
- Chunking via `chunk_text()` with `settings.chunking` params — never hardcode
- Ingestion order: parse → chunk → embed → vector store → file store → catalog entry
- Duplicate detection via `compute_file_hash()` / `compute_content_hash()` before proceeding
- URL fetching: always pass `timeout=`, catch `httpx.TimeoutException` and `httpx.HTTPStatusError` separately

### 6. `.claude/rules/models-ml.md`
**Paths:** `src/models/**/*.py`

- `Protocol` class for each model interface (`LLMClient`, `EmbeddingModel`)
- `create_*()` factory dispatches on `settings.model_backend` (mock always available)
- Mock implementations must be deterministic (hash-based, not random)
- Import heavy ML libraries inside `__init__`/method body, catch `ImportError` → `MODEL_LOAD_FAILED`
- Always set explicit `max_tokens`; default from `settings.llm.max_tokens`
- Log lifecycle events with `model=`, `input_tokens=`, `output_tokens=` fields
- Config via `settings.embedding.*`, `settings.llm.*` — never hardcode model names/keys

---

## Phase 2: New Agents (3 files)

### 7. `.claude/agents/product-manager.md`
**Tools:** Read, Grep, Glob | **Model:** sonnet

Senior PM who:
- Reads `docs/requirements/` (project + common + documentation) and controller JSONs
- Clarifies ambiguous requirements with specific questions
- Writes testable acceptance criteria (Given/When/Then)
- References specific REQ-* identifiers
- Output: Requirements Covered, Acceptance Criteria, Open Questions, Out of Scope

### 8. `.claude/agents/qa-tester.md`
**Tools:** Read, Grep, Glob | **Model:** sonnet

QA engineer who:
- Reviews `tests/` for coverage gaps against requirements
- Identifies missing edge cases from project requirements
- Checks error paths are tested (not just happy paths)
- Verifies test naming, isolation, and conventions
- Does NOT write tests (that's `test-writer`'s job) — produces coverage report
- Output: Coverage table (req → test), Missing Tests list, Test Quality Issues

### 9. `.claude/agents/code-reviewer.md`
**Tools:** Read, Grep, Glob | **Model:** sonnet

Senior developer reviewing for:
- Correctness: logic errors, async/await, edge cases
- Conventions: `__future__` annotations, structlog, AppError, Pydantic, TYPE_CHECKING
- Architecture: module boundaries, no circular imports, factory pattern
- Maintainability: naming, function length, docstrings, no dead code
- Differs from `security-reviewer` (which only checks vulnerabilities)
- Output: Findings table (File:line, Severity, Issue, Suggestion)

---

## Phase 3: CLAUDE.md Workflow Additions

### 10. Modify `CLAUDE.md` — Workflow section

Add 3 new bullets to the existing "Workflow" section:

- **Lessons learned**: After resolving a non-trivial debugging session, document problem, root cause, and solution in `docs/troubleshooting.md` with the commands used (REQ-AGT-004)
- **Cheatsheet maintenance**: When creating new scripts, commands, API endpoints, or config variables, update `docs/app_cheatsheet.md` before the task is complete
- **Runbook maintenance**: When adding alert types, operational procedures, or failure modes, create/update the corresponding runbook in `docs/runbook/`

---

## Phase 4: Documentation Artifacts

### 11. `docs/troubleshooting.md`
Skeleton with sections: General, Ingestion Pipeline, RAG/Chat, Models, Configuration. Each section has placeholder format: Symptom, Root cause, Diagnostic commands, Resolution. Living document updated per the workflow rule.

### 12. `.claude/CLAUDE.local.md.template`
Template file for personal overrides (not the actual `CLAUDE.local.md`). Shows developers what they can customize: model preferences, workflow preferences, environment notes. Includes comment explaining to copy to `CLAUDE.local.md`.

---

## Agent Responsibility Matrix (no overlaps)

| Agent | Role | Produces | Does NOT |
|---|---|---|---|
| security-reviewer | Find vulnerabilities | Security findings | Write code, check style |
| code-reviewer | Check quality & conventions | Quality findings | Find CVEs, write code |
| test-writer | Write tests | Test code | Review existing tests |
| qa-tester | Evaluate test coverage | Coverage report | Write tests |
| architecture-explorer | Map architecture | Architecture summary | Make changes |
| product-manager | Clarify requirements | Acceptance criteria | Write code/tests |

---

## Verification

After implementation:
1. Count files: `ls .claude/rules/*.md` should show 10 rules
2. Count agents: `ls .claude/agents/*.md` should show 6 agents
3. Verify CLAUDE.md has the 3 new workflow bullets
4. Verify `docs/troubleshooting.md` exists
5. Verify `.claude/CLAUDE.local.md.template` exists
