#!/bin/bash
# Start vLLM server for local GPU inference.
#
# Usage:
#   bash scripts/start_vllm.sh                           # default model
#   bash scripts/start_vllm.sh Qwen/Qwen2.5-7B-Instruct  # custom model
#   bash scripts/start_vllm.sh stop                       # stop running server
#
# Environment variables:
#   LLM__VLLM_MODEL          Model to serve (default: Qwen/Qwen2.5-14B-Instruct)
#   VLLM_PORT                Port to bind (default: 8000)
#   VLLM_GPU_MEMORY_UTIL     GPU memory utilization 0-1 (default: 0.90)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +a
fi

MODEL="${1:-${LLM__VLLM_MODEL:-Qwen/Qwen2.5-14B-Instruct}}"
PORT="${VLLM_PORT:-8000}"
GPU_MEM="${VLLM_GPU_MEMORY_UTIL:-0.90}"

# Handle stop command
if [ "$MODEL" = "stop" ]; then
    echo "Stopping vLLM server on port $PORT..."
    PID=$(lsof -ti:"$PORT" 2>/dev/null || true)
    if [ -n "$PID" ]; then
        kill "$PID"
        echo "Stopped process $PID"
    else
        echo "No process found on port $PORT"
    fi
    exit 0
fi

# Kill existing process on port (REQ-RUN-009)
EXISTING_PID=$(lsof -ti:"$PORT" 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
    echo "Killing existing process $EXISTING_PID on port $PORT..."
    kill "$EXISTING_PID"
    sleep 2
fi

echo "Starting vLLM server..."
echo "  Model: $MODEL"
echo "  Port:  $PORT"
echo "  GPU memory utilization: $GPU_MEM"
echo ""

exec uv run python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --port "$PORT" \
    --gpu-memory-utilization "$GPU_MEM" \
    --trust-remote-code
