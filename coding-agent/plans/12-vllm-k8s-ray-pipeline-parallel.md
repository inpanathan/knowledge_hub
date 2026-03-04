# Plan 12: vLLM K8s Deployment (Ray PP → Single-Node AWQ)

## Context

Pivot from Plan 11's `mp` backend to Ray backend failed — same NCCL `ncclCommInitRank` crash over flannel VXLAN. Further attempt with `hostNetwork: true` over Tailscale also failed. Multi-node NCCL is fundamentally broken on this cluster — incompatible with both flannel VXLAN overlay and WireGuard (Tailscale) tunnels.

**Final approach**: AWQ 4-bit quantized model on single RTX 3090. Qwen2.5-14B-Instruct-AWQ (~8GB) fits comfortably on 24GB GPU with ~14GB free for KV cache.

## Attempts

1. **mp backend PP=2** (Plan 11) — NCCL handshake crash during `init_process_group`
2. **Ray backend PP=3 over flannel** — same NCCL crash at `ncclCommInitRank` (Ray doesn't change transport)
3. **Ray + NCCL tuning** (`P2P_DISABLE`, `SHM_DISABLE`, `NET_GDR_LEVEL=0`) — same crash
4. **Ray PP=3 + hostNetwork over Tailscale** — fixed Gloo (`GLOO_SOCKET_IFNAME=tailscale0`), fixed Ray IP binding (`--node-ip-address`, `VLLM_HOST_IP`), but NCCL still crashed at `ncclCommInitRank` over WireGuard tunnel
5. **Single-node AWQ** — works

### hostNetwork Attempt Details

With `hostNetwork: true`, pods bind directly to host network stack (bypassing flannel):
- **Fixed**: Ray IP binding via `--node-ip-address` + `VLLM_HOST_IP` (was binding to WiFi IP instead of Tailscale)
- **Fixed**: Gloo connectivity via `GLOO_SOCKET_IFNAME=tailscale0` (was resolving to `127.0.1.1` loopback)
- **Not fixable**: NCCL `ncclCommInitRank` still crashes — NCCL socket transport incompatible with WireGuard tunnel MTU/protocol

### Cluster Network Topology

| Node | Tailscale IP | WiFi IP | WiFi Subnet |
|------|-------------|---------|-------------|
| vinpanathan-3090-1 | 100.111.249.61 | 192.168.4.20 | 192.168.4.0/22 |
| vinpanathan-precision-tower-7810 | 100.111.31.125 | 10.0.0.122 | 10.0.0.0/24 |

WiFi IPs on different subnets — nodes only reachable via Tailscale WireGuard mesh.

## Steps

### Step 1: Update ConfigMap
- [x] Simplified to AWQ model, removed Ray/NCCL/Gloo vars

### Step 2: Single-Pod Manifest
- [x] `k8s/vllm-head.yaml` — single pod on 3090-1, `--quantization awq`

### Step 3: Delete Multi-Node Manifests
- [x] Removed Ray head, worker-3090, worker-7810 manifests

### Step 4: Update Scripts
- [x] `scripts/start_vllm_k8s.sh` — simplified for single pod
- [x] `scripts/download_model_weights.sh` — HF_TOKEN support

### Step 5: Update Config & Docs
- [x] `configs/local.yaml` — updated model name
- [x] `docs/app_cheatsheet.md` — single-node AWQ architecture

### Step 6: Deploy & Verify
- [x] Downloaded AWQ weights to 3090-1
- [x] Deployed single pod — 1/1 Ready, 0 restarts
- [x] Health check: OK
- [x] Inference test: OK ("Hello")
