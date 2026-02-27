---
paths:
  - "src/models/**/*.py"
---

# Model & ML Rules

## Interface pattern
- Define a `Protocol` class for each model interface (`LLMClient`, `EmbeddingModel`)
- Use `create_*()` factory functions that dispatch on `settings.model_backend`
- Mock implementation must always be available and is the default for development and testing

## Mock implementations
- Mock models must be deterministic — use hash-based generation, not random
- Mock outputs should be realistic enough for integration tests to exercise downstream logic

## Heavy imports
- Import heavy ML libraries (`torch`, `transformers`, `sentence_transformers`) inside `__init__` or method body
- Catch `ImportError` and raise `AppError(code=ErrorCode.MODEL_LOAD_FAILED)` with install instructions in the message

## LLM calls
- Always set explicit `max_tokens` on every `generate()` call — default from `settings.llm.max_tokens` (REQ-ERR-007)
- Log lifecycle events with `model=`, `input_tokens=`, `output_tokens=`, `latency_ms=` fields

## Configuration
- Access config via `settings.embedding.*` and `settings.llm.*` — never hardcode model names or API keys
- Model backend (`mock`, `local`, `cloud`) controlled by `settings.model_backend`
