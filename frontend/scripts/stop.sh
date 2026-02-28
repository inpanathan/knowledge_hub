#!/usr/bin/env bash
# Stop the frontend dev server on port 3000
set -euo pipefail

EXISTING_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
  echo "Stopping frontend dev server (PID: $EXISTING_PID)"
  kill "$EXISTING_PID" 2>/dev/null || true
  echo "Stopped."
else
  echo "No process found on port 3000."
fi
