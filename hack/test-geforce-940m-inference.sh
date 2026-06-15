#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-llm-observability}"
MODEL="${MODEL:-gemma3-1b-it-gguf-local}"
PROMPT="${PROMPT:-In one short sentence, explain why GPU observability matters.}"

gpu="$(kubectl get nodes -o jsonpath='{range .items[*]}{.status.allocatable.nvidia\.com/gpu}{end}')"
[[ "${gpu:-0}" -ge 1 ]] || {
  echo "No allocatable nvidia.com/gpu resource." >&2
  exit 1
}

kubectl rollout status deployment/ollama -n "$NAMESPACE" --timeout=5m
kubectl exec -n "$NAMESPACE" deployment/ollama -- ollama show "$MODEL" >/dev/null
kubectl exec -n "$NAMESPACE" deployment/ollama -- ollama run "$MODEL" "$PROMPT"

echo
echo "GPU discovery evidence:"
kubectl logs -n "$NAMESPACE" deployment/ollama |
  grep -E 'inference compute.*library=CUDA.*NVIDIA GeForce 940M' |
  tail -1
