#!/bin/bash
# Download model weights to local and remote nodes for K8s vLLM serving.
#
# Usage:
#   bash scripts/download_model_weights.sh                    # download to all nodes
#   bash scripts/download_model_weights.sh --local-only       # download to this node only
#   bash scripts/download_model_weights.sh --dry-run          # show what would be done
#
# Environment variables:
#   VLLM_MODEL        Model to download (default: Qwen/Qwen2.5-14B-Instruct)
#   HF_TOKEN          HuggingFace token for authenticated downloads (read from .env)
#   HF_CACHE_DIR      Cache directory (default: /data/huggingface/hub)
#   REMOTE_NODES      Space-separated SSH targets (default: vinpanathan-3090-1 vinpanathan-serval-ws)

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

MODEL="${VLLM_MODEL:-Qwen/Qwen2.5-14B-Instruct}"
HF_CACHE="${HF_CACHE_DIR:-/data/huggingface/hub}"
REMOTE_NODES="${REMOTE_NODES:-vinpanathan-3090-1 vinpanathan-serval-ws}"
LOCAL_ONLY=false
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --local-only) LOCAL_ONLY=true ;;
        --dry-run)    DRY_RUN=true ;;
        *)            MODEL="$arg" ;;
    esac
done

echo "=== Model Weight Downloader ==="
echo "  Model:     $MODEL"
echo "  Cache dir: $HF_CACHE"
echo "  HF_TOKEN:  ${HF_TOKEN:+set}${HF_TOKEN:-not set (unauthenticated, slower)}"
echo "  Nodes:     $(hostname)${LOCAL_ONLY:+ (local only)}${LOCAL_ONLY:-  + $REMOTE_NODES}"
echo ""

download_local() {
    echo "[$(hostname)] Downloading $MODEL to $HF_CACHE ..."
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] Would run: huggingface-cli download $MODEL --cache-dir $HF_CACHE"
        return
    fi

    sudo mkdir -p "$HF_CACHE"
    sudo chown "$(id -u):$(id -g)" "$HF_CACHE"

    # HF_TOKEN is exported from .env — huggingface-cli and huggingface_hub
    # both read it automatically from the environment.
    if command -v huggingface-cli &>/dev/null; then
        huggingface-cli download "$MODEL" --cache-dir "$HF_CACHE"
    elif command -v uv &>/dev/null; then
        uv run python -c "
from huggingface_hub import snapshot_download
snapshot_download('$MODEL', cache_dir='$HF_CACHE')
"
    else
        echo "ERROR: Neither huggingface-cli nor uv found. Install huggingface_hub."
        exit 1
    fi

    echo "[$(hostname)] Download complete."
}

download_remote() {
    local node="$1"
    echo "[$node] Downloading $MODEL to $HF_CACHE ..."
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] Would SSH to $node and download"
        return
    fi

    # Forward HF_TOKEN for authenticated downloads on remote nodes.
    # shellcheck disable=SC2087
    ssh -o ConnectTimeout=10 "$node" bash <<REMOTE_EOF
set -euo pipefail
export HF_TOKEN="${HF_TOKEN:-}"
sudo mkdir -p "$HF_CACHE"
sudo chown "\$(id -u):\$(id -g)" "$HF_CACHE"

if command -v huggingface-cli &>/dev/null; then
    huggingface-cli download "$MODEL" --cache-dir "$HF_CACHE"
else
    # Use a temp venv for externally-managed Python environments (PEP 668)
    VENV="/tmp/hf_download_venv"
    python3 -m venv "\$VENV"
    "\$VENV/bin/pip" install -q huggingface_hub
    "\$VENV/bin/python3" -c "
from huggingface_hub import snapshot_download
snapshot_download('$MODEL', cache_dir='$HF_CACHE')
"
fi
echo "[$node] Download complete."
REMOTE_EOF
}

# Download locally
download_local

# Download to remote nodes
if [ "$LOCAL_ONLY" = false ]; then
    for node in $REMOTE_NODES; do
        download_remote "$node"
    done
fi

echo ""
echo "All downloads complete. Verify with:"
echo "  ls -la $HF_CACHE/models--${MODEL//\//__}/"
