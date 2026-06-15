#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${1:-$ROOT/artifacts/evidence-$STAMP}"
mkdir -p "$OUT"
git -C "$ROOT" rev-parse HEAD >"$OUT/git-commit.txt"
kubectl version >"$OUT/kubernetes-version.txt"
kubectl get nodes -o wide >"$OUT/nodes.txt"
kubectl get pods -A -o wide >"$OUT/pods.txt"
kubectl get servicemonitors,probes,prometheusrules -A >"$OUT/monitoring-resources.txt" 2>&1 || true
helm list -A >"$OUT/helm-releases.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv >"$OUT/nvidia-gpu.txt" 2>&1 || true
echo "Evidence written to $OUT"
echo "Review every file before sharing; Secrets and ConfigMaps are not collected."
