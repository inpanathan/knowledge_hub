#!/bin/bash
# Start/stop Qdrant vector database in Docker.
#
# Usage:
#   bash scripts/start_qdrant.sh          # start (idempotent)
#   bash scripts/start_qdrant.sh stop     # stop and remove container
#   bash scripts/start_qdrant.sh status   # show container status
#
# Persistent storage: data/qdrant_storage/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CONTAINER_NAME="knowledge-hub-qdrant"
QDRANT_PORT="${QDRANT_PORT:-6333}"
STORAGE_DIR="$PROJECT_ROOT/data/qdrant_storage"

case "${1:-start}" in
    stop)
        echo "Stopping Qdrant..."
        docker stop "$CONTAINER_NAME" 2>/dev/null && docker rm "$CONTAINER_NAME" 2>/dev/null \
            && echo "Stopped and removed $CONTAINER_NAME" \
            || echo "Container $CONTAINER_NAME not running"
        exit 0
        ;;
    status)
        docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        exit 0
        ;;
    start)
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac

# Stop existing container if running (REQ-RUN-005)
if docker ps -q --filter "name=$CONTAINER_NAME" 2>/dev/null | grep -q .; then
    echo "Stopping existing Qdrant container..."
    docker stop "$CONTAINER_NAME" >/dev/null
    docker rm "$CONTAINER_NAME" >/dev/null
fi

# Also clean up stopped container with the same name
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# Create storage directory
mkdir -p "$STORAGE_DIR"

echo "Starting Qdrant..."
echo "  Port:    $QDRANT_PORT"
echo "  Storage: $STORAGE_DIR"
echo ""

docker run -d \
    --name "$CONTAINER_NAME" \
    -p "${QDRANT_PORT}:6333" \
    -v "$STORAGE_DIR:/qdrant/storage:z" \
    qdrant/qdrant:latest

echo ""
echo "Qdrant is running at http://localhost:${QDRANT_PORT}"
echo "Dashboard: http://localhost:${QDRANT_PORT}/dashboard"
