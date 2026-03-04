# Plan 11: vLLM K8s Multi-Node Pipeline Parallel Serving

> **PIVOTED**: The `mp` (multiprocess) backend hit blocking NCCL/torch.distributed handshake failures. WorkerProc subprocess crashed silently during `init_process_group`. After debugging CUDA compat, DNS deadlock, probe timing, and service env collision, the `mp` backend's multi-node coordination remained broken. **See Plan 12** for the Ray-based replacement (`--distributed-executor-backend ray`, PP=3 across 3 GPUs).

## Context

The Qwen2.5-14B-Instruct model (bfloat16, ~28GB weights) can't fit on the RTX 3090 (24GB). The K8s cluster has 3 GPU nodes but GPUs aren't schedulable yet (no NVIDIA device plugin). We'll deploy vLLM as K8s pods with pipeline-parallel-size=2 across the RTX 3090 (24GB) and one RTX 3060 (12GB) for a total of 36GB VRAM.

## Cluster Inventory

| Node | Role | GPUs | VRAM | IP (Tailscale) |
|------|------|------|------|-----------------|
| vinpanathan-3090-1 | worker | 1x RTX 3090 | 24GB | 100.111.249.61 |
| vinpanathan-precision-tower-7810 | control-plane | 2x RTX 3060 | 24GB | 100.111.31.125 |
| vinpanathan-serval-ws | worker | 1x GTX 1660 Ti | 6GB | 100.110.105.68 |

**Current state**: `nvidia` RuntimeClass exists, containerd nvidia runtime auto-configured on all nodes by k3s. No NVIDIA device plugin deployed (GPUs show as "none" in capacity). No KubeRay operator. Ray 2.54.0 installed as vLLM transitive dep.

## Architecture

- **vLLM v0.16**: Multi-node uses `mp` backend (not Ray). Head pod (node-rank=0) serves API; worker pod (node-rank=1) runs `--headless`
- **Image**: `vllm/vllm-openai:v0.16.0-cu130` (8.6GB, both nodes have CUDA 13.0+)
- **NCCL**: Over flannel VXLAN (Tailscale overlay). Pods bind to `eth0` (CNI interface)
- **Model weights**: Pre-downloaded to `/data/huggingface/hub` on both nodes, mounted as hostPath
- **Context length**: `--max-model-len 8192` to fit within RTX 3060's 12GB

## Files to Create/Modify

```
k8s/nvidia-device-plugin.yaml     # NEW — GPU scheduling DaemonSet
k8s/namespace.yaml                # NEW — vllm namespace
k8s/vllm-configmap.yaml           # NEW — shared env vars
k8s/vllm-head.yaml                # NEW — head Deployment + Services
k8s/vllm-worker.yaml              # NEW — worker Deployment + init container
scripts/start_vllm_k8s.sh         # NEW — deploy/stop/status/logs/forward
scripts/download_model_weights.sh  # NEW — download weights to both nodes
configs/local.yaml                 # MODIFY — update vllm_base_url
docs/app_cheatsheet.md             # MODIFY — add K8s vLLM section
```

## Steps

### Step 1: Deploy NVIDIA Device Plugin
- [x] Create `k8s/nvidia-device-plugin.yaml` with `nvcr.io/nvidia/k8s-device-plugin:v0.17.0` DaemonSet
- [x] `FAIL_ON_INIT_ERROR=false` so pods succeed on nodes where GPU init might differ
- [ ] Apply and verify `nvidia.com/gpu` appears in node capacity (1 on 3090-1, 2 on 7810)

### Step 2: Label Nodes & Download Model Weights
- [ ] Label nodes: `kubectl label node vinpanathan-3090-1 gpu-model=rtx-3090` and 7810 `gpu-model=rtx-3060`
- [x] Create `scripts/download_model_weights.sh` — downloads Qwen2.5-14B-Instruct to `/data/huggingface/hub` on local + remote node via SSH
- [ ] Run on both nodes (28GB download each)

### Step 3: K8s Manifests
- [x] `k8s/namespace.yaml` — create `vllm` namespace
- [x] `k8s/vllm-configmap.yaml` — shared env: model name, NCCL settings (`NCCL_SOCKET_IFNAME=eth0`, `NCCL_IB_DISABLE=1`), `HUGGINGFACE_HUB_CACHE=/model-weights`, `MAX_MODEL_LEN=8192`
- [x] `k8s/vllm-head.yaml`:
  - Deployment: pinned to `vinpanathan-3090-1` via `nodeSelector`, `runtimeClassName: nvidia`, 1 GPU, hostPath model mount + `/dev/shm` emptyDir (4Gi)
  - Headless Service `vllm-head` (DNS for worker's `--master-addr`)
  - NodePort Service `vllm` (port 8001, nodePort 30801) for external access
  - Readiness/liveness probes on `/health`
  - Command: `--pipeline-parallel-size 2 --nnodes 2 --node-rank 0 --master-addr vllm-head.vllm.svc.cluster.local --master-port 29500`
- [x] `k8s/vllm-worker.yaml`:
  - Deployment: pinned to `vinpanathan-precision-tower-7810`, 1 GPU
  - Init container: wait for head DNS + NCCL port 29500
  - Command: `--pipeline-parallel-size 2 --nnodes 2 --node-rank 1 --headless --master-addr vllm-head.vllm.svc.cluster.local`
  - hostPath type `DirectoryOrCreate` to avoid scheduling failures

### Step 4: Config & Script Updates
- [x] Create `scripts/start_vllm_k8s.sh` with subcommands: `deploy`, `stop`, `status`, `logs [head|worker]`, `forward`, `pull-images`
- [x] Update `configs/local.yaml`: `vllm_base_url` to `http://vllm.vllm.svc.cluster.local:8001/v1` (or keep localhost for port-forward mode)
- [x] Update `docs/app_cheatsheet.md` with K8s vLLM commands and URLs

### Step 5: Deploy & Verify
- [ ] Pre-pull images on both nodes (`sudo crictl pull vllm/vllm-openai:v0.16.0-cu130`)
- [ ] Apply manifests, wait for rollout
- [ ] Verify GPU allocation: `kubectl describe pod -n vllm`
- [ ] Verify NCCL logs: head should show `net/Socket ... using if eth0`
- [ ] Health check: `curl http://localhost:30801/health`
- [ ] Inference test: `curl http://localhost:30801/v1/chat/completions`
- [ ] Run embedding/graph pipelines with updated config

## Fallback

Existing `scripts/start_vllm.sh` remains for single-node use (7B model or quantized). Switch by setting `LLM__VLLM_BASE_URL=http://localhost:8001/v1` in `.env`.
