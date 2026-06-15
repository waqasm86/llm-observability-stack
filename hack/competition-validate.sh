#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT_OVERRIDE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
STRICT_GPU=false
if [[ "${1:-}" == "--strict-gpu" ]]; then
  STRICT_GPU=true
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

for command in helm kubectl "$PYTHON_BIN"; do
  command -v "$command" >/dev/null || { echo "missing required command: $command" >&2; exit 1; }
done

cd "$ROOT"
helm lint .
helm template llm-observability-stack . >/dev/null
helm template llm-observability-stack . \
  -f values.competition-nvidia.example.yaml \
  --set langsmith.existingSecret="" \
  --set openWebUI.existingSecret="" \
  --set open-webui.webuiSecret.existingSecretName="" >/dev/null
"$PYTHON_BIN" -m pytest -q tests
kubectl get nodes
kubectl get storageclass

gpu_capacity="$(kubectl get nodes -o jsonpath='{range .items[*]}{.status.capacity.nvidia\.com/gpu}{"\n"}{end}' | tr -d '[:space:]')"
if [[ -z "$gpu_capacity" ]]; then
  echo "WARNING: Kubernetes does not currently advertise nvidia.com/gpu."
  if [[ "$STRICT_GPU" == true ]]; then exit 1; fi
else
  echo "NVIDIA GPU capacity detected: $gpu_capacity"
fi

if ! kubectl get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
  echo "INFO: Prometheus Operator CRDs are not installed; install monitoring first."
fi
echo "Competition validation completed."
