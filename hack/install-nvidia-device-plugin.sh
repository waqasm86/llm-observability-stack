#!/usr/bin/env bash
set -euo pipefail

VERSION="${NVIDIA_DEVICE_PLUGIN_VERSION:-0.18.1}"

helm repo add nvdp https://nvidia.github.io/k8s-device-plugin --force-update
helm repo update nvdp
helm upgrade --install nvidia-device-plugin nvdp/nvidia-device-plugin \
  --version "$VERSION" \
  --namespace nvidia-device-plugin \
  --create-namespace \
  --set runtimeClassName=nvidia \
  --set failOnInitError=true \
  --set deviceDiscoveryStrategy=nvml \
  --set-string nodeSelector.nvidia\\.com/gpu\\.present=true \
  --wait \
  --timeout 5m

kubectl rollout status daemonset/nvidia-device-plugin -n nvidia-device-plugin --timeout=3m
kubectl get pods -n nvidia-device-plugin -o wide
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU_CAPACITY:.status.capacity.nvidia\\.com/gpu,GPU_ALLOCATABLE:.status.allocatable.nvidia\\.com/gpu
