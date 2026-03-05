# Plan 14: Process All Books — Embedding + Knowledge Graph (CUDA)

## Context

65 books remain pending for embedding, plus 1 stuck in "processing". After embedding, each book needs its knowledge graph built (entity extraction via vLLM → Neo4j). The user wants books processed one by one (embed → graph → next book) using CUDA on the 7810's RTX 3060 GPUs for the embedding step.

## Outcome

Embedding completed. Graph deferred to a separate branch (option 14: pre-built knowledge graph).

## Steps

### Step 1: Start infrastructure on 3090-1
- [x] Start Qdrant on port 6333
- [x] Start Neo4j on port 7687 (database: `neo4j`, NOT `knowledgehub` — Community Edition)
- [x] vLLM already running via K8s on NodePort 30801 (Qwen2.5-14B-Instruct-AWQ)
- [x] All three services verified accessible from 7810

### Step 2: Prepare 7810
- [x] Install graph extra: `uv sync --extra dev --extra ml --extra graph` (neo4j 6.1.0 + pytz)
- [x] Fix stuck book: reset `processing` → `pending` (1 row)
- [x] Sync catalog.db to 7810

### Step 3: Create wrapper script + optimizations
- [x] Created `scripts/process_books_full.py` — embed + graph per book, `--skip-graph` flag
- [x] **Option 1**: Concurrent LLM requests — `extract_from_book()` now uses `ThreadPoolExecutor(max_workers=8)` for parallel vLLM calls
- [x] **Option 6**: Tuned vLLM — added `--max-num-seqs 16 --enable-chunked-prefill` to K8s manifest, redeployed

### Step 4: Run embed-only on 7810
- [x] Ran with `--skip-graph` flag, CUDA on RTX 3060, 180s LLM timeout
- [x] **Result: 56 completed, 10 failed, 23.3 minutes total**

### Step 5: Post-processing
- [x] Catalog synced back to local

## Failed Books (10)

| Title | Error |
|-------|-------|
| Generative Deep Learning | Failed to compute embeddings |
| Practical Lakehouse Architecture | Failed to extract text |
| Financial Data Engineering | Failed to compute embeddings |
| Data Science: The Hard Parts | Failed to compute embeddings |
| Natural Language Processing with Transformers | Failed to compute embeddings |
| Hands-On ML with Scikit-Learn/TensorFlow | Failed to compute embeddings |
| Learning Data Science | Failed to compute embeddings |
| Practical Statistics for Data Scientists | Failed to compute embeddings |
| How Large Language Models Work | Failed to extract text |
| Calculus and Analytical Geometry | No chunks produced |

Root causes likely: scanned/image PDFs (no extractable text), corrupt/protected PDFs, or math-heavy content (equations/images only).

## Next Steps

- [ ] Investigate failed books (likely need OCR or alternative extraction)
- [ ] Knowledge graph: implement option 14 (pre-built graph from Wikidata/ConceptNet) in separate branch
- [ ] Compare LLM-based graph extraction vs pre-built graph approach

## Files Changed

- `scripts/process_books_full.py` — new (embed + graph wrapper)
- `src/models/graph_extractor.py` — concurrent `extract_from_book()` with ThreadPoolExecutor
- `k8s/vllm-head.yaml` — added `--max-num-seqs 16 --enable-chunked-prefill`

## Key Learnings

- Neo4j Community Edition only supports the default `neo4j` database, not custom names
- vLLM K8s NodePort is 30801, not 8001 directly
- CUDA embedding is extremely fast: ~15-40s per book vs ~3min+ per chunk for LLM graph extraction
- LLM entity extraction at ~60s/chunk × 13K total chunks = ~9 days — impractical for the full corpus
