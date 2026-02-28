# Plan 5: Knowledge Hub Frontend — React + Tailwind + shadcn/ui

## Status: Implementation Complete

## Phase 0: Project Scaffold
- [x] Install Node.js via nvm (v22 LTS)
- [x] Create Vite React-TS project
- [x] Install all dependencies (react-router, react-query, tailwindcss, shadcn, etc.)
- [x] Configure Tailwind v4 with `@tailwindcss/vite` and `@tailwindcss/typography`
- [x] Configure Vite with `@/` path alias and dev proxy (5s timeout)
- [x] Initialize shadcn/ui and install 17 components
- [x] Create `frontend/scripts/start.sh` and `stop.sh`

## Phase 1: App Shell, Layout, Routing, API Client
- [x] Create directory structure (api/, components/, features/, hooks/, lib/)
- [x] API client layer — `client.ts`, `types.ts`, per-feature API modules
- [x] TypeScript interfaces matching `src/api/schemas.py`
- [x] Routing with react-router (/, /chat, /sources, /summarize, /qna, /interview)
- [x] AppLayout with collapsible Sidebar (240px → 64px)
- [x] Theme toggle (dark/light) with localStorage persistence
- [x] Shared components: MarkdownRenderer, LoadingSpinner, EmptyState, SourceSelector

## Phase 2: Chat (Perplexity-Style)
- [x] ChatPage with session list sidebar + message area
- [x] ChatMessage with user/assistant styling, markdown rendering
- [x] CitationCard — expandable source chunks with relevance score
- [x] ChatInput — auto-resizing textarea, Enter to send
- [x] SessionList — past sessions with message count

## Phase 3: Sources / Knowledge Base
- [x] SourcesPage — search, status filter, grid of cards
- [x] SourceCard — file icon, status dot, tags, actions dropdown
- [x] UploadDialog — tabs: File (drag-drop), URL, Text
- [x] SourceDetail — Sheet with editable fields, metadata, actions

## Phase 4: Interview Preparation
- [x] InterviewSetup — topic, mode, difficulty, question count, source selector
- [x] InterviewSession — progress bar, question card, answer textarea
- [x] FeedbackPanel — score badge, feedback text, collapsible model answer
- [x] InterviewSummary — overall score, breakdown by question

## Phase 5: Q&A Generation
- [x] GenerateForm — topic/source selector, count, difficulty
- [x] QASetView — list view + flashcard view tabs, export buttons
- [x] FlashCard — click-to-flip, prev/next navigation

## Phase 6: Summarization
- [x] SummarizePage — source selector OR topic input, short/detailed toggle
- [x] Inline SourceSelector with multi-select and search
- [x] SummaryResult with markdown, copy button, source attribution

## Phase 7: Polish and Production
- [x] Static file serving from FastAPI (`_mount_frontend` in main.py)
- [x] SPA fallback for client-side routing
- [x] Updated `docs/app_cheatsheet.md` with frontend URLs and ports
- [x] Build verified: `tsc -b && vite build` passes cleanly
