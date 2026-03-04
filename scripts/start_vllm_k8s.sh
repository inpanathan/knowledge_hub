#!/bin/bash
# Manage vLLM single-node AWQ deployment on K8s.
#
# Architecture:
#   Single pod on vinpanathan-3090-1 (1× RTX 3090, 24GB)
#   Model: Qwen2.5-14B-Instruct-AWQ (4-bit, ~8GB VRAM)
#
# Usage:
#   bash scripts/start_vllm_k8s.sh deploy         # apply all manifests
#   bash scripts/start_vllm_k8s.sh stop            # delete vllm pods
#   bash scripts/start_vllm_k8s.sh status          # show pod/node/gpu status
#   bash scripts/start_vllm_k8s.sh logs            # tail pod logs
#   bash scripts/start_vllm_k8s.sh forward         # port-forward 8001 -> vllm pod
#   bash scripts/start_vllm_k8s.sh pull-images     # pre-pull vLLM image on GPU node
#   bash scripts/start_vllm_k8s.sh test            # health check + inference test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$PROJECT_ROOT/k8s"
NAMESPACE="vllm"
VLLM_IMAGE="vllm/vllm-openai:v0.16.0"
NODEPORT=30801

# GPU node for image pre-pull
GPU_NODES=("vinpanathan-3090-1")

usage() {
    echo "Usage: $(basename "$0") {deploy|stop|status|logs|forward|pull-images|test}"
    echo ""
    echo "Commands:"
    echo "  deploy       Apply NVIDIA device plugin + vLLM manifests"
    echo "  stop         Delete vLLM deployment (keeps device plugin)"
    echo "  status       Show pods, GPU allocation, and services"
    echo "  logs         Tail vLLM pod logs"
    echo "  forward      Port-forward localhost:8001 to vLLM pod"
    echo "  pull-images  Pre-pull vLLM container image on GPU node"
    echo "  test         Run health check and inference test"
    exit 1
}

cmd_deploy() {
    echo "=== Deploying vLLM (single-node AWQ) ==="

    # NVIDIA device plugin (idempotent)
    echo "[1/4] NVIDIA device plugin..."
    kubectl apply -f "$K8S_DIR/nvidia-device-plugin.yaml"

    # Wait for device plugin to be ready
    echo "  Waiting for device plugin pods..."
    kubectl rollout status daemonset/nvidia-device-plugin-daemonset \
        -n kube-system --timeout=120s

    # Namespace
    echo "[2/4] Namespace..."
    kubectl apply -f "$K8S_DIR/namespace.yaml"

    # ConfigMap
    echo "[3/4] ConfigMap..."
    kubectl apply -f "$K8S_DIR/vllm-configmap.yaml"

    # vLLM pod
    echo "[4/4] vLLM deployment..."
    kubectl apply -f "$K8S_DIR/vllm-head.yaml"

    echo ""
    echo "Waiting for pod to be ready (this may take 2-5 minutes)..."
    kubectl rollout status deployment/vllm-head -n "$NAMESPACE" --timeout=600s || true

    echo ""
    cmd_status
    echo ""
    echo "vLLM API available at:"
    echo "  NodePort:     http://<any-node-ip>:$NODEPORT"
    echo "  Port-forward: bash scripts/start_vllm_k8s.sh forward"
}

cmd_stop() {
    echo "=== Stopping vLLM ==="
    kubectl delete -f "$K8S_DIR/vllm-head.yaml" --ignore-not-found
    kubectl delete -f "$K8S_DIR/vllm-configmap.yaml" --ignore-not-found
    echo "Stopped. Namespace and device plugin kept."
    echo "To remove everything: kubectl delete namespace $NAMESPACE"
}

cmd_status() {
    echo "=== vLLM K8s Status ==="
    echo ""
    echo "--- Pods ---"
    kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null || echo "No pods in namespace $NAMESPACE"
    echo ""
    echo "--- Services ---"
    kubectl get svc -n "$NAMESPACE" 2>/dev/null || echo "No services"
    echo ""
    echo "--- GPU Allocation ---"
    kubectl get nodes -o custom-columns=\
'NAME:.metadata.name,GPU_CAPACITY:.status.capacity.nvidia\.com/gpu,GPU_ALLOC:.status.allocatable.nvidia\.com/gpu' \
        2>/dev/null || echo "Cannot query GPU status"
    echo ""
    echo "--- Device Plugin ---"
    kubectl get pods -n kube-system -l app.kubernetes.io/name=nvidia-device-plugin \
        -o wide 2>/dev/null || echo "Device plugin not deployed"
}

cmd_logs() {
    local pod
    pod=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=head \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -z "$pod" ]; then
        echo "No vLLM pod found"
        exit 1
    fi
    echo "=== Logs: $pod ==="
    kubectl logs -n "$NAMESPACE" "$pod" -f --tail=100
}

cmd_forward() {
    echo "Port-forwarding localhost:8001 -> vllm pod:8001"
    echo "Press Ctrl+C to stop"
    kubectl port-forward -n "$NAMESPACE" svc/vllm-api 8001:8001
}

cmd_pull_images() {
    echo "=== Pre-pulling vLLM image on GPU node ==="
    for node in "${GPU_NODES[@]}"; do
        echo "[$node] Pulling $VLLM_IMAGE ..."
        ssh -o ConnectTimeout=10 "$node" "sudo crictl pull $VLLM_IMAGE" &
    done
    wait
    echo "All pulls complete."
}

cmd_test() {
    echo "=== vLLM Health Check ==="
    local url="http://localhost:$NODEPORT"

    echo "Testing $url/health ..."
    if curl -sf "$url/health" >/dev/null 2>&1; then
        echo "  Health: OK"
    else
        echo "  Health: FAILED (is the service running? try: bash scripts/start_vllm_k8s.sh status)"
        exit 1
    fi

    echo ""
    echo "Testing inference..."
    local response
    response=$(curl -sf "$url/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
            "messages": [{"role": "user", "content": "Say hello in one word."}],
            "max_tokens": 16
        }' 2>&1)

    if [ $? -eq 0 ]; then
        echo "  Inference: OK"
        echo "  Response: $(echo "$response" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(r['choices'][0]['message']['content'])
" 2>/dev/null || echo "$response")"
    else
        echo "  Inference: FAILED"
        echo "  $response"
        exit 1
    fi
}

# --- Main ---
COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    deploy)      cmd_deploy ;;
    stop)        cmd_stop ;;
    status)      cmd_status ;;
    logs)        cmd_logs "$@" ;;
    forward)     cmd_forward ;;
    pull-images) cmd_pull_images ;;
    test)        cmd_test ;;
    *)           usage ;;
esac
