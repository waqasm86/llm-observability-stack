#!/usr/bin/env bash
set -euo pipefail

NODE="${NODE:-$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')}"
MODEL_DIR="${MODEL_DIR:-/media/waqasm86/External11/Project-Llamatelemetry/repos-llamatelemetry/llamatelemetry-xubuntu24/models}"
MODEL_FILE="${MODEL_FILE:-gemma-3-1b-it-Q4_K_M.gguf}"

[[ "$(kubectl get nodes --no-headers | wc -l)" -eq 1 ]] || {
  echo "This helper is for a single-node k3s cluster." >&2
  exit 1
}
[[ -r "${MODEL_DIR}/${MODEL_FILE}" ]] || {
  echo "Model is not readable: ${MODEL_DIR}/${MODEL_FILE}" >&2
  exit 1
}

kubectl label node "$NODE" node-role.kubernetes.io/worker=true --overwrite
kubectl label node "$NODE" nvidia.com/gpu.present=true --overwrite
kubectl label node "$NODE" llm-observability.io/model-host=true --overwrite

echo "Prepared $NODE as the combined k3s control-plane and worker node."
kubectl get node "$NODE" -o custom-columns=NAME:.metadata.name,CONTROL_PLANE:.metadata.labels.node-role\\.kubernetes\\.io/control-plane,WORKER:.metadata.labels.node-role\\.kubernetes\\.io/worker,GPU_PRESENT:.metadata.labels.nvidia\\.com/gpu\\.present
