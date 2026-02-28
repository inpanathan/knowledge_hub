#!/usr/bin/env bash
# Frontend start script — dev server or production build
# Usage:
#   bash frontend/scripts/start.sh         # dev server on port 3000
#   bash frontend/scripts/start.sh build    # production build to dist/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Ensure nvm is loaded
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

cd "$PROJECT_DIR"

MODE="${1:-dev}"

case "$MODE" in
  build)
    echo "Building frontend for production..."
    npm run build
    echo "Build complete: $PROJECT_DIR/dist/"
    ;;
  dev|*)
    # Kill any existing process on port 3000 (REQ-RUN-009)
    EXISTING_PID=$(lsof -ti:3000 2>/dev/null || true)
    if [ -n "$EXISTING_PID" ]; then
      echo "Killing existing process on port 3000 (PID: $EXISTING_PID)"
      kill "$EXISTING_PID" 2>/dev/null || true
      sleep 1
    fi
    echo "Starting frontend dev server on http://localhost:3000"
    echo "Proxying /api -> http://localhost:8000 (5s timeout)"
    npm run dev
    ;;
esac
