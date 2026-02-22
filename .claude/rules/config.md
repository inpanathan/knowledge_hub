---
paths:
  - "src/utils/config.py"
  - "configs/**"
  - ".env*"
---

# Configuration Rules

## Layered config precedence (highest wins)
1. Environment variables (from `.env` or system)
2. YAML file (`configs/{APP_ENV}.yaml`)
3. Hardcoded defaults in `Settings` class

## Adding new config values
- Add the field to `Settings` or a nested `*Settings` class in `src/utils/config.py`
- Provide a sensible default for development
- Add validation if the value has constraints (use `@field_validator`)
- Add the variable to `.env.example` with a comment
- Add it to `configs/dev.yaml` if it differs from the class default
- Access everywhere via `from src.utils.config import settings`

## Nested settings
- Group related settings into a nested class (e.g., `LoggingSettings`, `ServerSettings`)
- Access with dot notation: `settings.logging.level`
- Set via env vars with `__` delimiter: `LOGGING__LEVEL=DEBUG`

## Security
- Never commit `.env` — only `.env.example`
- Production must set `SECRET_KEY` and `APP_DEBUG=false` (validated at startup)
- Don't log secret values — structlog fields are visible in JSON output
- `model_backend` must be one of: `mock`, `local`, `cloud`
