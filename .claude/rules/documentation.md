---
paths:
  - "docs/**/*.md"
  - "src/**/*.py"
---

# Documentation Rules

## Code documentation
- Public modules, classes, and functions in `src/` need Google-style docstrings (REQ-DOC-001)
- Docstrings describe what the function does and its parameters — not implementation details
- Don't add docstrings to private helpers, test functions, or trivially obvious methods

## Runbooks
- Runbooks live in `docs/runbook/` with consistent format: Symptoms, Root Causes, Diagnostic Commands, Mitigation, Long-Term Fix
- New alert types or failure modes need a corresponding runbook entry

## Living documents to update
- **`docs/app_cheatsheet.md`**: Update when adding scripts, commands, API endpoints, or config variables
- **`docs/troubleshooting.md`**: Update after resolving non-trivial debugging sessions (REQ-AGT-004)
- **`README.md`**: Anchor document linking to all other docs (REQ-AGT-001)

## API documentation
- FastAPI auto-generates OpenAPI/Swagger docs — ensure all endpoints have proper response models and descriptions
- New endpoints need entries in the API Endpoints table in `docs/app_cheatsheet.md`
